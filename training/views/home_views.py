from django.shortcuts import render
from django.views.generic import View

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
        ctx = {
            "link":"home",
            "nbformations" : Formation.objects.count(),
            "nbfilieres" : Filiere.objects.count(),
            "nbstagiaires" : Stagiaire.objects.count(),
            "nbactions" : Action.objects.count(),
            "user" : user
        }
        return render(request, "home/index.html", ctx)
    