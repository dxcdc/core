from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages

User = get_user_model()

def landing_view(request):
    """Renderiza a Landing Page pública do CDC Core."""
    return render(request, 'landing.html')

@login_required(login_url='dashboard:login')
def index(request):
    """Renderiza o painel principal de operações do CDC Core (Protegido por login)."""
    return render(request, 'dashboard/index.html')

def login_view(request):
    """Processa a autenticação e renderiza a página de login."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        username_input = request.POST.get('login-email', '').strip()
        password_input = request.POST.get('login-password', '').strip()

        # Tenta autenticar diretamente pelo username
        user = authenticate(request, username=username_input, password=password_input)

        # Se falhou, tenta buscar se o input fornecido é um email registrado
        if user is None and '@' in username_input:
            try:
                user_obj = User.objects.get(email=username_input)
                user = authenticate(request, username=user_obj.username, password=password_input)
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            return redirect('dashboard:index')
        else:
            messages.error(request, 'Usuário/Email ou senha incorretos.')

    return render(request, 'account/login.html')

def logout_view(request):
    """Realiza o logout do usuário e redireciona para a Landing Page pública."""
    logout(request)
    return redirect('dashboard:landing')
