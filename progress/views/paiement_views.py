from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView

from progress.models import Paiement
from progress.forms import PaiementForm

@method_decorator(login_required, name='dispatch')
class PaiementListView(ListView):
    model = Paiement
    template_name = 'progress/paiements.html'
    context_object_name = 'paiement_list'
    paginate_by = 10

    def get_queryset(self):
        # Optionnel: Filtrer les paiements par stagiaire si l'utilisateur est un stagiaire
        # ou par filière/service si l'utilisateur a un rôle spécifique
        queryset = super().get_queryset()
        # Exemple de filtre si l'utilisateur est un stagiaire et ne doit voir que ses paiements
        # if self.request.user.is_authenticated and hasattr(self.request.user, 'stagiaire'):
        #     queryset = queryset.filter(stagiaire=self.request.user.stagiaire)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'paiements' # Pour activer le lien dans le menu latéral
        context['titre'] = 'Liste des paiements'
        return context

@method_decorator(login_required, name='dispatch')
class PaiementCreateView(CreateView):
    model = Paiement
    form_class = PaiementForm
    template_name = 'progress/paiement_form.html'
    
    def get_success_url(self):
        return reverse_lazy('paiements') # Rediriger vers la liste des paiements après création

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'paiements'
        context['titre'] = 'Enregistrer un paiement'
        return context

@method_decorator(login_required, name='dispatch')
class PaiementDetailView(DetailView):
    model = Paiement
    template_name = 'progress/paiement_detail.html'
    context_object_name = 'paiement'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'paiements'
        context['titre'] = 'Détail du paiement'
        return context

@method_decorator(login_required, name='dispatch')
class PaiementUpdateView(UpdateView):
    model = Paiement
    form_class = PaiementForm
    template_name = 'progress/paiement_form.html'

    def get_success_url(self):
        return reverse_lazy('paiements') # Rediriger vers la liste des paiements après modification

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'paiements'
        context['titre'] = 'Modifier un paiement'
        return context

@method_decorator(login_required, name='dispatch')
class PaiementDeleteView(DeleteView):
    model = Paiement
    template_name = 'progress/paiement_confirm_delete.html'
    success_url = reverse_lazy('paiements')
    context_object_name = 'paiement'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'paiements'
        context['titre'] = 'Supprimer un paiement'
        return context