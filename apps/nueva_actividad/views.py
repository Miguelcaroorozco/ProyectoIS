from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.actividades.forms import ActividadForm


@login_required
def nueva_actividad(request):
    if request.method == 'POST':
        form = ActividadForm(request.POST)
        if form.is_valid():
            actividad = form.save(commit=False)
            actividad.creado_por = request.user
            actividad.save()
            messages.success(request, 'Actividad registrada correctamente.')
            return redirect('actividades')
    else:
        form = ActividadForm()

    return render(
        request,
        'nueva_actividad/nueva-actividad.html',
        {
            'form': form,
        },
    )
