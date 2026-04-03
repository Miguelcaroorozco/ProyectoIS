from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def busqueda_avanzada(request):
    return render(request, 'busqueda_avanzada/busqueda-avanzada.html')
