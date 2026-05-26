from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from training.models import Filiere, Formation

@method_decorator(login_required, name='dispatch')
class FormationListView(ListView):
    context_object_name = "formation_list"
    # queryset = Formation.objects.all() # Le queryset sera défini dynamiquement
    paginate_by = 4
    template_name = "training/formations.html"

    def get_queryset(self):
        user = self.request.user
        queryset = Formation.objects.all()

        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            # Les superutilisateurs et les managers voient toutes les formations
            return queryset
        elif user.profile and user.profile.name == "Chef de filière" and user.filiere:
            # Un chef de filière voit les formations de sa filière
            return queryset.filter(filiere=user.filiere)
        elif user.profile and user.profile.name == "Chef de service" and user.service:
            # Un chef de service voit les formations des filières de son service
            return queryset.filter(filiere__service=user.service)

        # Par défaut, si l'utilisateur n'a pas de rôle spécifique ou n'est pas lié, il ne voit aucune formation
        return Formation.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['link'] = "formations"
        return ctx

@method_decorator(login_required, name='dispatch')
class FormationDetailView(DetailView):
    model = Formation
    template_name = "training/formation.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filieres'] = Filiere.objects.all()
        ctx['titre'] = "Voir"
        return ctx


@method_decorator(login_required, name='dispatch')
class FormationCreateView(View):
    def get(self, request):
        filieres = Filiere.objects.all()
        ctx = {
            "filieres":filieres,
            "titre" : "Saisie d'une formation",
            "mode" : "new"
        }
        return render(request, 'training/formation.html', ctx)
    
    def post(self, request):
        nom = request.POST['nom']
        duree = request.POST['duree']
        duree_heures = request.POST.get('duree_heures') or 0
        id_filiere = request.POST['filiere']
        cout = request.POST.get('cout') or 0

        # Correction et ajout des champs de frais
        frais_participation = request.POST.get('frais_participation') or 0
        frais_jury = request.POST.get('frais_jury') or 0
        frais_materiels = request.POST.get('frais_materiels') or 0 # Renommé et clé corrigée

        formation = Formation(
            nom = nom,
            duree = duree,
            duree_heures = duree_heures,
            filiere_id = id_filiere,
            cout = cout,
            frais_participation = frais_participation, # Ajouté
            frais_jury = frais_jury,                   # Ajouté
            frais_materiels = frais_materiels          # Corrigé
        )
        formation.save()

        return HttpResponseRedirect("/training/formations")