from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count # Import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView, DeleteView # Import UpdateView and DeleteView

from training.models import Filiere, Formation, Module
from progress.models import Formateur, Action as ProgressAction # Import Action from progress app


class FormationPermissionMixin:
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

    def get_formation_queryset(self):
        user = self.request.user
        queryset = Formation.objects.all()

        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            return queryset
        if user.profile and user.profile.name == "Chef de filière" and user.filiere:
            return queryset.filter(filiere=user.filiere)
        if user.profile and user.profile.name == "Chef de service" and user.service:
            return queryset.filter(filiere__service=user.service)
        return Formation.objects.none()

    def enforce_manage_permission(self): # Renommé pour être plus générique
        if not self.get_allowed_filieres().exists():
            raise PermissionDenied("Vous n'avez pas la permission de gérer les formations.")


@method_decorator(login_required, name="dispatch")
class FormationListView(FormationPermissionMixin, ListView):
    context_object_name = "formation_list"
    paginate_by = 4
    template_name = "training/formations.html"

    def get_queryset(self):
        self.enforce_manage_permission() # Vérifier la permission avant de construire le queryset
        queryset = self.get_formation_queryset().select_related("filiere", "filiere__service")

        # Annoter chaque formation avec le nombre de modules et d'actions
        queryset = queryset.annotate(
            modules_count=Count('modules', distinct=True),
            actions_count=Count('action', distinct=True) # 'action' est le related_name par défaut pour ForeignKey de Action vers Formation
        )
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["link"] = "formations"

        # Calcul des statistiques globales
        all_formations = self.get_queryset() # Utiliser le queryset annoté
        ctx['stats'] = {
            'total': all_formations.count(),
            'active': all_formations.filter(active=True).count(),
            'inactive': all_formations.filter(active=False).count(),
            'total_modules': all_formations.aggregate(total_modules=Count('modules', distinct=True))['total_modules'],
            'total_actions': all_formations.aggregate(total_actions=Count('action', distinct=True))['total_actions'],
        }
        return ctx


@method_decorator(login_required, name="dispatch")
class FormationDetailView(FormationPermissionMixin, DetailView):
    model = Formation
    template_name = "training/formation.html"

    def get_queryset(self):
        return self.get_formation_queryset().select_related("filiere", "filiere__service").prefetch_related("modules__formateur") # Précharger les formateurs des modules

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filieres"] = self.get_allowed_filieres()
        ctx["formateurs"] = Formateur.objects.all() # Passer les formateurs au contexte
        ctx["titre"] = "Voir"
        return ctx


@method_decorator(login_required, name="dispatch")
class FormationCreateView(FormationPermissionMixin, View):
    def get(self, request):
        self.enforce_manage_permission()
        ctx = {
            "filieres": self.get_allowed_filieres(),
            "formateurs": Formateur.objects.all(), # Passer les formateurs au contexte
            "titre": "Saisie d'une formation",
            "mode": "new",
        }
        return render(request, "training/formation.html", ctx)

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
            raise PermissionDenied("Vous ne pouvez pas rattacher cette formation à cette filière.")

        total_duree_heures = 0

        formation = Formation(
            nom=nom,
            duree=duree,
            filiere_id=filiere_id,
            cout=cout,
            frais_participation=frais_participation,
            frais_jury=frais_jury,
            frais_materiels=frais_materiels,
        )
        formation.save()

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
                formation=formation,
                titre=titre,
                description=description_module or None,
                duree_heures=duree_module,
                formateur_id=formateur_id if formateur_id else None,
                ordre=index,
            )
            total_duree_heures += duree_module

        formation.duree_heures = total_duree_heures
        formation.save(update_fields=['duree_heures'])

        return HttpResponseRedirect(reverse_lazy("formations"))


@method_decorator(login_required, name="dispatch")
class FormationUpdateView(FormationPermissionMixin, UpdateView):
    model = Formation
    template_name = "training/formation.html"
    fields = ["nom", "duree", "filiere", "cout", "frais_participation", "frais_jury", "frais_materiels"]
    success_url = reverse_lazy("formations")

    def get_queryset(self):
        return self.get_formation_queryset().select_related("filiere", "filiere__service").prefetch_related("modules__formateur")

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
            raise PermissionDenied("Vous ne pouvez pas rattacher cette formation à cette filière.")

        # Mettre à jour l'objet Formation
        formation = form.save(commit=False)
        
        # Gérer les modules
        module_titres = self.request.POST.getlist("module_titre[]")
        module_descriptions = self.request.POST.getlist("module_description[]")
        module_durees = self.request.POST.getlist("module_duree_heures[]")
        module_formateurs = self.request.POST.getlist("module_formateur[]")
        module_ids = self.request.POST.getlist("module_id[]") # Pour identifier les modules existants

        # Supprimer les modules qui ne sont plus dans le formulaire
        existing_module_ids = [int(mid) for mid in module_ids if mid.isdigit()]
        formation.modules.exclude(pk__in=existing_module_ids).delete()

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
                'formation': formation,
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

        formation.duree_heures = total_duree_heures
        formation.save() # Sauvegarder la formation avec la nouvelle duree_heures

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
class FormationDeleteView(FormationPermissionMixin, DeleteView):
    model = Formation
    template_name = "training/formation_confirm_delete.html" # Nouveau template
    success_url = reverse_lazy("formations")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre"] = "Supprimer"
        return ctx