from django.views.generic import ListView, DetailView

from intern.models import Categorie

class CategorieListView(ListView):
    context_object_name = "categorie_list"
    queryset = Categorie.objects.all()
    template_name = "intern/categorie.html"

class CategorieDetailView(DetailView):
    pass
