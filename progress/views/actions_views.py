import json
import datetime
from datetime import date

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Count, Min, Max
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DeleteView, DetailView, ListView, UpdateView

from progress.models import Action, Formateur, ModuleProgress, TypeAction, SessionProgress
from progress.services import ActionWorkflowService
from intern.models import Stagiaire
from training.models import Formation, Module


class ActionPermissionMixin:
    def normalize_formateur_ids(self, formateur_ids):
        return [int(formateur_id) for formateur_id in formateur_ids if str(formateur_id).isdigit()]

    def get_allowed_formations(self):
        user = self.request.user
        queryset = Formation.objects.all().prefetch_related("modules__formateurs")
        
        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            return queryset
        if user.profile and user.profile.name == "Chef de filière" and user.filiere:
            return queryset.filter(filiere=user.filiere)
        if user.profile and user.profile.name == "Chef de service" and user.service:
            return queryset.filter(filiere__service=user.service)
        return Formation.objects.none()

    def get_queryset(self):
        allowed_formations = self.get_allowed_formations()
        if not allowed_formations.exists():
            return Action.objects.none()
        return (
            Action.objects.filter(formation__in=allowed_formations)
            .select_related("formation", "formation__filiere")
            .prefetch_related("formateurs")
            .annotate(stagiaire_total=Count("detailaction", distinct=True), formateur_total=Count("formateurs", distinct=True))
            .order_by("-date_debut", "-id")
        )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if not self.get_queryset().filter(pk=obj.pk).exists():
            raise PermissionDenied("Vous n'avez pas la permission d'accéder à cette ressource.")
        return obj

    def enforce_manage_permission(self):
        if not self.get_allowed_formations().exists():
            raise PermissionDenied("Vous n'avez pas la permission de gérer les actions.")

    def get_action_status(self, action):
        statut_map = {
            'PLANIFIEE': {"label": "Planifiée", "badge": "bg-light-primary text-primary", "key": "planned"},
            'EN_COURS': {"label": "En cours", "badge": "bg-light-success text-success", "key": "ongoing"},
            'TERMINEE': {"label": "Terminée", "badge": "bg-light-secondary text-dark", "key": "completed"},
            'ANNULEE': {"label": "Annulée", "badge": "bg-light-danger text-danger", "key": "canceled"},
        }
        return statut_map.get(getattr(action, 'statut', None), statut_map['EN_COURS'])

    def build_form_context(self, **kwargs):
        allowed_formations = self.get_allowed_formations()
        all_formateurs = Formateur.objects.filter(active=True).order_by("nom", "postnom")
        all_type_actions = TypeAction.objects.filter(active=True).order_by("libelle")
        formations_data = ActionWorkflowService.build_formations_payload(allowed_formations)
        modules_formateurs_assignment = {}

        context = {
            "formations": allowed_formations,
            "formateurs": all_formateurs,
            "type_actions": all_type_actions,
            "formations_json": formations_data,
            "formateurs_json": list(all_formateurs.values("id", "nom", "postnom", "prenom")),
            "today": date.today(),
            "selected_formateur_ids": [], # This is for Action.formateurs, which we might remove or keep separate
            "hero_actions": [
                {'label': 'Retour aux actions', 'url': reverse_lazy('actions'), 'class': 'btn-light-secondary', 'icon': 'bi bi-arrow-left'},
            ],
        }

        # If in update mode, populate initial module-formateur assignments for the specific action being edited
        action_object = kwargs.get('object') # Get the action object if available
        if action_object and action_object.pk:
            # Stats pour le mode édition (KPI cards)
            status_meta = self.get_action_status(action_object)
            context["hero_stats"] = [
                {'label': 'Inscrits', 'value': action_object.detailaction_set.count()},
                {'label': 'Formateurs', 'value': action_object.formateurs.count()},
                {'label': 'Statut', 'value': status_meta['label']},
            ]
            
            # On récupère les assignations réelles depuis ModuleProgress pour CETTE action
            progressions = ModuleProgress.objects.filter(action=action_object)
            for prog in progressions:
                if prog.module_id not in modules_formateurs_assignment:
                    modules_formateurs_assignment[prog.module_id] = []
                modules_formateurs_assignment[prog.module_id].append(prog.formateur_id)
            context["modules_formateurs_assignment_json"] = modules_formateurs_assignment
            # On charge les créneaux existants pour le formulaire
            context["action_schedules"] = list(action_object.course_schedules.all().order_by("jour_semaine", "heure_debut"))
        else:
            context["modules_formateurs_assignment_json"] = {} # Empty for create view
            context["action_schedules"] = []
            context["stats"] = None

        context.update(kwargs)
        return context

    def _save_module_assignments(self, action, request):
        assignments = ActionWorkflowService.extract_module_assignments(action.formation, request.POST)
        return ActionWorkflowService.sync_action_components(action, assignments, request=request)

    def validate_action_payload(self, date_debut, date_fin, formation_id, formateur_ids):
        errors = []
        allowed_formations = self.get_allowed_formations()

        if not allowed_formations.filter(pk=formation_id).exists():
            errors.append("La formation sélectionnée n'est pas autorisée pour votre périmètre.")
        if date_fin and date_debut and date_fin < date_debut:
            errors.append("La date de fin doit être postérieure ou égale à la date de début.")

        if formation_id:
            try:
                selected_formation = Formation.objects.get(pk=formation_id)
                pass # No longer validating Action.formateurs directly here
            except Formation.DoesNotExist:
                errors.append("La formation sélectionnée est introuvable.")

        return errors

    def validate_action_components(self, formation, request):
        assignments = ActionWorkflowService.extract_module_assignments(formation, request.POST)
        return ActionWorkflowService.validate_module_assignments(formation, assignments)


@method_decorator(login_required, name="dispatch")
class ActionListViews(ActionPermissionMixin, ListView):
    context_object_name = "action_list"
    model = Action
    template_name = "progress/actions.html"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        page_actions = list(ctx["object_list"])
        all_actions = self.get_queryset()

        for action in page_actions:
            action.status_meta = self.get_action_status(action)
            # Calcul de la progression
            progressions = action.module_progressions.all()
            total_modules = action.formation.modules.count()
            if total_modules > 0:
                # On considère un module "avancé" s'il est au moins en cours (EC)
                # Et "terminé" s'il est TE ou VA.
                completed_count = progressions.filter(statut_module__in=['TE', 'VA']).values('module').distinct().count()
                action.progression_percent = int((completed_count / total_modules) * 100)
            else:
                action.progression_percent = 0

        ctx["object_list"] = page_actions
        ctx["link"] = "actions"
        ctx["stats"] = {
            "total": all_actions.count(),
            "planned": all_actions.filter(statut='PLANIFIEE').count(),
            "ongoing": all_actions.filter(statut='EN_COURS').count(),
            "completed": all_actions.filter(statut='TERMINEE').count(),
            "enrolled": all_actions.aggregate(total=Count("detailaction", distinct=True))["total"] or 0,
        }

        # Préparation des données pour le composant tm_hero
        ctx["hero_actions"] = [
            {'label': 'Nouvelle action', 'url': reverse_lazy('action_create'), 'icon': 'bi bi-clipboard-plus'},
            {'label': 'Voir les formations', 'url': reverse_lazy('formations'), 'class': 'btn-light-secondary', 'icon': 'bi bi-journal-text'},
        ]

        ctx["hero_stats"] = [
            {'label': 'Total Actions', 'value': ctx['stats']['total']},
            {'label': 'En cours', 'value': ctx['stats']['ongoing']},
            {'label': 'Terminées', 'value': ctx['stats']['completed']},
            {'label': 'Inscrits', 'value': ctx['stats']['enrolled']},
        ]
        return ctx


@method_decorator(login_required, name="dispatch")
class ActionDetailViews(ActionPermissionMixin, DetailView):
    model = Action
    template_name = "progress/action_detail.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("formation", "formation__filiere")
            .prefetch_related(
                "detailaction_set__stagiaire",
                "formateurs",
                "course_schedules",
                "formation__modules__formateurs",
                "formation__modules__subjects",
                "formation__modules__seances__formateur",
                "formation__modules__seances__evaluateur",
                "module_progressions",
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        action = ctx["object"]
        inscriptions = action.detailaction_set.select_related("stagiaire").order_by("stagiaire__nom", "stagiaire__postnom")
        inscrit_ids = list(inscriptions.values_list("stagiaire_id", flat=True))

        # On récupère la liste des modules une seule fois
        modules_list = list(action.formation.modules.all().order_by("ordre"))
        # On récupère toutes les progressions de cette action pour filtrer en mémoire (plus performant)
        all_progressions = list(action.module_progressions.all().select_related('formateur'))

        for module in modules_list:
            module.sessions = list(
                module.seances.select_related("formateur", "evaluateur").order_by("date_debut_reelle", "created_at")
            )
            # On attache les progressions filtrées pour ce module spécifique
            module.module_progressions = [p for p in all_progressions if p.module_id == module.id]
            module.module_progressions.sort(key=lambda x: x.formateur.nom)
            
            # Calcul de la progression horaire du module
            m_hours_done = 0
            for mp in module.module_progressions:
                for s in mp.sessions_progress.filter(statut='REALISEE'):
                    if s.actual_start_time and s.actual_end_time:
                        start = datetime.datetime.combine(datetime.date.today(), s.actual_start_time)
                        end = datetime.datetime.combine(datetime.date.today(), s.actual_end_time)
                        m_hours_done += (end - start).total_seconds() / 3600
            
            module.hours_done = round(m_hours_done, 1)
            module.progress_percent = int((m_hours_done / module.duree_heures * 100)) if module.duree_heures > 0 else 0
            if module.progress_percent > 100: module.progress_percent = 100

        # Statistiques financières
        total_attendu = (action.formation.cout or 0) * inscriptions.count()
        total_paye = sum(p.montant for ins in inscriptions for p in ins.stagiaire.paiements.filter(action=action))
        
        ctx["finance"] = {
            "total_attendu": total_attendu,
            "total_paye": total_paye,
            "solde": total_attendu - total_paye,
            "percent": int((total_paye / total_attendu * 100)) if total_attendu > 0 else 0
        }

        # Données pour le graphique financier (Donut)
        ctx["finance_chart"] = {
            'series': [float(total_paye), float(total_attendu - total_paye)],
            'labels': ['Encaissé', 'Reste à percevoir']
        }

        ctx["modules"] = modules_list
        ctx["status_meta"] = self.get_action_status(action)
        ctx["inscriptions"] = inscriptions
        ctx["stagiaires_disponibles"] = Stagiaire.objects.filter(active=True).exclude(pk__in=inscrit_ids).order_by("nom", "postnom", "prenom")
        ctx["link"] = "actions"
        ctx["inscription_count"] = inscriptions.count()
        ctx["formateurs_assignes"] = action.formateurs.all().order_by("nom", "postnom")
        ctx["course_schedules"] = action.course_schedules.all().order_by("jour_semaine", "heure_debut", "ordre", "id")

        # Données pour le graphique d'évolution
        all_sessions = SessionProgress.objects.filter(module_progress__action=action).order_by('planned_date')

        evolution_data = {
            'categories': [],
            'planned': [],
            'actual': []
        }

        cumul_planned = 0
        cumul_actual = 0

        # Construire daily_stats à partir des sessions
        daily_stats = {}
        for session in all_sessions:
            planned_key = session.planned_date
            actual_key = session.actual_date

            # Heures planifiées
            if session.planned_start_time and session.planned_end_time and planned_key:
                if planned_key not in daily_stats:
                    daily_stats[planned_key] = {'p': 0.0, 'a': 0.0}
                start = datetime.datetime.combine(planned_key, session.planned_start_time)
                end = datetime.datetime.combine(planned_key, session.planned_end_time)
                daily_stats[planned_key]['p'] += round((end - start).total_seconds() / 3600, 1)

            # Heures réalisées
            if session.actual_start_time and session.actual_end_time and actual_key:
                if actual_key not in daily_stats:
                    daily_stats[actual_key] = {'p': 0.0, 'a': 0.0}
                start = datetime.datetime.combine(actual_key, session.actual_start_time)
                end = datetime.datetime.combine(actual_key, session.actual_end_time)
                daily_stats[actual_key]['a'] += round((end - start).total_seconds() / 3600, 1)

        # Trouver la date de la dernière séance réalisée pour savoir où arrêter la courbe
        last_realized_session = all_sessions.filter(statut='REALISEE').order_by('-actual_date', '-planned_date').first()
        last_realized_date = None
        if last_realized_session:
            last_realized_date = last_realized_session.actual_date or last_realized_session.planned_date

        for d in sorted(daily_stats.keys()):
            h_p = daily_stats[d]['p']
            h_a = daily_stats[d]['a']

            if h_p > 0 or h_a > 0:
                cumul_planned += h_p
                evolution_data['planned'].append(round(cumul_planned, 1))

                # Le Réalisé s'arrête après la date de dernière réalisation
                if last_realized_date and d <= last_realized_date:
                    cumul_actual += h_a
                    evolution_data['actual'].append(round(cumul_actual, 1))
                else:
                    evolution_data['actual'].append(None) # null en JS = arrêt de la ligne

                evolution_data['categories'].append(d.strftime('%d/%m'))

        if not evolution_data['categories']:
            ctx["evolution_chart"] = {'categories': None}
        else:
            ctx["evolution_chart"] = evolution_data

        # Stats pour le Hero
        ctx["hero_stats"] = [
            {'label': 'Inscrits', 'value': ctx["inscription_count"]},
            {'label': 'Modules', 'value': len(modules_list)},
            {'label': 'Statut', 'value': ctx["status_meta"]['label']},
            {'label': 'Reste à payer', 'value': f"{ctx['finance']['solde']:,.0f} USD"},
        ]

        ctx["hero_actions"] = [
            {'label': 'Retour', 'url': reverse_lazy('actions'), 'icon': 'bi bi-arrow-left', 'class': 'btn-light-secondary'},
            {'label': 'Progressions', 'url': reverse_lazy('module_progressions') + f'?action={action.pk}', 'icon': 'bi bi-list-task'},
            {'label': 'Mettre à jour les statuts', 'url': reverse_lazy('action_update_progressions', kwargs={'pk': action.pk}), 'icon': 'bi bi-arrow-repeat'},
            {'label': 'Modifier', 'url': reverse_lazy('action_update', kwargs={'pk': action.pk}), 'icon': 'bi bi-pencil'},
        ]

        return ctx


@method_decorator(login_required, name="dispatch")
class ActionCreateView(ActionPermissionMixin, View):
    def get(self, request):
        self.enforce_manage_permission()
        ctx = self.build_form_context(
            titre="Créer",
            mode="new",
            submitted={},
            selected_formateur_ids=[],
        )
        return render(request, "progress/action.html", ctx)

    def post(self, request):
        self.enforce_manage_permission()

        description = request.POST["description"].strip()
        date_debut = request.POST["date_debut"]
        date_fin = request.POST["date_fin"]
        formation_id = request.POST["formation"]
        type_action_id = request.POST.get("type_action")
        lieu = request.POST.get("lieu", "").strip()

        formation = get_object_or_404(Formation, pk=formation_id)
        schedules = ActionWorkflowService.extract_action_schedules(request.POST)
        errors = self.validate_action_payload(date_debut, date_fin, formation_id, [])
        errors.extend(self.validate_action_components(formation, request))
        errors.extend(ActionWorkflowService.validate_action_schedules(schedules))
        if errors:
            ctx = self.build_form_context(
                titre="Créer",
                mode="new",
                submitted=request.POST,
                selected_formateur_ids=[],
                form_errors=errors,
                submitted_schedules=schedules,
            )
            return render(request, "progress/action.html", ctx, status=400)

        with transaction.atomic():
            action = Action(
                description=description,
                date_debut=date_debut,
                date_fin=date_fin,
                formation_id=formation_id,
                type_action_id=type_action_id,
                lieu=lieu,
            )
            action.save()
            ActionWorkflowService.sync_action_schedules(action, schedules)
            result = self._save_module_assignments(action, request)

        messages.success(
            request,
            f"L'action a été créée avec {result.created_progressions} progression(s) de module."
        )
        return HttpResponseRedirect(reverse_lazy("action", kwargs={"pk": action.pk}))

@method_decorator(login_required, name="dispatch")
class ActionUpdateView(ActionPermissionMixin, UpdateView):
    model = Action
    template_name = "progress/action.html"
    fields = ["description", "date_debut", "date_fin", "formation", "type_action", "lieu"]
    success_url = reverse_lazy("actions")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["formation"].queryset = self.get_allowed_formations().select_related("filiere").order_by("nom")
        return form

    def form_valid(self, form):
        schedules = ActionWorkflowService.extract_action_schedules(self.request.POST)
        errors = self.validate_action_payload(
            form.cleaned_data["date_debut"],
            form.cleaned_data["date_fin"],
            str(form.cleaned_data["formation"].pk),
            [],
        )
        errors.extend(self.validate_action_components(form.cleaned_data["formation"], self.request))
        errors.extend(ActionWorkflowService.validate_action_schedules(schedules))
        if errors:
            for error in errors:
                form.add_error(None, error)
            return self.form_invalid(form)

        with transaction.atomic():
            response = super().form_valid(form)
            ActionWorkflowService.sync_action_schedules(self.object, schedules)
            result = self._save_module_assignments(self.object, self.request)

        messages.success(
            self.request,
            f"L'action a été mise à jour avec {result.created_progressions} nouvelle(s) progression(s) de module."
        )
        return HttpResponseRedirect(reverse_lazy("action", kwargs={"pk": self.object.pk}))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            self.build_form_context(
                titre="Modifier",
                mode="edit",
                object=self.object, # Pass the object to build_form_context
                selected_formateur_ids=[], # No longer tracking action-level formateurs
                submitted_schedules=ActionWorkflowService.extract_action_schedules(self.request.POST) if self.request.method == "POST" else [],
            )
        )
        return ctx


@method_decorator(login_required, name="dispatch")
class ActionUpdateProgressionsView(ActionPermissionMixin, View):
    def get(self, request, pk):
        return self._update(request, pk)

    def post(self, request, pk):
        return self._update(request, pk)

    def _update(self, request, pk):
        action = get_object_or_404(Action, pk=pk)
        updated_progressions = 0
        for mp in action.module_progressions.all():
            old = mp.statut_module
            mp.update_statut_module()
            if mp.statut_module != old:
                updated_progressions += 1
        action.update_statut()
        messages.success(request, f"Statuts mis à jour : {updated_progressions} progression(s) modifiée(s).")
        return HttpResponseRedirect(reverse_lazy("action", kwargs={"pk": pk}))


@method_decorator(login_required, name="dispatch")
class ActionDeleteView(ActionPermissionMixin, DeleteView):
    model = Action
    template_name = "progress/action_confirm_delete.html"
    success_url = reverse_lazy("actions")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre"] = "Supprimer"
        return ctx
