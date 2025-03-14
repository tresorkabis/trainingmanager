from django.views.generic import ListView, DetailView

from progress.models import DetailAction

class DetailActionListViews(ListView):
    context_object_name = "detailAction_list"
    queryset = DetailAction.objects.all()
    template_name = "progress/detailactions.html"

class DetailActionDetailView(DetailView):
    model = DetailAction
    template_name = "progress/detailaction.html"