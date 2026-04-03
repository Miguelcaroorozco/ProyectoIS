from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def generador_ia(request):
    messages.info(request, 'El modulo de IA esta deshabilitado temporalmente.')
    return redirect('index')
