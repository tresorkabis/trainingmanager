from django.views.generic import ListView, DetailView

from training.models import Formation

class FormationListView(ListView):
    context_object_name = "formation_list"
    queryset = Formation.objects.all()
    template_name = "training/formations.html"

class FormationDetailView(DetailView):
    pass
