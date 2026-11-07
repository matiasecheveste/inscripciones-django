"""
Inscripciones a cursos — Matías Nicolás Echeveste Cardozo
Reglas de inscripción en transacciones con bloqueo de fila para evitar sobrecupos con solicitudes simultáneas.
"""

from django.db import transaction

from .models import Curso, Estudiante, Inscripcion


class ReglaIncumplida(Exception):
    pass


@transaction.atomic
def inscribir(curso_id: int, estudiante: Estudiante) -> Inscripcion:
    # select_for_update serializa las inscripciones al mismo curso en PostgreSQL.
    curso = Curso.objects.select_for_update().get(pk=curso_id)
    vigentes = curso.inscripciones.exclude(estado=Inscripcion.Estado.CANCELADA)
    if vigentes.filter(estudiante=estudiante).exists():
        raise ReglaIncumplida("El estudiante ya está inscripto en este curso.")
    superpuestos = (
        Inscripcion.objects.filter(estudiante=estudiante, estado=Inscripcion.Estado.CONFIRMADA)
        .filter(curso__inicio__lte=curso.fin, curso__fin__gte=curso.inicio, curso__modalidad=Curso.Modalidad.PRESENCIAL)
        .exclude(curso=curso)
    )
    if curso.modalidad == Curso.Modalidad.PRESENCIAL and superpuestos.exists():
        raise ReglaIncumplida("El estudiante ya cursa otro curso presencial en esas fechas.")
    hay_cupo = vigentes.filter(estado=Inscripcion.Estado.CONFIRMADA).count() < curso.cupo
    estado = Inscripcion.Estado.CONFIRMADA if hay_cupo else Inscripcion.Estado.ESPERA
    return Inscripcion.objects.create(curso=curso, estudiante=estudiante, estado=estado)


@transaction.atomic
def cancelar(inscripcion_id: int) -> tuple[Inscripcion, Inscripcion | None]:
    """Cancela una inscripción y, si liberó un lugar, confirma a la primera persona en lista de espera."""
    inscripcion = Inscripcion.objects.select_for_update().select_related("curso").get(pk=inscripcion_id)
    if inscripcion.estado == Inscripcion.Estado.CANCELADA:
        raise ReglaIncumplida("La inscripción ya estaba cancelada.")
    Curso.objects.select_for_update().get(pk=inscripcion.curso_id)
    liberaba_lugar = inscripcion.estado == Inscripcion.Estado.CONFIRMADA
    inscripcion.estado = Inscripcion.Estado.CANCELADA
    inscripcion.save(update_fields=["estado"])

    promovida = None
    if liberaba_lugar:
        promovida = (
            Inscripcion.objects.select_for_update()
            .filter(curso_id=inscripcion.curso_id, estado=Inscripcion.Estado.ESPERA)
            .order_by("creada", "id")
            .first()
        )
        if promovida:
            promovida.estado = Inscripcion.Estado.CONFIRMADA
            promovida.save(update_fields=["estado"])
    return inscripcion, promovida
