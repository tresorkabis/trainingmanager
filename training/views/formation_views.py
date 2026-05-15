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
        duree_heures = request.POST.get('duree_heures') or 0
        id_filiere = request.POST['filiere']
        cout = request.POST.get('cout') or 0
        fraismateriels = request.POST['fraism']

        formation = Formation(
            nom = nom,
            duree = duree,
            duree_heures = duree_heures,
            filiere_id = id_filiere,
            cout = cout,
            fraismateriels = fraismateriels
        )
        formation.save()

        return HttpResponseRedirect("/training/formations")
