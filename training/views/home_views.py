from django.shortcuts import render
from django.views.generic import View

class HomeView(View):
    def get(self, request):
        ctx = {}
        return render(request, "home/index.html", ctx)