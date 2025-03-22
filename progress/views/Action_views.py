from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView

from progress.models import Action

class ActionListViews(ListView):
    context_object_name = "action_list"
    queryset = Action.objects.all()
    template_name = "progress/actions.html"

class ActionDetailViews(DetailView):
    model = Action
    template_name = "progress/actions.html"
class ActionCreateView(View):
    def get(self, request):
        action = Action.objects.all()
        ctx = {
            "action":action
        }
        return render(request, 'progress/actions.html', ctx)
    
    def post(self, request):
        description= request.POST['description']
        date_debut = request.POST['date_debut']
        date_fin= request.POST['date_fin']
        formation= request.POST['formation']
        
        action= Action(
            description = description,
            date_debut = date_debut,
            date_fin= date_fin,
            formation = formation,
            
        )
        action.save()

        return HttpResponseRedirect("/progress/action")