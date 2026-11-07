# Inscripciones a cursos — Matías Nicolás Echeveste Cardozo

import cursos.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Estudiante",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "cedula",
                    models.CharField(
                        max_length=8,
                        unique=True,
                        validators=[cursos.models.validar_cedula],
                    ),
                ),
                ("nombre", models.CharField(max_length=120)),
                ("correo", models.EmailField(max_length=254, unique=True)),
            ],
            options={
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="Curso",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nombre", models.CharField(max_length=120)),
                ("descripcion", models.TextField(blank=True)),
                (
                    "modalidad",
                    models.CharField(
                        choices=[
                            ("presencial", "Presencial"),
                            ("virtual", "Virtual"),
                            ("hibrida", "Híbrida"),
                        ],
                        default="presencial",
                        max_length=12,
                    ),
                ),
                ("cupo", models.PositiveSmallIntegerField()),
                ("inicio", models.DateField()),
                ("fin", models.DateField()),
            ],
            options={
                "ordering": ["inicio", "nombre"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("fin__gte", models.F("inicio"))),
                        name="curso_fin_posterior_al_inicio",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("cupo__gt", 0)), name="curso_cupo_positivo"
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Inscripcion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("confirmada", "Confirmada"),
                            ("espera", "En lista de espera"),
                            ("cancelada", "Cancelada"),
                        ],
                        max_length=12,
                    ),
                ),
                ("creada", models.DateTimeField(auto_now_add=True)),
                (
                    "curso",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inscripciones",
                        to="cursos.curso",
                    ),
                ),
                (
                    "estudiante",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inscripciones",
                        to="cursos.estudiante",
                    ),
                ),
            ],
            options={
                "ordering": ["creada", "id"],
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(("estado", "cancelada"), _negated=True),
                        fields=("curso", "estudiante"),
                        name="inscripcion_vigente_unica",
                    )
                ],
            },
        ),
    ]
