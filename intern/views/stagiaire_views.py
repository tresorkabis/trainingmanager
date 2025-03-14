from django.views.generic import ListView, DetailView

from intern.models import Stagiaire

class StagiaireListView(ListView):
    context_object_name = "stagiaire_list"
    queryset = Stagiaire.objects.all()
    template_name = "intern/stagiaires.html"

class StagiaireDetailView(DetailView):
    model = Stagiaire
    template_name = "intern/stagiaire.html"
