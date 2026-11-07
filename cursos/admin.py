"""
Inscripciones a cursos — Matías Nicolás Echeveste Cardozo
Panel de administración.
"""

from django.contrib import admin

from .models import Curso, Estudiante, Inscripcion


class InscripcionEnLinea(admin.TabularInline):
    model = Inscripcion
    extra = 0
    readonly_fields = ["creada"]


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "modalidad", "inicio", "fin", "cupo"]
    list_filter = ["modalidad"]
    search_fields = ["nombre"]
    inlines = [InscripcionEnLinea]


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ["nombre", "cedula", "correo"]
    search_fields = ["nombre", "cedula", "correo"]


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ["estudiante", "curso", "estado", "creada"]
    list_filter = ["estado", "curso"]
