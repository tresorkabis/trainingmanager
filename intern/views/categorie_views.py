from django.views.generic import ListView, DetailView

from intern.models import Categorie

class CategorieListView(ListView):
    context_object_name = "categorie_list"
    queryset = Categorie.objects.all()
    template_name = "intern/categories.html"

class CategorieDetailView(DetailView):
    model = Categorie
    template_name = "training/categorie.html"
