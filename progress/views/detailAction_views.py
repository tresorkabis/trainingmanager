from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView

from progress.models import DetailAction

class DetailActionListViews(ListView):
    context_object_name = "detailAction_list"
    queryset = DetailAction.objects.all()
    template_name = "progress/detailactions.html"

class DetailActionDetailView(DetailView):
    model = DetailAction
    template_name = "progress/detailaction.html"
class detailActionCreateView(View):
    def get(self, request):
        detailaction = DetailAction.objects.all()
        ctx = {
            "detailaction":detailaction
        }
        return render(request, 'progress/detailaction.html', ctx)
    
    def post(self, request):
        stagiaire= request.POST['statgiaire']
        action = request.POST['action']    
        detailaction= DetailAction(
        stagiaire = stagiaire, 
        action=action   
        )
        detailaction.save()

        return HttpResponseRedirect("/progress/action")