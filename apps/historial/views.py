from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def historial(request):
    return render(request, 'historial/historial.html')
