from dataclasses import dataclass
from datetime import datetime, time, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction

from progress.models import Action, ActionSchedule, Formateur, ModuleProgress
from training.models import Formation


@dataclass
class ActionWorkflowResult:
    action: Action
    created_progressions: int
    removed_progressions: int
    assigned_formateurs: int


class ActionWorkflowService:
    @staticmethod
    def build_formations_payload(formations):
        payload = []
        for formation in formations:
            modules_data = []
            formation_formateurs = set()

            for module in formation.modules.all():
                eligible_formateurs = list(module.formateurs.filter(active=True).order_by("nom", "postnom"))
                formation_formateurs.update(eligible_formateurs)
                modules_data.append(
                    {
                        "id": module.id,
                        "titre": module.titre,
                        "duree_heures": module.duree_heures,
                        "eligible_formateurs_ids": [formateur.id for formateur in eligible_formateurs],
                        "assigned_formateurs_ids": [formateur.id for formateur in eligible_formateurs],
                    }
                )

            payload.append(
                {
                    "id": formation.id,
                    "nom": formation.nom,
                    "modules": modules_data,
                    "formateurs_ids": [formateur.id for formateur in formation_formateurs],
                }
            )

        return payload

    @staticmethod
    def extract_module_assignments(formation, post_data):
        assignments = {}
        for module in formation.modules.all():
            selected_ids = [
                int(formateur_id)
                for formateur_id in post_data.getlist(f"module_formateurs_{module.id}")
                if str(formateur_id).isdigit()
            ]
            assignments[module.id] = selected_ids
        return assignments

    @staticmethod
    def validate_module_assignments(formation, assignments):
        errors = []
        allowed_module_ids = set(formation.modules.values_list("id", flat=True))

        for module_id, selected_formateur_ids in assignments.items():
            if module_id not in allowed_module_ids:
                errors.append("Un module sélectionné n'appartient pas à la formation choisie.")
                continue

            module = formation.modules.get(pk=module_id)
            allowed_formateur_ids = set(module.formateurs.filter(active=True).values_list("id", flat=True))
            invalid_ids = sorted(set(selected_formateur_ids) - allowed_formateur_ids)
            if invalid_ids:
                errors.append(
                    f"Le module '{module.titre}' contient des formateurs non autorisés."
                )

        return errors

    @staticmethod
    @transaction.atomic
    def sync_action_components(action, assignments, request=None):
        existing_progress = {
            (progress.module_id, progress.formateur_id): progress
            for progress in ModuleProgress.objects.filter(action=action)
        }

        all_assigned_formateur_ids = set()
        created_progressions = 0
        removed_progressions = 0

        new_assignments = set()

        for module_id, formateur_ids in assignments.items():
            for formateur_id in formateur_ids:
                new_assignments.add((module_id, formateur_id))
                all_assigned_formateur_ids.add(formateur_id)
                if (module_id, formateur_id) not in existing_progress:
                    ModuleProgress.objects.create(
                        action=action,
                        module_id=module_id,
                        formateur_id=formateur_id,
                        statut_module="NC",
                    )
                    created_progressions += 1

        for (module_id, formateur_id), progress_obj in existing_progress.items():
            if (module_id, formateur_id) in new_assignments:
                continue

            if progress_obj.sessions_progress.exists():
                if request is not None:
                    from django.contrib import messages

                    messages.error(
                        request,
                        f"Le formateur {progress_obj.formateur} ne peut pas être retiré du module "
                        f"'{progress_obj.module.titre}' car des séances de formation ont déjà été enregistrées.",
                    )
                all_assigned_formateur_ids.add(formateur_id)
                continue

            progress_obj.delete()
            removed_progressions += 1

        if all_assigned_formateur_ids:
            action.formateurs.set(list(all_assigned_formateur_ids))
        else:
            action.formateurs.clear()

        return ActionWorkflowResult(
            action=action,
            created_progressions=created_progressions,
            removed_progressions=removed_progressions,
            assigned_formateurs=len(all_assigned_formateur_ids),
        )

    @staticmethod
    def ensure_action_matches_formation(action):
        if not action.pk or not action.formation_id:
            return
        module_formation_ids = set(action.formation.modules.values_list("id", flat=True))
        invalid = ModuleProgress.objects.filter(action=action).exclude(module_id__in=module_formation_ids)
        if invalid.exists():
            raise ValidationError("Certains modules liés à l'action n'appartiennent pas à sa formation.")

    @staticmethod
    def extract_action_schedules(post_data):
        schedules = []
        day_values = post_data.getlist("course_schedule_day")
        start_values = post_data.getlist("course_schedule_start")
        end_values = post_data.getlist("course_schedule_end")

        max_len = max(len(day_values), len(start_values), len(end_values))
        for index in range(max_len):
            day = day_values[index] if index < len(day_values) else ""
            start = start_values[index] if index < len(start_values) else ""
            end = end_values[index] if index < len(end_values) else ""
            if not day and not start and not end:
                continue
            schedules.append(
                {
                    "jour_semaine": day,
                    "heure_debut": start,
                    "heure_fin": end,
                }
            )
        return schedules

    @staticmethod
    def validate_action_schedules(schedules):
        errors = []
        if not schedules:
            errors.append("Ajoutez au moins un créneau de cours pour l'action.")
            return errors

        seen = set()
        for index, schedule in enumerate(schedules, start=1):
            day = schedule.get("jour_semaine")
            start = schedule.get("heure_debut")
            end = schedule.get("heure_fin")
            if day in (None, ""):
                errors.append(f"Le créneau {index} doit préciser un jour de cours.")
                continue
            if start in (None, "") or end in (None, ""):
                errors.append(f"Le créneau {index} doit préciser une heure de début et une heure de fin.")
                continue

            try:
                day_int = int(day)
            except (TypeError, ValueError):
                errors.append(f"Le créneau {index} contient un jour de cours invalide.")
                continue

            if day_int < 0 or day_int > 6:
                errors.append(f"Le créneau {index} contient un jour de cours invalide.")
                continue

            try:
                start_time = datetime.strptime(start, "%H:%M").time()
                end_time = datetime.strptime(end, "%H:%M").time()
            except (TypeError, ValueError):
                errors.append(f"Le créneau {index} contient une heure invalide.")
                continue

            if end_time <= start_time:
                errors.append(f"Le créneau {index} doit avoir une heure de fin postérieure à l'heure de début.")
                continue

            key = (day_int, start, end)
            if key in seen:
                errors.append(f"Le créneau {index} est dupliqué.")
                continue
            seen.add(key)

        return errors

    @staticmethod
    @transaction.atomic
    def sync_action_schedules(action, schedules):
        action.course_schedules.all().delete()

        created_count = 0
        for index, schedule in enumerate(schedules, start=1):
            ActionSchedule.objects.create(
                action=action,
                jour_semaine=int(schedule["jour_semaine"]),
                heure_debut=datetime.strptime(schedule["heure_debut"], "%H:%M").time(),
                heure_fin=datetime.strptime(schedule["heure_fin"], "%H:%M").time(),
                ordre=index,
            )
            created_count += 1
        return created_count

    @staticmethod
    def build_session_initial(module_progress):
        """
        Build the default values for a quick session planning flow.

        The suggestion is intentionally simple:
        - next date = last session date + 1 day, or action start date
        - hours = reused from the last session when available, otherwise a standard slot
        - topics = module description, then module title as fallback
        """
        action = module_progress.action
        last_session = (
            module_progress.sessions_progress.filter(statut__in=["PLANIFIEE", "REALISEE", "REPORTEE"])
            .order_by("-actual_date", "-planned_date", "-planned_start_time", "-created_at")
            .first()
        )

        planned_date = action.date_debut
        planned_start_time = time(8, 0)
        planned_end_time = None
        planned_topics = module_progress.module.description or module_progress.module.titre

        reference_date = action.date_debut - timedelta(days=1)
        if last_session:
            reference_date = last_session.actual_date or last_session.planned_date or reference_date

        next_schedule, next_date = action.get_next_course_schedule(reference_date)
        if next_schedule and next_date:
            planned_date = next_date
            planned_start_time = next_schedule.heure_debut
            planned_end_time = next_schedule.heure_fin
        else:
            duration_hours = module_progress.module.duree_heures or 2
            duration_hours = max(2, min(duration_hours, 8))
            planned_end_time = (datetime.combine(planned_date, planned_start_time) + timedelta(hours=duration_hours)).time()

        subject_plan = module_progress.get_subject_planning()
        if subject_plan:
            subject = subject_plan["subject"]
            if subject.description:
                planned_topics = subject.description
            else:
                planned_topics = subject.titre

        return {
            "planned_date": planned_date,
            "planned_start_time": planned_start_time,
            "planned_end_time": planned_end_time,
            "planned_topics": planned_topics,
            "statut": "PLANIFIEE",
        }

    @staticmethod
    def get_action_valid_dates(action):
        """
        Calculates all valid dates for an action based on its start/end dates
        and defined weekly schedules.
        """
        valid_dates = []
        schedules = action.course_schedules.all()
        if not schedules.exists():
            return []

        active_weekdays = {s.jour_semaine for s in schedules}
        
        current_date = action.date_debut
        while current_date <= action.date_fin:
            if current_date.weekday() in active_weekdays:
                # On trouve le créneau correspondant pour l'affichage si besoin, 
                # mais ici on veut juste la date unique
                valid_dates.append(current_date)
            current_date += timedelta(days=1)
            
        return valid_dates
