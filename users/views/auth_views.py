from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.views import View

from users.forms import CustomAuthenticationForm


class LoginPageView(View):
    template_name = 'home/login.html'
    form_class = CustomAuthenticationForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('home')

        form = self.form_class(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', '/')
            return redirect(next_url)

        return render(request, self.template_name, {'form': form})


class LogoutPageView(View):

    def get(self, request):
        logout(request)
        return redirect('login')