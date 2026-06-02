from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView, DeleteView

from training.models import Filiere, Formation, Module
from progress.models import Formateur
from training.forms import MetierForm, ModuleFormSet # Import des formulaires et formset


class MetierPermissionMixin:
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

    def get_metier_queryset(self):
        user = self.request.user
        queryset = Formation.objects.all()

        if user.is_superuser or (user.profile and user.profile.name == "Manager"):
            return queryset
        if user.profile and user.profile.name == "Chef de filière" and user.filiere:
            return queryset.filter(filiere=user.filiere)
        if user.profile and user.profile.name == "Chef de service" and user.service:
            return queryset.filter(filiere__service=user.service)
        return Formation.objects.none()

    def enforce_manage_permission(self):
        user = self.request.user
        if not (user.is_superuser or (user.profile and user.profile.name in ["Manager", "Chef de filière", "Chef de service"])):
            raise PermissionDenied("Vous n'avez pas la permission de gérer les métiers.")


@method_decorator(login_required, name="dispatch")
class MetierListView(MetierPermissionMixin, ListView):
    context_object_name = "metier_list"
    paginate_by = 4
    template_name = "training/formations.html"

    def get_queryset(self):
        self.enforce_manage_permission()
        queryset = self.get_metier_queryset().select_related("filiere", "filiere__service")

        queryset = queryset.annotate(
            modules_count=Count('modules', distinct=True),
            actions_count=Count('actions', distinct=True)
        )
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["link"] = "formations"

        all_metiers = self.get_queryset()
        ctx['stats'] = {
            'total': all_metiers.count(),
            'active': all_metiers.filter(active=True).count(),
            'inactive': all_metiers.filter(active=False).count(),
            'total_modules': all_metiers.aggregate(total_modules=Count('modules', distinct=True))['total_modules'],
            'total_actions': all_metiers.aggregate(total_actions=Count('actions', distinct=True))['total_actions'],
        }
        return ctx


@method_decorator(login_required, name="dispatch")
class MetierDetailView(MetierPermissionMixin, DetailView):
    model = Formation
    template_name = "training/formation.html"
    context_object_name = "object" # Utilise 'object' comme nom de contexte par défaut

    def get_queryset(self):
        return self.get_metier_queryset().select_related("filiere", "filiere__service").prefetch_related("modules__formateurs")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filieres"] = self.get_allowed_filieres()
        ctx["formateurs"] = Formateur.objects.all()
        ctx["titre"] = "Voir"
        ctx["mode"] = "view"
        ctx["link"] = "formations"
        return ctx


@method_decorator(login_required, name="dispatch")
class MetierCreateUpdateView(MetierPermissionMixin, View): # Vue unifiée pour créer et modifier
    template_name = "training/formation_form.html" # Nouveau template pour le formulaire

    def get(self, request, pk=None):
        self.enforce_manage_permission()
        metier = None
        if pk:
            metier = get_object_or_404(Formation, pk=pk)
            form = MetierForm(instance=metier)
            formset = ModuleFormSet(instance=metier)
            mode = "edit"
            titre = "Modifier une formation"
        else:
            form = MetierForm()
            formset = ModuleFormSet()
            mode = "new"
            titre = "Créer une formation"

        ctx = {
            "form": form,
            "formset": formset,
            "filieres": self.get_allowed_filieres(),
            "formateurs": Formateur.objects.all(), # Peut être utile pour le JS du formset
            "titre": titre,
            "mode": mode,
            "object": metier, # Passe l'objet métier s'il existe
        }
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        self.enforce_manage_permission()
        metier = None
        if pk:
            metier = get_object_or_404(Formation, pk=pk)
            form = MetierForm(request.POST, instance=metier)
            formset = ModuleFormSet(request.POST, instance=metier)
            mode = "edit"
            titre = "Modifier une formation"
        else:
            form = MetierForm(request.POST)
            formset = ModuleFormSet(request.POST)
            mode = "new"
            titre = "Créer une formation"

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                metier = form.save(commit=False)

                # Validation de la filière
                filiere_id = form.cleaned_data["filiere"].pk
                if not self.get_allowed_filieres().filter(pk=filiere_id).exists():
                    messages.error(request, "Vous n'avez pas la permission de rattacher cette formation à cette filière.")
                    return self.form_invalid(request, form, formset, metier, mode, titre)

                metier.save()
                formset.instance = metier # Assurez-vous que le formset est lié à l'instance du métier
                formset.save()

                # Recalculer duree_heures après la sauvegarde des modules
                total_duree_heures = sum(module.duree_heures for module in metier.modules.all())
                if metier.duree_heures != total_duree_heures:
                    metier.duree_heures = total_duree_heures
                    metier.save(update_fields=['duree_heures'])

            messages.success(request, f"La formation '{metier.nom}' a été {'mise à jour' if pk else 'créée'} avec succès.")
            return HttpResponseRedirect(reverse_lazy("formation", kwargs={'pk': metier.pk}))
        else:
            return self.form_invalid(request, form, formset, metier, mode, titre)

    def form_invalid(self, request, form, formset, metier, mode, titre):
        ctx = {
            "form": form,
            "formset": formset,
            "filieres": self.get_allowed_filieres(),
            "formateurs": Formateur.objects.all(),
            "titre": titre,
            "mode": mode,
            "object": metier,
            "form_errors": form.errors,
            "formset_errors": formset.errors, # Passer les erreurs du formset
        }
        return render(request, self.template_name, ctx, status=400)


@method_decorator(login_required, name="dispatch")
class MetierDeleteView(MetierPermissionMixin, DeleteView):
    model = Formation
    template_name = "training/formation_confirm_delete.html"
    success_url = reverse_lazy("formations")
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre"] = "Supprimer"
        return ctx

# La vue ModuleFormateursUpdateView n'est plus nécessaire car la gestion des formateurs
# se fait via le formset dans MetierCreateUpdateView.
# @method_decorator(login_required, name="dispatch")
# class ModuleFormateursUpdateView(MetierPermissionMixin, View):
#     """Vue pour mettre à jour uniquement les formateurs d'un module spécifique."""
#     def post(self, request, pk):
#         self.enforce_manage_permission()
#         module = get_object_or_404(Module, pk=pk)
        
#         allowed_metiers = self.get_metier_queryset()
#         if not allowed_metiers.filter(pk=module.metier.pk).exists():
#             raise PermissionDenied("Vous n'avez pas la permission de modifier ce module.")

#         formateur_ids = [fid for fid in request.POST.getlist('formateur_ids') if fid]
        
#         module.formateurs.set(formateur_ids)
        
#         messages.success(request, f"Les formateurs du module '{module.titre}' ont été mis à jour avec succès.")
        
#         return HttpResponseRedirect(reverse_lazy("metier", kwargs={'pk': module.metier.pk}))