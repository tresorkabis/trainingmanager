from django.shortcuts import render
from django.views.generic import View

from intern.models import Stagiaire
from progress.models import Action
from training.models import Filiere, Formation

class HomeView(View):
    def get(self, request):
        ctx = {
            "link":"home",
            "nbformations" : Formation.objects.count(),
            "nbfilieres" : Filiere.objects.count(),
            "nbstagiaires" : Stagiaire.objects.count(),
            "nbactions" : Action.objects.count()
        }
        return render(request, "home/index.html", ctx)