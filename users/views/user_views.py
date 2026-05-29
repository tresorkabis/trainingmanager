from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView

from users.models import User
from users.forms import CustomUserCreationForm, CustomUserChangeForm

@method_decorator(login_required, name='dispatch')
class UserListView(ListView):
    model = User
    template_name = 'users/users.html'
    context_object_name = 'user_list'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'users' # Pour activer le lien dans le menu latéral
        context['titre'] = 'Liste des utilisateurs'
        return context

@method_decorator(login_required, name='dispatch')
class UserCreateView(CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'users/user_form.html'
    
    def get_success_url(self):
        return reverse_lazy('users') # Rediriger vers la liste des utilisateurs après création

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'users'
        context['titre'] = 'Créer un utilisateur'
        return context

@method_decorator(login_required, name='dispatch')
class UserDetailView(DetailView):
    model = User
    template_name = 'users/user_detail.html'
    context_object_name = 'user_object' # Renommé pour éviter conflit avec request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'users'
        context['titre'] = 'Détail de l\'utilisateur'
        return context

@method_decorator(login_required, name='dispatch')
class UserUpdateView(UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'users/user_form.html'

    def get_success_url(self):
        return reverse_lazy('users') # Rediriger vers la liste des utilisateurs après modification

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'users'
        context['titre'] = 'Modifier un utilisateur'
        return context

@method_decorator(login_required, name='dispatch')
class UserDeleteView(DeleteView):
    model = User
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('users')
    context_object_name = 'user_object' # Renommé pour éviter conflit avec request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link'] = 'users'
        context['titre'] = 'Supprimer un utilisateur'
        return context