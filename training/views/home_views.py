from datetime import date, timedelta

from django.shortcuts import render
from django.views.generic import View
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth, TruncWeek
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.cache import cache

from intern.models import Stagiaire
from progress.models import Action, DetailAction, Paiement, SessionProgress
from training.models import Filiere, Formation


class HomeView(View):

    @method_decorator(login_required)
    def get(self, request):
        user = request.user

        # Initialisation des querysets de base
        stagiaires_queryset = Stagiaire.objects.all()
        actions_queryset = Action.objects.select_related('formation__filiere').all()
        metiers_queryset = Formation.objects.select_related('filiere').all()
        filieres_queryset = Filiere.objects.select_related('service').all()

        # Filtrage basé sur le rôle de l'utilisateur
        if user.is_superuser or (user.profile and user.profile.name in ["Manager", "Conseiller"]):
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
        # Agréger les stagiaires et les actions par filière en une seule fois
        filiere_stats = filieres_queryset.annotate(
            stagiaire_count=Count('formations__actions__detailaction__stagiaire', distinct=True),
            action_count=Count('formations__actions', distinct=True)
        ).filter(nom__isnull=False) # Exclure les filières sans nom

        # Calculer un score total pour le tri
        filiere_totals_list = [
            (f.nom, f.stagiaire_count, f.action_count, f.stagiaire_count + f.action_count)
            for f in filiere_stats if (f.stagiaire_count + f.action_count) > 0
        ]

        # Trier par score total (décroissant) puis par nom (alphabétique)
        sorted_filieres = sorted(
            filiere_totals_list,
            key=lambda item: (-item[3], item[0]),
        )

        top_limit = 6
        top_filiere_names = [item[0] for item in sorted_filieres[:top_limit]]

        stagiaire_counts = {item[0]: item[1] for item in sorted_filieres}
        action_counts = {item[0]: item[2] for item in sorted_filieres}

        categories = top_filiere_names[:]
        stagiaire_data = [stagiaire_counts.get(name, 0) for name in top_filiere_names]
        action_data = [action_counts.get(name, 0) for name in top_filiere_names]

        if len(sorted_filieres) > top_limit:
            other_filieres = sorted_filieres[top_limit:]
            categories.append("Autres")
            stagiaire_data.append(sum(item[1] for item in other_filieres))
            action_data.append(sum(item[2] for item in other_filieres))

        dashboard_chart = {
            "title": "Répartition par filière",
            "categories": categories,
            "series": [
                {"name": "Stagiaires", "data": stagiaire_data},
                {"name": "Actions", "data": action_data},
            ],
        }

        # =========== GRAPHIQUE : Encaissements mensuels ===========
        paiements_qs = Paiement.objects.filter(action__in=actions_queryset) if not (user.is_superuser or (user.profile and user.profile.name in ["Manager", "Conseiller"])) else Paiement.objects.all()
        
        today = date.today()
        # Date de début pour la période de 6 mois
        six_months_ago = today - timedelta(days=180)

        # Générer tous les mois des 6 derniers mois pour s'assurer qu'il n'y a pas de trous
        all_months = {}
        current_month = today
        for _ in range(6):
            all_months[current_month.strftime("%Y-%m")] = 0.0
            # Aller au mois précédent
            current_month = (current_month.replace(day=1) - timedelta(days=1))

        # Agréger les paiements par mois avec une seule requête
        monthly_totals = paiements_qs.filter(date_paiement__gte=six_months_ago)\
            .annotate(month=TruncMonth('date_paiement'))\
            .values('month').annotate(total=Sum('montant')).values('month', 'total')

        for item in monthly_totals:
            all_months[item['month'].strftime("%Y-%m")] = float(item['total'])

        sorted_months = sorted(all_months.items())

        paiements_chart = {
            "title": "Encaissements mensuels (USD)",
            "categories": [item[0] for item in sorted_months],
            "series": [{"name": "Encaissements", "data": [item[1] for item in sorted_months]}],
        }

        # =========== GRAPHIQUE : Statut des actions ===========
        statut_ordered = ["Planifiée", "En cours", "Terminée", "Annulée"]
        statut_colors_map = {
            "Planifiée": "#ffc107",
            "En cours": "#0dcaf0",
            "Terminée": "#198754",
            "Annulée": "#dc3545",
        }
        
        statut_counts_query = actions_queryset.values('statut').annotate(count=Count('id'))
        statut_map = {'PLANIFIEE': "Planifiée", 'EN_COURS': "En cours", 'TERMINEE': "Terminée", 'ANNULEE': "Annulée"}
        statut_counts = {label: 0 for label in statut_ordered}
        for item in statut_counts_query:
            label = statut_map.get(item['statut'])
            if label:
                statut_counts[label] = item['count']

        actions_status_chart = {
            "title": "Statut des actions",
            "series": [statut_counts[s] for s in statut_ordered],
            "labels": statut_ordered[:],
            "colors": [statut_colors_map[s] for s in statut_ordered],
        }

        # =========== GRAPHIQUE : Progression des séances par semaine ===========
        sessions = SessionProgress.objects.filter(module_progress__action__in=actions_queryset)
        six_weeks_ago = today - timedelta(weeks=6)
        sessions_recent = sessions.filter(planned_date__gte=six_weeks_ago)

        # Agréger les séances planifiées par semaine
        planned_by_week = sessions_recent.annotate(week=TruncWeek('planned_date'))\
            .values('week').annotate(count=Count('id')).order_by('week')

        # Agréger les séances réalisées par semaine
        realized_by_week = sessions_recent.filter(statut="REALISEE")\
            .annotate(week=TruncWeek('planned_date'))\
            .values('week').annotate(count=Count('id')).order_by('week')

        # Fusionner les données
        weekly_data = {item['week']: {'planned': item['count'], 'realized': 0} for item in planned_by_week}
        for item in realized_by_week:
            if item['week'] in weekly_data:
                weekly_data[item['week']]['realized'] = item['count']

        sorted_weeks = sorted(weekly_data.keys())
        sessions_chart = {
            "title": "Séances par semaine",
            "categories": [w.strftime("%d/%m") for w in sorted_weeks],
            "series": [
                {"name": "Prévues", "data": [weekly_data[w]["planned"] for w in sorted_weeks]},
                {"name": "Réalisées", "data": [weekly_data[w]["realized"] for w in sorted_weeks]},
            ],
        }

        # Préparation des données pour le composant tm_hero
        hero_stats = [
            {'label': 'Formations', 'value': metiers_queryset.count()},
            {'label': 'Filières', 'value': filieres_queryset.count()},
            {'label': 'Stagiaires', 'value': stagiaires_queryset.count()},
            {'label': 'Actions', 'value': actions_queryset.count()},
        ] 

        # Variables individuelles pour les métriques du template
        nbmetiers = metiers_queryset.count()
        nbfilieres = filieres_queryset.count()
        nbstagiaires = stagiaires_queryset.count()
        nbactions = actions_queryset.count()

        # Si l'utilisateur est Conseiller, fournir un tableau de bord allégé et ciblé
        is_conseiller = bool(user.profile and user.profile.name == 'Conseiller')
        if is_conseiller:
            cache_key = f"conseiller_dashboard_{user.id}"
            cached = cache.get(cache_key)
            if cached:
                return render(request, "home/conseiller_dashboard.html", cached)

            # Récupérer les stagiaires récents (champ limité pour performance)
            # Eviter N+1: inclure updated_at pour la miniature et limiter les champs visités
            recent_stagiaires = stagiaires_queryset.order_by('-updated_at').only('id','nom','postnom','prenom','photo','updated_at')[:8]

            # Récupérer les inscriptions récentes (limitée) et inclure formation pour éviter requêtes supplémentaires
            recent_inscriptions = DetailAction.objects.filter(action__in=actions_queryset)\
                .select_related('stagiaire','action__formation')\
                .only('id','stagiaire_id','action_id')\
                .order_by('-id')[:8]

            # Récupérer les paiements récents filtrés par les actions autorisées pour le conseiller
            recent_paiements = Paiement.objects.filter(action__in=actions_queryset)\
                .select_related('stagiaire','action')\
                .only('id','montant','date_paiement','stagiaire_id','action_id')\
                .order_by('-date_paiement')[:6]

            ctx = {
                "link": "home",
                "user": user,
                "hero_stats": hero_stats,
                "nbmetiers": nbmetiers,
                "nbfilieres": nbfilieres,
                "nbstagiaires": nbstagiaires,
                "nbactions": nbactions,
                "is_conseiller": True,
                "recent_stagiaires": list(recent_stagiaires),
                "recent_inscriptions": list(recent_inscriptions),
                "recent_paiements": list(recent_paiements),
            }

            # Mettre en cache la vue du conseiller pour courte durée (spécifique à l'utilisateur)
            cache.set(cache_key, ctx, timeout=60)

            return render(request, "home/conseiller_dashboard.html", ctx)

        # Par défaut: tableau de bord complet
        ctx = {
            "link": "home",
            "user": user,
            "hero_stats": hero_stats,
            "nbmetiers": nbmetiers,
            "nbfilieres": nbfilieres,
            "nbstagiaires": nbstagiaires,
            "nbactions": nbactions,
            "dashboard_chart": dashboard_chart,
            "paiements_chart": paiements_chart,
            "actions_status_chart": actions_status_chart,
            "sessions_chart": sessions_chart,
        }
        return render(request, "home/index.html", ctx)