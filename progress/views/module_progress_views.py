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
        context['formateurs'] = Formateur.objects.all().order_by('nom') # Changed from stagiaires
        context['actions'] = Action.objects.all().order_by('description') # Changed from modules
        context['modules'] = Module.objects.all().order_by('titre') # Keep modules for potential future filtering or display
        context['statut_choices'] = ModuleProgress.STATUT_CHOICES
        context['link'] = 'module_progressions'
        
        # Convert query params to int in the view
        try:
            context['selected_formateur_id'] = int(self.request.GET.get('formateur')) # Updated context key
        except (TypeError, ValueError):
            context['selected_formateur_id'] = None
            
        try:
            context['selected_action_id'] = int(self.request.GET.get('action')) # Updated context key
        except (TypeError, ValueError):
            context['selected_action_id'] = None

        context['selected_statut'] = self.request.GET.get('statut')
        
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
        initial['module_progress'] = get_object_or_404(ModuleProgress, pk=module_progress_pk)
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
        context['module_progress'] = get_object_or_404(ModuleProgress, pk=self.kwargs.get('module_progress_pk'))
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