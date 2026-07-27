from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.db.models import Sum
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from datetime import date

from progress.models import Paiement
from progress.forms import PaiementForm

@method_decorator(login_required, name='dispatch')
class PaiementListView(ListView):
    model = Paiement
    template_name = 'progress/paiements.html'
    context_object_name = 'paiement_list'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related('stagiaire', 'action', 'action__formation').order_by('-date_paiement', '-id')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_paiements = self.get_queryset()
        today = date.today()
        
        # Stats
        total_recu = all_paiements.aggregate(total=Sum('montant'))['total'] or 0
        total_especes = all_paiements.filter(mode_paiement='ESPECES').aggregate(total=Sum('montant'))['total'] or 0
        total_virement = all_paiements.filter(mode_paiement='VIREMENT').aggregate(total=Sum('montant'))['total'] or 0
        total_mois = all_paiements.filter(date_paiement__month=today.month, date_paiement__year=today.year).aggregate(total=Sum('montant'))['total'] or 0

        context['hero_stats'] = [
            {'label': 'Total Encaissé', 'value': f"{total_recu:,.0f} USD"},
            {'label': 'Ce mois', 'value': f"{total_mois:,.0f} USD"},
            {'label': 'Espèces', 'value': f"{total_especes:,.0f} USD"},
            {'label': 'Virements', 'value': f"{total_virement:,.0f} USD"},
        ]

        context['hero_actions'] = [
            {'label': 'Nouveau paiement', 'url': reverse_lazy('paiement_create'), 'icon': 'bi bi-plus-circle', 'class': 'btn-primary'},
        ]

        context['link'] = 'paiements'
        context['titre'] = 'Liste des paiements'
        return context

@method_decorator(login_required, name='dispatch')
class PaiementCreateView(CreateView):
    model = Paiement
    form_class = PaiementForm
    template_name = 'progress/paiement_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        stagiaire_id = self.request.GET.get('stagiaire')
        if stagiaire_id:
            try:
                sid = int(stagiaire_id)
                initial['stagiaire'] = sid
                # Try to prefill the action based on stagiaire's latest DetailAction
                from progress.models import DetailAction
                latest = DetailAction.objects.filter(stagiaire_id=sid).order_by('-action__date_debut').select_related('action').first()
                if latest and latest.action_id:
                    initial['action'] = latest.action_id
            except ValueError:
                pass
        return initial

    def get_success_url(self):
        # Après création, rediriger vers la fiche du stagiaire si possible
        if hasattr(self, 'object') and self.object and self.object.stagiaire:
            return reverse_lazy('stagiaire', kwargs={'pk': self.object.stagiaire.pk})
        return reverse_lazy('paiements')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'paiements'
        context['titre'] = 'Enregistrer un paiement'
        # Pass information to template so we can render hidden inputs and display labels
        stagiaire_id = self.request.GET.get('stagiaire')
        if stagiaire_id:
            from intern.models import Stagiaire
            try:
                stagiaire_obj = Stagiaire.objects.get(pk=int(stagiaire_id))
                context['prefill_stagiaire'] = True
                context['stagiaire_obj'] = stagiaire_obj
            except Exception:
                context['prefill_stagiaire'] = False
        else:
            context['prefill_stagiaire'] = False

        # If initial has action set, pass it
        initial_action = self.get_initial().get('action')
        if initial_action:
            from progress.models import Action
            try:
                context['prefill_action'] = True
                context['action_obj'] = Action.objects.get(pk=initial_action)
            except Exception:
                context['prefill_action'] = False
        else:
            context['prefill_action'] = False

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
        context['total_cout'] = self.object.get_total_cout()
        context['total_paye'] = self.object.get_total_paye()
        context['solde_restant'] = self.object.get_solde_restant()
        
        mode_icon = 'bi bi-cash' if self.object.mode_paiement == 'ESPECES' else 'bi bi-bank' # Determine icon based on mode
        
        context['hero_stats'] = [
            {'label': 'Montant reçu', 'value': f"{self.object.montant:,.0f} USD"},
            {'label': 'Déjà payé', 'value': f"{context['total_paye']:,.0f} USD"},
            {'label': 'Solde restant', 'value': f"{context['solde_restant']:,.0f} USD"},
            {'label': 'Mode', 'value': self.object.get_mode_paiement_display()},
        ]
        
        context['hero_actions'] = [
            {'label': 'Retour à la liste', 'url': reverse_lazy('paiements'), 'icon': 'bi bi-arrow-left', 'class': 'btn-light-secondary'},
            {'label': 'Imprimer', 'url': reverse_lazy('paiement_print', kwargs={'pk': self.object.pk}), 'icon': 'bi bi-printer', 'class': 'btn-light-primary', 'target': '_blank'},
        ]
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
class PaiementReceiptPrintView(DetailView):
    model = Paiement
    template_name = 'progress/paiement_receipt_print.html'
    context_object_name = 'paiement'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_cout'] = self.object.get_total_cout()
        context['total_paye'] = self.object.get_total_paye()
        context['solde_restant'] = self.object.get_solde_restant()
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