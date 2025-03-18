from django.views.generic import ListView, DetailView, CreateView

from training.models import Filiere, Formation

class FormationListView(ListView):
    context_object_name = "formation_list"
    queryset = Formation.objects.all()
    template_name = "training/formations.html"

class FormationDetailView(DetailView):
    model = Formation
    template_name = "training/formation.html"


class FormationCreateView(CreateView):
    model = Formation
    template_name = "training/formation.html"
    fields = '__all__'
    success_url = "/formations"

    def get_context_data(self, **kwargs):
        filieres = Filiere.objects.all()
        kwargs['filieres'] = filieres
        return super().get_context_data(**kwargs)

