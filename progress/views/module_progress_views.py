from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from progress.models import ModuleProgress, SessionProgress, Module, Formateur, Action # Removed DetailAction
from progress.forms import ModuleProgressForm, SessionProgressForm
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.views import View
from django.contrib import messages
from progress.services import ActionWorkflowService

class ModuleProgressListView(LoginRequiredMixin, ListView):
    model = ModuleProgress
    template_name = 'progress/module_progress_list.html'
    context_object_name = 'module_progressions'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related('formateur', 'action', 'module') # Updated select_related
        
        query = self.request.GET.get('q')
        formateur_id = self.request.GET.get('formateur') # Changed from stagiaire_id
        action_id = self.request.GET.get('action') # Changed from module_id
        statut = self.request.GET.get('statut')

        if query:
            queryset = queryset.filter(
                Q(formateur__nom__icontains=query) | # Updated Q object
                Q(formateur__postnom__icontains=query) | # Updated Q object
                Q(action__description__icontains=query) | # Updated Q object
                Q(module__titre__icontains=query) |
                Q(commentaires__icontains=query)
            )
        
        if formateur_id:
            try:
                formateur_id = int(formateur_id)
                queryset = queryset.filter(formateur_id=formateur_id) # Updated filter field
            except ValueError:
                pass # Ignore invalid integer conversion
        
        if action_id:
            try:
                action_id = int(action_id)
                queryset = queryset.filter(action_id=action_id) # Updated filter field
            except ValueError:
                pass # Ignore invalid integer conversion

        if statut:
            queryset = queryset.filter(statut_module=statut)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_progs = self.get_queryset()
        
        context['formateurs'] = Formateur.objects.all().order_by('nom')
        context['actions'] = Action.objects.all().order_by('description')
        context['modules'] = Module.objects.all().order_by('titre')
        context['statut_choices'] = ModuleProgress.STATUT_CHOICES
        context['link'] = 'module_progressions'
        
        # Hero Stats
        context['hero_stats'] = [
            {'label': 'Total Suivis', 'value': all_progs.count()},
            {'label': 'En cours', 'value': all_progs.filter(statut_module='EC').count()},
            {'label': 'Terminés', 'value': all_progs.filter(statut_module__in=['TE', 'VA']).count()},
            {'label': 'Non commencés', 'value': all_progs.filter(statut_module='NC').count()},
        ]

        # Convert query params to int in the view
        try:
            context['selected_formateur_id'] = int(self.request.GET.get('formateur'))
        except (TypeError, ValueError):
            context['selected_formateur_id'] = None
            
        try:
            context['selected_action_id'] = int(self.request.GET.get('action'))
        except (TypeError, ValueError):
            context['selected_action_id'] = None

        context['selected_statut'] = self.request.GET.get('statut')

        hero_actions = [
            {'label': 'Nouvelle progression', 'url': reverse_lazy('module_progress_create'), 'icon': 'bi bi-plus-circle'},
        ]

        selected_action_id = context.get('selected_action_id')
        if selected_action_id:
            hero_actions.append({
                'label': "Voir l'action",
                'url': reverse_lazy('action', kwargs={'pk': selected_action_id}),
                'icon': 'bi bi-eye',
                'class': 'btn-light-secondary',
            })

        context['hero_actions'] = hero_actions
        
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['query_params'] = query_params.urlencode()
        
        return context

class ModuleProgressDetailView(LoginRequiredMixin, DetailView):
    model = ModuleProgress
    template_name = 'progress/module_progress_detail.html'
    context_object_name = 'module_progress'

    def get_queryset(self):
        # Updated select_related for detail view
        return super().get_queryset().select_related('formateur', 'action', 'module')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sessions'] = self.object.sessions_progress.all()
        context['next_session_defaults'] = ActionWorkflowService.build_session_initial(self.object)
        context['subject_planning'] = self.object.get_subject_planning()
        context['hero_actions'] = [
            {'label': 'Retour à la liste', 'url': reverse_lazy('module_progressions'), 'icon': 'bi bi-arrow-left', 'class': 'btn-light-secondary'},
            {'label': 'Modifier', 'url': reverse_lazy('module_progress_update', kwargs={'pk': self.object.pk}), 'icon': 'bi bi-pencil'},
        ]

        # Calcul du volume horaire réalisé
        from django.db.models import Sum, F, ExpressionWrapper, DurationField
        import datetime
        
        # On calcule la durée totale des séances
        hours_done = 0
        hours_planned = 0
        
        for s in context['sessions']:
            if s.statut == 'REALISEE' and s.actual_start_time and s.actual_end_time:
                start = datetime.datetime.combine(datetime.date.today(), s.actual_start_time)
                end = datetime.datetime.combine(datetime.date.today(), s.actual_end_time)
                hours_done += (end - start).total_seconds() / 3600
            elif s.statut == 'PLANIFIEE' and s.planned_start_time and s.planned_end_time:
                start = datetime.datetime.combine(datetime.date.today(), s.planned_start_time)
                end = datetime.datetime.combine(datetime.date.today(), s.planned_end_time)
                hours_planned += (end - start).total_seconds() / 3600

        context['hours_done'] = round(hours_done, 1)
        context['hours_planned'] = round(hours_planned, 1)
        
        # On masque la planification si le cumul (fait + prévu) atteint le quota
        total_engaged = hours_done + hours_planned
        context['can_plan_more'] = total_engaged < self.object.module.duree_heures
        context['is_finished'] = hours_done >= self.object.module.duree_heures

        return context

class ModuleProgressCreateView(LoginRequiredMixin, CreateView):
    model = ModuleProgress
    form_class = ModuleProgressForm
    template_name = 'progress/module_progress_form.html'
    success_url = reverse_lazy('module_progressions')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Nouvelle Progression de Module"
        return context

class ModuleProgressUpdateView(LoginRequiredMixin, UpdateView):
    model = ModuleProgress
    form_class = ModuleProgressForm
    template_name = 'progress/module_progress_form.html'
    success_url = reverse_lazy('module_progressions')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Modifier Progression de Module"
        return context

class ModuleProgressDeleteView(LoginRequiredMixin, DeleteView):
    model = ModuleProgress
    template_name = 'progress/module_progress_confirm_delete.html'
    success_url = reverse_lazy('module_progressions')

class SessionProgressCreateView(LoginRequiredMixin, CreateView):
    model = SessionProgress
    form_class = SessionProgressForm
    template_name = 'progress/session_progress_form.html'

    def get_initial(self):
        initial = super().get_initial()
        module_progress_pk = self.kwargs.get('module_progress_pk')
        # module_progress now directly contains action and module
        module_progress = get_object_or_404(ModuleProgress, pk=module_progress_pk)
        initial['module_progress'] = module_progress
        initial.update(ActionWorkflowService.build_session_initial(module_progress))
        return initial

    def form_valid(self, form):
        module_progress_pk = self.kwargs.get('module_progress_pk')
        module_progress = get_object_or_404(ModuleProgress, pk=module_progress_pk)
        form.instance.module_progress = module_progress
        messages.success(self.request, "La séance a été ajoutée avec succès.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('module_progress_detail', kwargs={'pk': self.kwargs.get('module_progress_pk')})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Ajouter une Séance"
        module_progress = get_object_or_404(ModuleProgress, pk=self.kwargs.get('module_progress_pk'))
        context['module_progress'] = module_progress
        context['next_session_defaults'] = ActionWorkflowService.build_session_initial(module_progress)
        context['valid_dates'] = ActionWorkflowService.get_action_valid_dates(module_progress.action)
        
        # Passer les créneaux en JSON pour le JS
        schedules = []
        for s in module_progress.action.course_schedules.all():
            schedules.append({
                'day': s.jour_semaine,
                'start': s.heure_debut.strftime('%H:%M'),
                'end': s.heure_fin.strftime('%H:%M')
            })
        context['schedules_json'] = schedules
        return context

class SessionProgressUpdateView(LoginRequiredMixin, UpdateView):
    model = SessionProgress
    form_class = SessionProgressForm
    template_name = 'progress/session_progress_form.html'

    def form_valid(self, form):
        messages.success(self.request, "La séance a été mise à jour avec succès.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('module_progress_detail', kwargs={'pk': self.object.module_progress.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Modifier la Séance"
        context['module_progress'] = self.object.module_progress
        context['valid_dates'] = ActionWorkflowService.get_action_valid_dates(self.object.module_progress.action)
        
        # Passer les créneaux en JSON pour le JS
        schedules = []
        for s in self.object.module_progress.action.course_schedules.all():
            schedules.append({
                'day': s.jour_semaine,
                'start': s.heure_debut.strftime('%H:%M'),
                'end': s.heure_fin.strftime('%H:%M')
            })
        context['schedules_json'] = schedules
        return context

class SessionProgressDeleteView(LoginRequiredMixin, DeleteView):
    model = SessionProgress
    template_name = 'progress/session_progress_confirm_delete.html'

    def get_success_url(self):
        messages.success(self.request, "La séance a été supprimée avec succès.")
        return reverse_lazy('module_progress_detail', kwargs={'pk': self.object.module_progress.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module_progress'] = self.object.module_progress
        return context
