from django.shortcuts import render
from django.views.generic import ListView

from training.models import Formation

class FormationListView(ListView):
    context_object_name = "formation_list"
    queryset = Formation.objects.all()
    template_name = "training/formations.html"