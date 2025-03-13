from django.views.generic import ListView, DetailView

from training.models import Filiere

class FiliereListView(ListView):
    context_object_name = "filiere_list"
    queryset = Filiere.objects.all()
    template_name = "training/filieres.html"

class FiliereDetailView(DetailView):
    model = Filiere
    template_name = "training/filiere.html"
