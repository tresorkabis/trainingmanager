from django.views.generic import ListView, DetailView

from progress.models import Formateur

class FormateurListView(ListView):
    context_object_name = "formateur_list"
    queryset = Formateur.objects.all()
    template_name = "progress/formateurs.html"

class FormateurDetailView(DetailView):
    model = Formateur
    template_name = "progress/formateur.html"
