from django.views.generic import ListView, DetailView

from training.models import Service

class ServiceListView(ListView):
    context_object_name = "filiere_list"
    queryset = Service.objects.all()
    template_name = "training/filieres.html"

class ServiceDetailView(DetailView):
    model = Service
    template_name = "training/filiere.html"
