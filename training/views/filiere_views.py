from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from training.models import Filiere, Service

@method_decorator(login_required, name='dispatch')
class FiliereListView(ListView):
    context_object_name = "filiere_list"
    # queryset = Filiere.objects.all() # Le queryset sera défini dynamiquement
    paginate_by = 4
    template_name = "training/filieres.html"

    def get_queryset(self):
        user = self.request.user
        queryset = Filiere.objects.all()

        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            # Les superutilisateurs et les managers voient toutes les filières
            return queryset
        elif user.profile and user.profile.name == "Chef de filière" and user.filiere:
            # Un chef de filière voit seulement sa filière
            return queryset.filter(pk=user.filiere.pk)
        elif user.profile and user.profile.name == "Chef de service" and user.service:
            # Un chef de service voit les filières de son service
            return queryset.filter(service=user.service)

        # Par défaut, si l'utilisateur n'a pas de rôle spécifique ou n'est pas lié, il ne voit aucune filière
        return Filiere.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['link'] = "filieres"
        return ctx

@method_decorator(login_required, name='dispatch')
class FiliereDetailView(DetailView):
    model = Filiere
    template_name = "training/filiere.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['services'] = Service.objects.all()
        ctx['titre'] = "Voir"
        return ctx

@method_decorator(login_required, name='dispatch')
class FiliereCreateView(View):
    def get(self, request):
        services = Service.objects.all()
        ctx = {
            "services":services
        }
        return render(request, 'training/filiere.html', ctx)
    
    def post(self, request):
        nom = request.POST['nom']
        id_service = request.POST['service']

        filiere = Filiere(
            nom = nom,
            service_id = id_service
        )
        filiere.save()

        return HttpResponseRedirect("/training/filieres")