from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from intern.models import Stagiaire, Categorie

class StagiaireListView(ListView):
    context_object_name = "stagiaire_list"
    queryset = Stagiaire.objects.all()
    paginate_by = 4
    template_name = "intern/stagiaires.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['link'] = "stagiaires"
        return ctx

class StagiaireDetailView(DetailView):
    model = Stagiaire
    template_name = "intern/stagiaire.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['stagiaires'] = Stagiaire.objects.all()
        ctx['titre'] = "Voir"
        return ctx


class StagiaireCreateView(View):
    def get(self, request):
        categories = Categorie.objects.all()
        ctx = {
            "categories":categories,
            "titre" : "Saisie d'une formation",
            "mode" : "new"
        }
        return render(request, 'intern/stagiaire.html', ctx)
    
    def post(self, request):
        nom = request.POST['nom']
        postnom = request.POST['postnom']
        prenom = request.POST['prenom']
        adresse = request.POST['adresse']
        sexe = request.POST['sexe']
        telephone = request.POST['telephone']
        id_categorie = request.POST['categorie']

        stagiaire = Stagiaire(
            nom = nom,
            postnom = postnom,
            prenom = prenom,
            adresse = adresse,
            sexe = sexe,
            telephone = telephone,
            categorie_id = id_categorie
        )
        stagiaire.save()

        return HttpResponseRedirect("/intern/stagiaires")
