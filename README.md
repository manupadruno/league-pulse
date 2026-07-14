# league-pulse

Pipeline de datos que extrae, procesa y modela información de competiciones de fútbol
a partir de la API pública de [football-data.org](https://www.football-data.org/), con el
objetivo de construir la evolución de la clasificación de una liga a lo largo de una
temporada (snapshot por jornada).

Proyecto personal de aprendizaje orientado a Data Engineering: pipeline batch de extremo
a extremo, con foco en buenas prácticas de ingeniería (arquitectura por capas,
configuración centralizada, control de versiones, calidad de datos) más que en la
complejidad del dominio.

## Objetivo funcional

Dada una competición y temporada, reconstruir y consultar cómo evolucionó la
clasificación jornada a jornada, a partir de los resultados de los partidos.

## Arquitectura

Pipeline batch con arquitectura por capas (medallion-style):

- **Raw**: respuestas crudas de la API, guardadas tal cual en disco (JSON), sin transformar.
- **Silver/Gold** _(próximas fases)_: datos limpios, validados y cargados en PostgreSQL,
  listos para análisis.

## Modelo de datos

**Entidades base (persistentes)**
| Tabla | Descripción |
|---|---|
| `competiciones` | id, nombre, país, código (ej. `PD` = LaLiga) |
| `temporadas` | id, competicion_id, año, fecha_inicio, fecha_fin |
| `equipos` | id, nombre, país, escudo |
| `jugadores` | id, nombre, fecha_nacimiento, nacionalidad |

**Hechos**
| Tabla | Descripción |
|---|---|
| `partidos` | id, temporada_id, equipo_local_id, equipo_visitante_id, fecha, estado, goles_local, goles_visitante |
| `scorers` | id, jugador_id, temporada_id, equipo_id, goles, asistencias, penaltis (N:1 con jugador) |

**Snapshot periódico (derivado)**
| Tabla | Descripción |
|---|---|
| `clasificacion_jornada` | temporada_id, jornada, equipo_id, puntos, victorias, empates, derrotas, gf, gc, posición |

Relaciones clave: `competiciones 1—N temporadas`, `temporadas 1—N partidos`,
`equipos` referenciado dos veces desde `partidos` (local/visitante, en vez de tabla
puente, ver decisiones de diseño).

## Stack técnico

- **Python 3** con **uv** para gestión de dependencias y entorno.
- **requests** para el cliente HTTP.
- **PostgreSQL** _(próxima fase)_ para las capas silver/gold.
- **Docker / Airflow / AWS** _(fases posteriores)_.

## Decisiones de diseño (con motivo)

- **uv en vez de pip/venv**: lockfile determinista y gestión de dependencias más rápida
  y moderna; estándar cada vez más adoptado en 2026.
- **Capa raw en JSON, no en PostgreSQL**: la respuesta de la API es semi-estructurada y
  puede cambiar de forma. JSON es schema-on-read: tolera cambios de esquema sin romper
  el pipeline. Postgres impondría schema-on-write y fallaría o ignoraría campos nuevos.
- **`equipo_local_id` / `equipo_visitante_id` como dos FK en `partidos`, en vez de tabla
  puente**: la relación es siempre exactamente 2 (nunca variable), así que una tabla
  puente añadiría complejidad (habría que guardar además si es local o visitante) sin
  aportar nada que dos columnas no resuelvan directamente.
- **`competiciones` y `temporadas` separadas**: tienen ciclos de vida distintos (la
  competición es estable, la temporada cambia cada año) — mismo principio de slowly
  changing dimensions aplicado a jugadores/clubes.
- **`data/` fuera de git**: por privacidad, por peso del repositorio, y porque git no
  está diseñado para versionar datos que cambian constantemente.

## Estado actual

- [x] Modelado de entidades y relaciones.
- [x] Entorno del proyecto (uv, estructura de carpetas, `.env`).
- [x] `config.py` con carga de variables y fail-fast.
- [ ] Extracción de datos (`extract.py`).
- [ ] Persistencia de la capa raw (`raw.py`).
- [ ] Transformación y carga a PostgreSQL.
- [ ] Orquestación con Airflow.
- [ ] Despliegue en AWS.

## Cómo ejecutarlo

```bash
git clone <repo-url>
cd league-pulse
uv sync
cp .env.example .env  # rellenar con tu token de football-data.org
```
