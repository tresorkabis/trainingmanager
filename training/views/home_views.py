from django.shortcuts import render
from django.views.generic import View
from django.db.models import Count

from intern.models import Stagiaire
from progress.models import Action
from training.models import Filiere, Formation
from users.models import User
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


class HomeView(View):

    @method_decorator(login_required)
    def get(self, request):
        user = None
        if request.user.id:
            user = User.objects.get(pk=request.user.id)

        stagiaire_counts = {
            item["detailaction__action__formation__filiere__nom"]: item["total"]
            for item in Stagiaire.objects.exclude(detailaction__action__formation__filiere__nom__isnull=True)
            .values("detailaction__action__formation__filiere__nom")
            .annotate(total=Count("id"))
        }
        action_counts = {
            item["formation__filiere__nom"]: item["total"]
            for item in Action.objects.exclude(formation__filiere__nom__isnull=True)
            .values("formation__filiere__nom")
            .annotate(total=Count("id"))
        }

        filiere_categories = sorted(
            set(stagiaire_counts.keys()) | set(action_counts.keys()),
            key=lambda name: (-(stagiaire_counts.get(name, 0) + action_counts.get(name, 0)), name),
        )

        dashboard_chart = {
            "categories": filiere_categories,
            "series": [
                {
                    "name": "Stagiaires",
                    "data": [stagiaire_counts.get(name, 0) for name in filiere_categories],
                },
                {
                    "name": "Actions planifiées",
                    "data": [action_counts.get(name, 0) for name in filiere_categories],
                },
            ],
        }

        ctx = {
            "link":"home",
            "nbformations" : Formation.objects.count(),
            "nbfilieres" : Filiere.objects.count(),
            "nbstagiaires" : Stagiaire.objects.count(),
            "nbactions" : Action.objects.count(),
            "user" : user,
            "dashboard_chart": dashboard_chart,
        }
        return render(request, "home/index.html", ctx)
    
