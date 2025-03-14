from django.views.generic import ListView, DetailView

from progress.models import TypeAction

class TypeActionListView(ListView):
    context_object_name = "typeAction_list"
    queryset = TypeAction.objects.all()
    template_name = "progress/typeactions.html"

class TypeActionDetailView(DetailView):
    model = TypeAction
    template_name = "progress/typeaction.html"