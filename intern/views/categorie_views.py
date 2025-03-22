from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView

from intern.models import Categorie

class CategorieListView(ListView):
    context_object_name = "categorie_list"
    queryset = Categorie.objects.all()
    template_name = "intern/categories.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['link'] = "categories"
        return ctx

class CategorieDetailView(DetailView):
    model = Categorie
    template_name = "training/categorie.html"

class CategorieCreateView(View):
    def get(self, request):
        categories = Categorie.objects.all()
        ctx = {
            "categories":categories
        }
        return render(request, 'intern/categorie.html', ctx)
    
    def post(self, request):
        titre = request.POST['titre']

        categories = Categorie(
            titre = titre,
        )
        categories.save()

        return HttpResponseRedirect("/intern/categories")
