from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView

from training.models import Filiere, Formation

class FormationListView(ListView):
    context_object_name = "formation_list"
    queryset = Formation.objects.all()
    paginate_by = 4
    template_name = "training/formations.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['link'] = "formations"
        return ctx

class FormationDetailView(DetailView):
    model = Formation
    template_name = "training/formation.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filieres'] = Filiere.objects.all()
        ctx['titre'] = "Voir"
        return ctx


class FormationCreateView(View):
    def get(self, request):
        filieres = Filiere.objects.all()
        ctx = {
            "filieres":filieres,
            "titre" : "Saisie d'une formation",
            "mode" : "new"
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