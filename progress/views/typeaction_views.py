from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView

from progress.models import TypeAction

class TypeActionListView(ListView):
    context_object_name = "typeAction_list"
    queryset = TypeAction.objects.all()
    template_name = "progress/typeactions.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['link'] = "typeactions"
        return ctx

class TypeActionDetailView(DetailView):
    model = TypeAction
    template_name = "progress/typeaction.html"
    
class TypeActionCreateView(View):
    def get(self, request):
        typeaction =TypeAction.objects.all()
        ctx = {
            "typeaction":typeaction
        }
        return render(request, 'progress/typeaction.html', ctx)
    
    def post(self, request):
        description= request.POST['description']
        date_debut = request.POST['date_debut']
        date_fin= request.POST['date_fin']
        formation= request.POST['formation']
        
        typeaction= typeaction(
            description = description,
            date_debut = date_debut,
            date_fin= date_fin,
            formation = formation,
            
        )
        typeaction.save()

        return HttpResponseRedirect("/progress/typeaction")