from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView

from training.models import Formation

class FormationListView(ListView):
    context_object_name = "formation_list"
    queryset = Formation.objects.all()
    template_name = "training/formations.html"

class FormationDetailView(DetailView):
    model = Formation
    template_name = "training/formation.html"


class FormationCreateView(View):
    def get(self, request):
        return render(request, 'training/formation.html')
    
    def post(self, request):
        return HttpResponseRedirect("/formations")