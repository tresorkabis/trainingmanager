from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView

from progress.models import Formateur

class FormateurListView(ListView):
    context_object_name = "formateur_list"
    queryset = Formateur.objects.all()
    template_name = "progress/formateurs.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['link'] = "formateurs"
        return ctx

class FormateurDetailView(DetailView):
    model = Formateur
    template_name = "progress/formateurs.html"
class FormateurCreateView(View):
    def get(self, request):
        formateur = Formateur.objects.all()
        ctx = {
            "formateur":formateur
        }
        return render(request, 'progress/formateurs.html', ctx)
    
    def post(self, request):
        matricule= request.POST['matricule']
        nom = request.POST['nom']
        postnom = request.POST['postnom']
        adresse = request.POST['adresse']
        telephone = request.POST['telephone']
        email = request.POST['email']

        formateur= Formateur(
            matricule = matricule,
            nom = nom,
            postnom = postnom,
            adresse = adresse,
            telephone = telephone,
            email= email
        )
        formateur.save()

        return HttpResponseRedirect("/progress/formateur")
