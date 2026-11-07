"""
Inscripciones a cursos — Matías Nicolás Echeveste Cardozo
Modelos: cursos con cupo, estudiantes y sus inscripciones (confirmadas, en lista de espera o canceladas).
"""

from django.core.exceptions import ValidationError
from django.db import models

PESOS_CEDULA = (2, 9, 8, 7, 6, 3, 4)


def validar_cedula(valor: str) -> None:
    """Dígito de control de la cédula de identidad uruguaya (7 u 8 dígitos, sin puntos ni guion)."""
    if not valor.isdigit() or not 7 <= len(valor) <= 8:
        raise ValidationError("La cédula debe tener 7 u 8 dígitos, sin puntos ni guion.")
    digitos = [int(d) for d in valor.zfill(8)]
    suma = sum(d * p for d, p in zip(digitos[:7], PESOS_CEDULA, strict=True))
    if (10 - suma % 10) % 10 != digitos[7]:
        raise ValidationError("El dígito de control de la cédula no es correcto.")


class Curso(models.Model):
    class Modalidad(models.TextChoices):
        PRESENCIAL = "presencial", "Presencial"
        VIRTUAL = "virtual", "Virtual"
        HIBRIDA = "hibrida", "Híbrida"

    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    modalidad = models.CharField(max_length=12, choices=Modalidad.choices, default=Modalidad.PRESENCIAL)
    cupo = models.PositiveSmallIntegerField()
    inicio = models.DateField()
    fin = models.DateField()

    class Meta:
        ordering = ["inicio", "nombre"]
        constraints = [
            models.CheckConstraint(condition=models.Q(fin__gte=models.F("inicio")), name="curso_fin_posterior_al_inicio"),
            models.CheckConstraint(condition=models.Q(cupo__gt=0), name="curso_cupo_positivo"),
        ]

    def __str__(self) -> str:
        return self.nombre

    @property
    def total_confirmadas(self) -> int:
        return self.inscripciones.filter(estado=Inscripcion.Estado.CONFIRMADA).count()


class Estudiante(models.Model):
    cedula = models.CharField(max_length=8, unique=True, validators=[validar_cedula])
    nombre = models.CharField(max_length=120)
    correo = models.EmailField(unique=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.cedula})"


class Inscripcion(models.Model):
    class Estado(models.TextChoices):
        CONFIRMADA = "confirmada", "Confirmada"
        ESPERA = "espera", "En lista de espera"
        CANCELADA = "cancelada", "Cancelada"

    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="inscripciones")
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="inscripciones")
    estado = models.CharField(max_length=12, choices=Estado.choices)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creada", "id"]
        constraints = [
            # Un estudiante sólo puede tener una inscripción vigente por curso (las canceladas no cuentan).
            models.UniqueConstraint(
                fields=["curso", "estudiante"],
                condition=~models.Q(estado="cancelada"),
                name="inscripcion_vigente_unica",
            )
        ]

    def __str__(self) -> str:
        return f"{self.estudiante} → {self.curso} [{self.estado}]"
