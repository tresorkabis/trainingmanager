from datetime import date, timedelta
from decimal import Decimal

from django.shortcuts import render
from django.views.generic import View
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth, TruncWeek

from intern.models import Stagiaire
from progress.models import Action, DetailAction, Paiement, SessionProgress, ModuleProgress
from training.models import Filiere, Formation, Service
from users.models import User, Profile
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


class HomeView(View):

    @method_decorator(login_required)
    def get(self, request):
        user = request.user

        # Initialisation des querysets de base
        stagiaires_queryset = Stagiaire.objects.all()
        actions_queryset = Action.objects.all()
        metiers_queryset = Formation.objects.all()
        filieres_queryset = Filiere.objects.all()

        # Filtrage basé sur le rôle de l'utilisateur
        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            pass
        elif user.profile and user.profile.name == "Chef de filière" and user.filiere:
            stagiaires_ids = DetailAction.objects.filter(
                action__formation__filiere=user.filiere
            ).values_list('stagiaire_id', flat=True).distinct()
            stagiaires_queryset = stagiaires_queryset.filter(id__in=stagiaires_ids)
            actions_queryset = actions_queryset.filter(formation__filiere=user.filiere)
            metiers_queryset = metiers_queryset.filter(filiere=user.filiere)
            filieres_queryset = filieres_queryset.filter(pk=user.filiere.pk)

        elif user.profile and user.profile.name == "Chef de service" and user.service:
            stagiaires_ids = DetailAction.objects.filter(
                action__formation__filiere__service=user.service
            ).values_list('stagiaire_id', flat=True).distinct()
            stagiaires_queryset = stagiaires_queryset.filter(id__in=stagiaires_ids)
            actions_queryset = actions_queryset.filter(formation__filiere__service=user.service)
            metiers_queryset = metiers_queryset.filter(filiere__service=user.service)
            filieres_queryset = filieres_queryset.filter(service=user.service)
        else:
            stagiaires_queryset = Stagiaire.objects.none()
            actions_queryset = Action.objects.none()
            metiers_queryset = Formation.objects.none()
            filieres_queryset = Filiere.objects.none()

        # =========== GRAPHIQUE EXISTANT : Répartition par filière ===========
        stagiaire_counts_list = DetailAction.objects.filter(stagiaire__in=stagiaires_queryset).values(
            "action__formation__filiere__nom"
        ).annotate(total=Count("stagiaire", distinct=True))

        stagiaire_counts = {
            item["action__formation__filiere__nom"]: item["total"]
            for item in stagiaire_counts_list if item["action__formation__filiere__nom"]
        }

        action_counts = {
            item["formation__filiere__nom"]: item["total"]
            for item in actions_queryset.exclude(formation__filiere__nom__isnull=True)
            .values("formation__filiere__nom")
            .annotate(total=Count("id"))
        }

        filiere_names = set(stagiaire_counts.keys()) | set(action_counts.keys())
        filiere_totals = {
            name: stagiaire_counts.get(name, 0) + action_counts.get(name, 0)
            for name in filiere_names if name
        }

        sorted_filieres = sorted(
            filiere_totals.items(),
            key=lambda item: (-item[1], item[0]),
        )

        top_limit = 6
        top_filiere_names = [name for name, _ in sorted_filieres[:top_limit]]

        categories = top_filiere_names[:]
        stagiaire_data = [stagiaire_counts.get(name, 0) for name in top_filiere_names]
        action_data = [action_counts.get(name, 0) for name in top_filiere_names]

        if len(sorted_filieres) > top_limit:
            other_filieres = sorted_filieres[top_limit:]
            categories.append("Autres")
            stagiaire_data.append(sum(stagiaire_counts.get(name, 0) for name, _ in other_filieres))
            action_data.append(sum(action_counts.get(name, 0) for name, _ in other_filieres))

        dashboard_chart = {
            "title": "Répartition par filière",
            "categories": categories,
            "series": [
                {"name": "Stagiaires", "data": stagiaire_data},
                {"name": "Actions", "data": action_data},
            ],
        }

        # =========== GRAPHIQUE 1 : Encaissements mensuels ===========
        paiements = Paiement.objects.all()
        if not (user.is_superuser or (user.profile and user.profile.name == "Manager")):
            paiements = paiements.filter(action__in=actions_queryset)

        today = date.today()
        months_data = []
        for i in range(5, -1, -1):
            m = today.month - i
            y = today.year
            while m < 1:
                m += 12
                y -= 1
            month_total = paiements.filter(
                date_paiement__year=y,
                date_paiement__month=m,
            ).aggregate(total=Sum('montant'))['total'] or 0
            month_label = f"{y}-{m:02d}"
            months_data.append({
                "label": month_label,
                "total": float(month_total),
            })

        paiements_chart = {
            "title": "Encaissements mensuels (USD)",
            "categories": [m["label"] for m in months_data],
            "series": [{"name": "Encaissements", "data": [m["total"] for m in months_data]}],
        }

        # =========== GRAPHIQUE 2 : Statut des actions (aligné sur la liste /progress/actions/) ===========
        statut_ordered = ["Terminée", "Planifiée", "En cours", "Annulée"]
        statut_colors_map = {
            "Terminée": "#198754",
            "Planifiée": "#ffc107",
            "En cours": "#0dcaf0",
            "Annulée": "#dc3545",
        }
        statut_counts = {label: 0 for label in statut_ordered}
        for action in actions_queryset:
            # Même logique que ActionListViews.get_context_data()
            if action.statut == 'ANNULEE':
                label = "Annulée"
            elif action.statut == 'TERMINEE':
                label = "Terminée"
            elif action.date_debut > today:
                label = "Planifiée"
            else:
                label = "En cours"
            if label in statut_counts:
                statut_counts[label] += 1

        actions_status_chart = {
            "title": "Statut des actions",
            "series": [statut_counts[s] for s in statut_ordered],
            "labels": statut_ordered[:],
            "colors": [statut_colors_map[s] for s in statut_ordered],
        }

        # =========== GRAPHIQUE 3 : Progression des séances par semaine ===========
        sessions = SessionProgress.objects.filter(module_progress__action__in=actions_queryset)
        six_weeks_ago = today - timedelta(weeks=6)
        sessions_recent = sessions.filter(planned_date__gte=six_weeks_ago)

        weekly_data = {}
        for s in sessions_recent:
            if s.planned_date:
                week_start = s.planned_date - timedelta(days=s.planned_date.weekday())
                if week_start not in weekly_data:
                    weekly_data[week_start] = {"planned": 0, "realized": 0}
                weekly_data[week_start]["planned"] += 1
                if s.statut == "REALISEE":
                    weekly_data[week_start]["realized"] += 1

        sorted_weeks = sorted(weekly_data.keys())
        sessions_chart = {
            "title": "Séances par semaine",
            "categories": [w.strftime("%d/%m") for w in sorted_weeks],
            "series": [
                {"name": "Prévues", "data": [weekly_data[w]["planned"] for w in sorted_weeks]},
                {"name": "Réalisées", "data": [weekly_data[w]["realized"] for w in sorted_weeks]},
            ],
        }

        ctx = {
            "link": "home",
            "nbmetiers": metiers_queryset.count(),
            "nbfilieres": filieres_queryset.count(),
            "nbstagiaires": stagiaires_queryset.count(),
            "nbactions": actions_queryset.count(),
            "user": user,
            "dashboard_chart": dashboard_chart,
            "paiements_chart": paiements_chart,
            "actions_status_chart": actions_status_chart,
            "sessions_chart": sessions_chart,
        }
        return render(request, "home/index.html", ctx)