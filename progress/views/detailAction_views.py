from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib import messages

from progress.models import DetailAction

class DetailActionListViews(ListView):
    context_object_name = "detailAction_list"
    queryset = DetailAction.objects.all()
    template_name = "progress/detailactions.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['link'] = "detailactions"
        return ctx

class DetailActionDetailView(DetailView):
    model = DetailAction
    template_name = "progress/detailaction.html"

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy

@method_decorator(login_required, name='dispatch')
class DetailActionCreateView(View):
    """Create a DetailAction (assign a stagiaire to an action).
    Accepts POST with 'stagiaire' and 'action' (ids). If provided via GET, a simple form can be shown (not used here).
    After creation, redirects to the stagiaire detail page.
    """
    def post(self, request):
        # Permission: only superuser, Manager or Conseiller can create inscriptions
        user = request.user
        allowed = False
        if user and user.is_authenticated:
            if user.is_superuser:
                allowed = True
            else:
                profile = getattr(user, 'profile', None)
                if profile and getattr(profile, 'name', None) in ['Manager', 'Conseiller']:
                    allowed = True
        if not allowed:
            messages.error(request, 'Vous n\'avez pas la permission d\'inscrire un stagiaire à une action.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse_lazy('detailactions')))

        stagiaire_id = request.POST.get('stagiaire') or request.GET.get('stagiaire')
        action_id = request.POST.get('action') or request.GET.get('action')
        next_url = request.POST.get('next') or request.GET.get('next')

        if not stagiaire_id or not action_id:
            # Bad request; redirect back
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse_lazy('detailactions')))

        from intern.models import Stagiaire
        from progress.models import Action

        stagiaire = get_object_or_404(Stagiaire, pk=stagiaire_id)
        action = get_object_or_404(Action, pk=action_id)

        # Avoid duplicate inscriptions
        obj, created = DetailAction.objects.get_or_create(
            stagiaire=stagiaire,
            action=action,
            defaults={'statut': 'Inscrit'}
        )

        if created:
            messages.success(
                request,
                f"{stagiaire.get_full_name()} a été inscrit à l'action '{action.description}'."
            )
        else:
            messages.info(
                request,
                f"{stagiaire.get_full_name()} est déjà inscrit à l'action '{action.description}'."
            )

        return HttpResponseRedirect(next_url or reverse_lazy('stagiaire', kwargs={'pk': stagiaire.pk}))
