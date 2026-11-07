"""
Inscripciones a cursos — Matías Nicolás Echeveste Cardozo
Serializadores de Django REST Framework.
"""

from rest_framework import serializers

from .models import Curso, Estudiante, Inscripcion


class CursoSerializer(serializers.ModelSerializer):
    confirmadas = serializers.IntegerField(read_only=True)
    en_espera = serializers.IntegerField(read_only=True)
    lugares_libres = serializers.SerializerMethodField()

    class Meta:
        model = Curso
        fields = [
            "id", "nombre", "descripcion", "modalidad", "cupo", "inicio", "fin",
            "confirmadas", "en_espera", "lugares_libres",
        ]

    def get_lugares_libres(self, curso: Curso) -> int:
        return max(0, curso.cupo - getattr(curso, "confirmadas", 0))

    def validate(self, datos):
        inicio = datos.get("inicio", getattr(self.instance, "inicio", None))
        fin = datos.get("fin", getattr(self.instance, "fin", None))
        if inicio and fin and fin < inicio:
            raise serializers.ValidationError({"fin": "La fecha de fin debe ser posterior al inicio."})
        return datos


class EstudianteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estudiante
        fields = ["id", "cedula", "nombre", "correo"]


class InscripcionSerializer(serializers.ModelSerializer):
    curso_nombre = serializers.CharField(source="curso.nombre", read_only=True)
    estudiante_nombre = serializers.CharField(source="estudiante.nombre", read_only=True)

    class Meta:
        model = Inscripcion
        fields = ["id", "curso", "curso_nombre", "estudiante", "estudiante_nombre", "estado", "creada"]
        read_only_fields = ["estado", "creada"]
