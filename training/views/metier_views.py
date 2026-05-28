from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count # Import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView, DeleteView # Import UpdateView and DeleteView

from training.models import Filiere, Metier, Module # Changé Formation à Metier
from progress.models import Formateur, Action as ProgressAction # Import Action from progress app


class MetierPermissionMixin: # Renommé de FormationPermissionMixin à MetierPermissionMixin
    def get_allowed_filieres(self):
        user = self.request.user
        queryset = Filiere.objects.all()

        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            return queryset
        if user.profile and user.profile.name == "Chef de filière" and user.filiere:
            return queryset.filter(pk=user.filiere.pk)
        if user.profile and user.profile.name == "Chef de service" and user.service:
            return queryset.filter(service=user.service)
        return Filiere.objects.none()

    def get_metier_queryset(self): # Renommé de get_formation_queryset à get_metier_queryset
        user = self.request.user
        queryset = Metier.objects.all() # Changé Formation à Metier

        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            return queryset
        if user.profile and user.profile.name == "Chef de filière" and user.filiere:
            return queryset.filter(filiere=user.filiere)
        if user.profile and user.profile.name == "Chef de service" and user.service:
            return queryset.filter(filiere__service=user.service)
        return Metier.objects.none() # Changé Formation à Metier

    def enforce_manage_permission(self):
        if not self.get_allowed_filieres().exists():
            raise PermissionDenied("Vous n'avez pas la permission de gérer les métiers.") # Changé formations à métiers


@method_decorator(login_required, name="dispatch")
class MetierListView(MetierPermissionMixin, ListView): # Renommé de FormationListView à MetierListView
    context_object_name = "metier_list" # Changé formation_list à metier_list
    paginate_by = 4
    template_name = "training/metiers.html" # Changé formations.html à metiers.html

    def get_queryset(self):
        self.enforce_manage_permission()
        queryset = self.get_metier_queryset().select_related("filiere", "filiere__service") # Changé get_formation_queryset à get_metier_queryset

        # Annoter chaque métier avec le nombre de modules et d'actions
        queryset = queryset.annotate(
            modules_count=Count('modules', distinct=True),
            actions_count=Count('actions', distinct=True) # CHANGÉ 'progressaction' à 'actions'
        )
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["link"] = "metiers" # Changé formations à metiers

        # Calcul des statistiques globales
        all_metiers = self.get_queryset() # Changé all_formations à all_metiers
        ctx['stats'] = {
            'total': all_metiers.count(),
            'active': all_metiers.filter(active=True).count(),
            'inactive': all_metiers.filter(active=False).count(),
            'total_modules': all_metiers.aggregate(total_modules=Count('modules', distinct=True))['total_modules'],
            'total_actions': all_metiers.aggregate(total_actions=Count('actions', distinct=True))['total_actions'], # CHANGÉ 'progressaction' à 'actions'
        }
        return ctx


@method_decorator(login_required, name="dispatch")
class MetierDetailView(MetierPermissionMixin, DetailView): # Renommé de FormationDetailView à MetierDetailView
    model = Metier # Changé Formation à Metier
    template_name = "training/metier.html" # Changé formation.html à metier.html

    def get_queryset(self):
        return self.get_metier_queryset().select_related("filiere", "filiere__service").prefetch_related("modules__formateur") # Changé get_formation_queryset à get_metier_queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filieres"] = self.get_allowed_filieres()
        ctx["formateurs"] = Formateur.objects.all()
        ctx["titre"] = "Voir"
        return ctx


@method_decorator(login_required, name="dispatch")
class MetierCreateView(MetierPermissionMixin, View): # Renommé de FormationCreateView à MetierCreateView
    def get(self, request):
        self.enforce_manage_permission()
        ctx = {
            "filieres": self.get_allowed_filieres(),
            "formateurs": Formateur.objects.all(),
            "titre": "Saisie d'un métier", # Changé formation à métier
            "mode": "new",
        }
        return render(request, "training/metier.html", ctx) # Changé formation.html à metier.html

    def post(self, request):
        self.enforce_manage_permission()

        nom = request.POST["nom"]
        duree = request.POST["duree"]
        filiere_id = request.POST["filiere"]
        cout = request.POST.get("cout") or 0
        frais_participation = request.POST.get("frais_participation") or 0
        frais_jury = request.POST.get("frais_jury") or 0
        frais_materiels = request.POST.get("frais_materiels") or 0

        if not self.get_allowed_filieres().filter(pk=filiere_id).exists():
            raise PermissionDenied("Vous ne pouvez pas rattacher ce métier à cette filière.") # Changé formation à métier

        total_duree_heures = 0

        metier = Metier( # Changé formation à metier
            nom=nom,
            duree=duree,
            filiere_id=filiere_id,
            cout=cout,
            frais_participation=frais_participation,
            frais_jury=frais_jury,
            frais_materiels=frais_materiels,
        )
        metier.save() # Changé formation.save() à metier.save()

        module_titres = request.POST.getlist("module_titre[]")
        module_descriptions = request.POST.getlist("module_description[]")
        module_durees = request.POST.getlist("module_duree_heures[]")
        module_formateurs = request.POST.getlist("module_formateur[]")

        for index, titre in enumerate(module_titres, start=1):
            titre = (titre or "").strip()
            if not titre:
                continue

            duree_module_str = module_durees[index - 1].strip() if index - 1 < len(module_durees) else "0"
            duree_module = int(duree_module_str) if duree_module_str.isdigit() else 0
            description_module = module_descriptions[index - 1].strip() if index - 1 < len(module_descriptions) else ""
            formateur_id = module_formateurs[index - 1].strip() if index - 1 < len(module_formateurs) else None

            Module.objects.create(
                metier=metier, # Changé formation à metier
                titre=titre,
                description=description_module or None,
                duree_heures=duree_module,
                formateur_id=formateur_id if formateur_id else None,
                ordre=index,
            )
            total_duree_heures += duree_module

        metier.duree_heures = total_duree_heures # Changé formation.duree_heures à metier.duree_heures
        metier.save(update_fields=['duree_heures']) # Changé formation.save() à metier.save()

        return HttpResponseRedirect(reverse_lazy("metiers")) # Changé formations à metiers


@method_decorator(login_required, name="dispatch")
class MetierUpdateView(MetierPermissionMixin, UpdateView): # Renommé de FormationUpdateView à MetierUpdateView
    model = Metier # Changé Formation à Metier
    template_name = "training/metier.html" # Changé formation.html à metier.html
    fields = ["nom", "duree", "filiere", "cout", "frais_participation", "frais_jury", "frais_materiels"]
    success_url = reverse_lazy("metiers") # Changé formations à metiers

    def get_queryset(self):
        return self.get_metier_queryset().select_related("filiere", "filiere__service").prefetch_related("modules__formateur") # Changé get_formation_queryset à get_metier_queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filieres"] = self.get_allowed_filieres()
        ctx["formateurs"] = Formateur.objects.all()
        ctx["titre"] = "Modifier"
        ctx["mode"] = "edit"
        
        # Récupérer les modules existants pour le formulaire
        ctx["existing_modules"] = self.object.modules.all().order_by('ordre')
        return ctx

    def form_valid(self, form):
        self.enforce_manage_permission()
        
        # Récupérer les données du formulaire
        nom = form.cleaned_data["nom"]
        duree = form.cleaned_data["duree"]
        filiere = form.cleaned_data["filiere"]
        cout = form.cleaned_data["cout"]
        frais_participation = form.cleaned_data["frais_participation"]
        frais_jury = form.cleaned_data["frais_jury"]
        frais_materiels = form.cleaned_data["frais_materiels"]

        # Validation de la filière
        if not self.get_allowed_filieres().filter(pk=filiere.pk).exists():
            raise PermissionDenied("Vous ne pouvez pas rattacher ce métier à cette filière.") # Changé formation à métier

        # Mettre à jour l'objet Metier
        metier = form.save(commit=False) # Changé formation à metier
        
        # Gérer les modules
        module_titres = self.request.POST.getlist("module_titre[]")
        module_descriptions = self.request.POST.getlist("module_description[]")
        module_durees = self.request.POST.getlist("module_duree_heures[]")
        module_formateurs = self.request.POST.getlist("module_formateur[]")
        module_ids = self.request.POST.getlist("module_id[]") # Pour identifier les modules existants

        # Supprimer les modules qui ne sont plus dans le formulaire
        existing_module_ids = [int(mid) for mid in module_ids if mid.isdigit()]
        metier.modules.exclude(pk__in=existing_module_ids).delete() # Changé formation.modules à metier.modules

        total_duree_heures = 0
        for index, titre in enumerate(module_titres, start=1):
            titre = (titre or "").strip()
            if not titre:
                continue

            duree_module_str = module_durees[index - 1].strip() if index - 1 < len(module_durees) else "0"
            duree_module = int(duree_module_str) if duree_module_str.isdigit() else 0
            description_module = module_descriptions[index - 1].strip() if index - 1 < len(module_descriptions) else ""
            formateur_id = module_formateurs[index - 1].strip() if index - 1 < len(module_formateurs) else None
            module_pk = module_ids[index - 1].strip() if index - 1 < len(module_ids) else None

            module_data = {
                'metier': metier, # Changé formation à metier
                'titre': titre,
                'description': description_module or None,
                'duree_heures': duree_module,
                'formateur_id': formateur_id if formateur_id else None,
                'ordre': index,
            }

            if module_pk and module_pk.isdigit(): # Module existant
                Module.objects.filter(pk=module_pk).update(**module_data)
            else: # Nouveau module
                Module.objects.create(**module_data)
            
            total_duree_heures += duree_module

        metier.duree_heures = total_duree_heures # Changé formation.duree_heures à metier.duree_heures
        metier.save() # Sauvegarder le métier avec la nouvelle duree_heures

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        # Repopuler le contexte avec les données soumises et les erreurs
        ctx = self.get_context_data(form=form)
        ctx["filieres"] = self.get_allowed_filieres()
        ctx["formateurs"] = Formateur.objects.all()
        ctx["titre"] = "Modifier"
        ctx["mode"] = "edit"
        ctx["submitted"] = self.request.POST # Pour repopuler les champs
        ctx["form_errors"] = form.errors # Passer les erreurs du formulaire
        
        # Pour les modules, nous devons reconstruire la liste à partir des données POST
        module_titres = self.request.POST.getlist("module_titre[]")
        module_descriptions = self.request.POST.getlist("module_description[]")
        module_durees = self.request.POST.getlist("module_duree_heures[]")
        module_formateurs = self.request.POST.getlist("module_formateur[]")
        module_ids = self.request.POST.getlist("module_id[]")

        reconstructed_modules = []
        for index, titre in enumerate(module_titres):
            if titre.strip():
                reconstructed_modules.append({
                    'id': module_ids[index] if index < len(module_ids) else '',
                    'titre': titre,
                    'description': module_descriptions[index] if index < len(module_descriptions) else '',
                    'duree_heures': module_durees[index] if index < len(module_durees) else '',
                    'formateur_id': module_formateurs[index] if index < len(module_formateurs) else '',
                })
        ctx["existing_modules"] = reconstructed_modules
        
        return render(self.request, self.template_name, ctx, status=400)


@method_decorator(login_required, name="dispatch")
class MetierDeleteView(MetierPermissionMixin, DeleteView): # Renommé de FormationDeleteView à MetierDeleteView
    model = Metier # Changé Formation à Metier
    template_name = "training/metier_confirm_delete.html" # Changé formation_confirm_delete.html à metier_confirm_delete.html
    success_url = reverse_lazy("metiers") # Changé formations à metiers

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre"] = "Supprimer"
        return ctx