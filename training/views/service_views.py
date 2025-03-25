from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView

from training.models import Service


class ServiceListView(ListView):
    context_object_name = "service_list"
    queryset = Service.objects.all()
    paginate_by = 4
    template_name = "training/services.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['link'] = "services"
        return ctx

class ServiceDetailView(DetailView):
    model = Service
    template_name = "training/service.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['services'] = Service.objects.all()
        ctx['titre'] = "Voir"
        return ctx

class ServiceCreateView(View):
    def get(self, request):
        services = Service.objects.all()
        ctx = {
            "services":services
        }
        return render(request, 'training/service.html', ctx)
    
    def post(self, request):
        nom = request.POST['nom']

        service = Service(
            nom = nom,
        )
        service.save()

        return HttpResponseRedirect("/training/services")
