from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView
from training.models import Filiere, Service

class FiliereListView(ListView):
    context_object_name = "filiere_list"
    queryset = Filiere.objects.all()
    paginate_by = 4
    template_name = "training/filieres.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['link'] = "filieres"
        return ctx

class FiliereDetailView(DetailView):
    model = Filiere
    template_name = "training/filiere.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['services'] = Service.objects.all()
        ctx['titre'] = "Voir"
        return ctx

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
