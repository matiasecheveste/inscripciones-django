"""
Inscripciones a cursos — Matías Nicolás Echeveste Cardozo
Rutas del proyecto.
"""

from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from cursos.views import CursoViewSet, EstudianteViewSet, InscripcionViewSet

rutas = DefaultRouter()
rutas.register("cursos", CursoViewSet, basename="curso")
rutas.register("estudiantes", EstudianteViewSet)
rutas.register("inscripciones", InscripcionViewSet, basename="inscripcion")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/token/", obtain_auth_token),
    path("api/", include(rutas.urls)),
]
