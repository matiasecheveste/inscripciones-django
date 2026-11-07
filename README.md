# Inscripciones a cursos

API REST para que una institución educativa publique cursos y gestione inscripciones con **cupo**, **lista de
espera** y **promoción automática** cuando alguien cancela.

**Tecnologías:** Python 3.12, Django 5.2, Django REST Framework, PostgreSQL 16 (SQLite en desarrollo), gunicorn,
Docker y GitHub Actions.

## Qué demuestra

- **Reglas de negocio en una capa de servicios** (`cursos/servicios.py`), separadas de las vistas:
  - si hay cupo la inscripción queda confirmada; si no, en lista de espera;
  - al cancelar una confirmada se confirma a la primera persona en espera (orden de llegada);
  - no se permiten inscripciones duplicadas ni dos cursos presenciales con fechas superpuestas.
- **Concurrencia:** las operaciones corren en transacciones con `select_for_update`, de modo que dos
  inscripciones simultáneas no superan el cupo.
- **Integridad en la base de datos:** restricciones `CHECK`, y `UniqueConstraint` condicional (una sola
  inscripción vigente por estudiante y curso, pero se permite volver a inscribirse después de cancelar).
- **Validación de la cédula uruguaya** con dígito de control.
- **Consultas eficientes:** cupos ocupados y lista de espera calculados con `annotate(Count(..., filter=Q(...)))`,
  sin consultas N+1.
- **Permisos:** el catálogo es público; crear cursos, estudiantes e inscripciones requiere personal autorizado.
  Autenticación por token o sesión.
- **Configuración 12-factor** y endurecimiento para producción (`check --deploy` sin advertencias: HSTS, cookies
  seguras, redirección a HTTPS).
- **CI** con PostgreSQL real: Ruff, migraciones al día, `check --deploy` y pruebas.

## Rutas

| Método | Ruta | Acceso |
|---|---|---|
| GET | `/api/cursos/?modalidad=virtual&con_cupo=1` | público |
| POST/PUT/DELETE | `/api/cursos/` | personal |
| GET | `/api/cursos/{id}/inscriptos/` | personal |
| CRUD | `/api/estudiantes/` | personal |
| POST | `/api/inscripciones/` (`curso`, `estudiante`) | personal |
| POST | `/api/inscripciones/{id}/cancelar/` | personal |
| POST | `/api/token/` | obtiene un token |
| — | `/admin/` | panel de administración |

## Uso

```bash
python -m venv .venv && . .venv/bin/activate   # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DJANGO_DEBUG=1                          # en desarrollo usa SQLite
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
python manage.py test
```

En producción se configuran `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` y `POSTGRES_DB`, `POSTGRES_USER`,
`POSTGRES_PASSWORD`, `POSTGRES_HOST`.

```bash
docker build -t inscripciones .
docker run -p 8000:8000 -e DJANGO_SECRET_KEY=... -e DJANGO_ALLOWED_HOSTS=localhost -e DJANGO_SSL_REDIRECT=0 inscripciones
```

## Autoría

Desarrollado por **Matías Nicolás Echeveste Cardozo**. Licencia MIT.
