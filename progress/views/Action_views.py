from django.views.generic import ListView, DetailView

from progress.models import Action

class ActionListViews(ListView):
    context_object_name = "action_list"
    queryset = Action.objects.all()
    template_name = "progress/actions.html"

class ActionDetailViews(DetailView):
    model = Action
    template_name = "progress/action.html"