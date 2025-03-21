from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView
from training.models import Filiere, Service

class FiliereListView(ListView):
    context_object_name = "filiere_list"
    queryset = Filiere.objects.all()
    template_name = "training/filieres.html"

class FiliereDetailView(DetailView):
    model = Filiere
    template_name = "training/filiere.html"

class FiliereCreateView(View):
    def get(self, request):
        services = Service.objects.all()
        ctx = {
            "services":services
        }
        return render(request, 'training/filiere.html', ctx)
    
    def post(self, request):
        nom = request.POST['nom']
        id_service = request.POST['service']

        filiere = Filiere(
            nom = nom,
            service_id = id_service
        )
        filiere.save()

        return HttpResponseRedirect("/training/filieres")
