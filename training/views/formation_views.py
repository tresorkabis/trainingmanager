from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView

from training.models import Filiere, Formation

class FormationListView(ListView):
    context_object_name = "formation_list"
    queryset = Formation.objects.all()
    paginate_by = 3
    template_name = "training/formations.html"

class FormationDetailView(DetailView):
    model = Formation
    template_name = "training/formation.html"


class FormationCreateView(View):
    def get(self, request):
        filieres = Filiere.objects.all()
        ctx = {
            "filieres":filieres
        }
        return render(request, 'training/formation.html', ctx)
    
    def post(self, request):
        nom = request.POST['nom']
        duree = request.POST['duree']
        id_filiere = request.POST['filiere']
        fraismateriels = request.POST['fraism']

        formation = Formation(
            nom = nom,
            duree = duree,
            filiere_id = id_filiere,
            fraismateriels = fraismateriels
        )
        formation.save()

        return HttpResponseRedirect("/training/formations")