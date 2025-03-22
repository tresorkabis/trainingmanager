from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView

from intern.models import Stagiaire, Categorie

class StagiaireListView(ListView):
    context_object_name = "stagiaire_list"
    queryset = Stagiaire.objects.all()
    template_name = "intern/stagiaires.html"

class StagiaireDetailView(DetailView):
    model = Stagiaire
    template_name = "intern/stagiaire.html"


class StagiaireCreateView(View):
    def get(self, request):
        categorie = Categorie.objects.all()
        ctx = {
            "categorie":categorie
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
