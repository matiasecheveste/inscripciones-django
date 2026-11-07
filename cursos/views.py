"""
Inscripciones a cursos — Matías Nicolás Echeveste Cardozo
Vistas de la API: catálogo público, administración restringida al personal e inscripciones con reglas de cupo.
"""

from django.db.models import Count, F, Q
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from . import servicios
from .models import Curso, Estudiante, Inscripcion
from .serializers import CursoSerializer, EstudianteSerializer, InscripcionSerializer


class SoloPersonalEscribe(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or bool(request.user and request.user.is_staff)


class CursoViewSet(viewsets.ModelViewSet):
    serializer_class = CursoSerializer
    permission_classes = [SoloPersonalEscribe]

    def get_queryset(self):
        cursos = Curso.objects.annotate(
            confirmadas=Count("inscripciones", filter=Q(inscripciones__estado=Inscripcion.Estado.CONFIRMADA)),
            en_espera=Count("inscripciones", filter=Q(inscripciones__estado=Inscripcion.Estado.ESPERA)),
        )
        modalidad = self.request.query_params.get("modalidad")
        if modalidad:
            cursos = cursos.filter(modalidad=modalidad)
        if self.request.query_params.get("con_cupo") == "1":
            cursos = cursos.filter(confirmadas__lt=F("cupo"))
        return cursos

    @action(detail=True, methods=["get"], permission_classes=[permissions.IsAdminUser])
    def inscriptos(self, request, pk=None):
        inscripciones = self.get_object().inscripciones.select_related("estudiante", "curso")
        return Response(InscripcionSerializer(inscripciones, many=True).data)


class EstudianteViewSet(viewsets.ModelViewSet):
    queryset = Estudiante.objects.all()
    serializer_class = EstudianteSerializer
    permission_classes = [permissions.IsAdminUser]


class InscripcionViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    serializer_class = InscripcionSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Inscripcion.objects.select_related("curso", "estudiante")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            inscripcion = servicios.inscribir(
                serializer.validated_data["curso"].pk, serializer.validated_data["estudiante"]
            )
        except servicios.ReglaIncumplida as error:
            raise ValidationError({"detail": str(error)}) from error
        return Response(self.get_serializer(inscripcion).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        try:
            cancelada, promovida = servicios.cancelar(self.get_object().pk)
        except servicios.ReglaIncumplida as error:
            return Response({"detail": str(error)}, status=status.HTTP_409_CONFLICT)
        return Response(
            {
                "cancelada": self.get_serializer(cancelada).data,
                "promovida": self.get_serializer(promovida).data if promovida else None,
            }
        )
