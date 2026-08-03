from django.shortcuts import render

def index(request):
    """Renderiza o painel principal de operações do CDC Core."""
    return render(request, 'dashboard/index.html')

def login_view(request):
    """Renderiza a página de login."""
    return render(request, 'account/login.html')
