from django.shortcuts import render
from django.views.generic import View

from intern.models import Stagiaire
from progress.models import Action
from training.models import Filiere, Formation
from users.models import User

class HomeView(View):
    def get(self, request):
        user = None
        if request.user.id:
            user = User.objects.get(pk=request.user.id)
        print("******")
        print(user)
        ctx = {
            "link":"home",
            "nbformations" : Formation.objects.count(),
            "nbfilieres" : Filiere.objects.count(),
            "nbstagiaires" : Stagiaire.objects.count(),
            "nbactions" : Action.objects.count(),
            "user" : user
        }
        return render(request, "home/index.html", ctx)