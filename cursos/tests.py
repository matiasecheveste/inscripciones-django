"""
Inscripciones a cursos — Matías Nicolás Echeveste Cardozo
Pruebas de modelos, reglas de inscripción y API.
"""

from datetime import date

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APITestCase

from . import servicios
from .models import Curso, Estudiante, Inscripcion, validar_cedula


def curso(**extra) -> Curso:
    datos = {"nombre": "Python inicial", "cupo": 2, "inicio": date(2026, 3, 2), "fin": date(2026, 4, 30)}
    return Curso.objects.create(**{**datos, **extra})


def estudiante(n: int) -> Estudiante:
    cedulas = ["12345672", "11111111", "22222222", "33333333"]
    return Estudiante.objects.create(cedula=cedulas[n], nombre=f"Estudiante {n}", correo=f"e{n}@ejemplo.uy")


class CedulaTests(TestCase):
    def test_valida_digito_de_control(self):
        validar_cedula("12345672")
        validar_cedula("11111111")
        for invalida in ["12345670", "1.234.567-2", "123"]:
            with self.assertRaises(ValidationError):
                validar_cedula(invalida)


class ReglasTests(TestCase):
    def test_cupo_lista_de_espera_y_promocion(self):
        c = curso(cupo=2)
        a, b, x = estudiante(0), estudiante(1), estudiante(2)
        primera = servicios.inscribir(c.pk, a)
        servicios.inscribir(c.pk, b)
        en_espera = servicios.inscribir(c.pk, x)
        self.assertEqual(primera.estado, Inscripcion.Estado.CONFIRMADA)
        self.assertEqual(en_espera.estado, Inscripcion.Estado.ESPERA)

        _, promovida = servicios.cancelar(primera.pk)
        self.assertEqual(promovida.pk, en_espera.pk)
        self.assertEqual(c.total_confirmadas, 2)

    def test_cancelar_en_espera_no_promueve(self):
        c = curso(cupo=1)
        servicios.inscribir(c.pk, estudiante(0))
        espera = servicios.inscribir(c.pk, estudiante(1))
        _, promovida = servicios.cancelar(espera.pk)
        self.assertIsNone(promovida)
        with self.assertRaises(servicios.ReglaIncumplida):
            servicios.cancelar(espera.pk)

    def test_impide_inscripcion_duplicada_pero_permite_reinscribir_tras_cancelar(self):
        c, e = curso(), estudiante(0)
        i = servicios.inscribir(c.pk, e)
        with self.assertRaises(servicios.ReglaIncumplida):
            servicios.inscribir(c.pk, e)
        servicios.cancelar(i.pk)
        self.assertEqual(servicios.inscribir(c.pk, e).estado, Inscripcion.Estado.CONFIRMADA)

    def test_impide_cursos_presenciales_superpuestos(self):
        e = estudiante(0)
        servicios.inscribir(curso().pk, e)
        otro = curso(nombre="Redes", inicio=date(2026, 4, 1), fin=date(2026, 5, 30))
        with self.assertRaises(servicios.ReglaIncumplida):
            servicios.inscribir(otro.pk, e)
        virtual = curso(nombre="SQL", modalidad=Curso.Modalidad.VIRTUAL)
        self.assertEqual(servicios.inscribir(virtual.pk, e).estado, Inscripcion.Estado.CONFIRMADA)


class ApiTests(APITestCase):
    def setUp(self):
        self.personal = User.objects.create_user("bedelia", password="clave-segura-123", is_staff=True)

    def test_catalogo_publico_y_escritura_restringida(self):
        curso()
        r = self.client.get("/api/cursos/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["results"][0]["lugares_libres"], 2)
        nuevo = {"nombre": "Java", "cupo": 10, "inicio": "2026-05-01", "fin": "2026-06-01", "modalidad": "virtual"}
        self.assertEqual(self.client.post("/api/cursos/", nuevo).status_code, 401)
        self.client.force_authenticate(User.objects.create_user("estudiante", password="otra-clave-456"))
        self.assertEqual(self.client.post("/api/cursos/", nuevo).status_code, 403)
        self.client.force_authenticate(self.personal)
        self.assertEqual(self.client.post("/api/cursos/", nuevo).status_code, 201)
        self.assertEqual(self.client.get("/api/cursos/?modalidad=virtual").data["count"], 1)

    def test_valida_fechas_del_curso(self):
        self.client.force_authenticate(self.personal)
        r = self.client.post("/api/cursos/", {"nombre": "X", "cupo": 1, "inicio": "2026-05-01", "fin": "2026-04-01"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("fin", r.data)

    def test_flujo_de_inscripcion_por_api(self):
        self.client.force_authenticate(self.personal)
        c = curso(cupo=1)
        a, b = estudiante(0), estudiante(1)
        r1 = self.client.post("/api/inscripciones/", {"curso": c.pk, "estudiante": a.pk})
        r2 = self.client.post("/api/inscripciones/", {"curso": c.pk, "estudiante": b.pk})
        self.assertEqual((r1.data["estado"], r2.data["estado"]), ("confirmada", "espera"))
        self.assertEqual(self.client.post("/api/inscripciones/", {"curso": c.pk, "estudiante": a.pk}).status_code, 400)

        r = self.client.post(f"/api/inscripciones/{r1.data['id']}/cancelar/")
        self.assertEqual(r.data["promovida"]["id"], r2.data["id"])
        self.assertEqual(self.client.post(f"/api/inscripciones/{r1.data['id']}/cancelar/").status_code, 409)
        inscriptos = self.client.get(f"/api/cursos/{c.pk}/inscriptos/").data
        self.assertEqual([i["estado"] for i in inscriptos], ["cancelada", "confirmada"])

    def test_rechaza_cedula_invalida(self):
        self.client.force_authenticate(self.personal)
        r = self.client.post("/api/estudiantes/", {"cedula": "12345670", "nombre": "Ana", "correo": "ana@ejemplo.uy"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("cedula", r.data)

    def test_token(self):
        r = self.client.post("/api/token/", {"username": "bedelia", "password": "clave-segura-123"})
        self.assertIn("token", r.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {r.data['token']}")
        self.assertEqual(self.client.get("/api/estudiantes/").status_code, 200)
