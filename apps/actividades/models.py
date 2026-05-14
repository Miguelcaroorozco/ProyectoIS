from django.conf import settings
from django.db import models


class Actividad(models.Model):
    MESES = [
        ('enero', 'Enero'),
        ('febrero', 'Febrero'),
        ('marzo', 'Marzo'),
        ('abril', 'Abril'),
        ('mayo', 'Mayo'),
        ('junio', 'Junio'),
        ('julio', 'Julio'),
        ('agosto', 'Agosto'),
        ('septiembre', 'Septiembre'),
        ('octubre', 'Octubre'),
        ('noviembre', 'Noviembre'),
        ('diciembre', 'Diciembre'),
    ]

    TIPOLOGIAS = [
        ('taller', 'Taller'),
        ('seminario', 'Seminario'),
        ('curso', 'Curso'),
        ('otro', 'Otro'),
    ]

    MODALIDADES = [
        ('presencial', 'Presencial'),
        ('virtual', 'Virtual'),
        ('mixta', 'Mixta'),
    ]

    mes = models.CharField(max_length=20, choices=MESES)
    periodo = models.CharField(max_length=20)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    tipologia = models.CharField(max_length=30, choices=TIPOLOGIAS)
    modalidad = models.CharField(max_length=20, choices=MODALIDADES)
    programa = models.CharField(max_length=120)

    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    objetivo = models.TextField(blank=True)

    numero_participantes = models.PositiveIntegerField(default=0)
    horas_dedicadas = models.PositiveIntegerField(default=0)

    recursos_utilizados = models.TextField(blank=True)
    resultados = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)

    creado_con_ia = models.BooleanField(default=False)

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actividades_creadas',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_inicio', '-id']

    def __str__(self):
        return f'{self.nombre} ({self.periodo})'
