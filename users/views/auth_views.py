from django.contrib.auth import login,authenticate,logout
from django.shortcuts import redirect, render
from django.views import View


class LoginPageView(View):
    template_name = 'home/login.html'
    #form_class = forms.LoginForm

    def get(self, request):
        message = ''
        return render(request, self.template_name, context={'message': message})
        
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(
            username=username,
            password=password,
        )
        if user is not None:
            login(request, user)
            return redirect('/')
        message = 'Identifiants invalides.'
        return render(request, self.template_name, context={'message': message})
    

class LogoutPageView(View):

    def get(self, request):
        logout(request)
        return redirect('login')