from django.shortcuts import render
from django.views.generic import View

class FormationView(View):
    def get(self, request):
        ctx = {}
        return render(request, "training/formations.html", ctx)