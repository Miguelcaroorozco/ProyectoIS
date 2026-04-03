from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def actividades(request):
    return render(request, 'actividades/actividades/actividades.html')
