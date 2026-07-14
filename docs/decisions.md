## 2026-07-14 — Propagar los bugs de programación

**Decisión**: los bugs de programación deben propagarse y parar la ejecución, no esconderse detrás de un print o ser capturados en un bloque try catch

**Por qué**: queremos enterarnos si la ejecución de uno de nuestros pipeline falla por un error en nuestro código. La forma más rapida de detectar estos errores es propagarlos en el código y que se pare la ejecucción.

---

## 2026-07-14 — Aislamiento de try/except por operación

**Decisión**: separar el manejo de errores de `fetch_competition` y `fetch_matches`
en bloques try/except independientes, en vez de uno solo envolviendo ambos.

**Por qué**: son operaciones que fallan de forma independiente (una competición
puede tener datos válidos aunque una temporada concreta de matches falle, y
viceversa). Un único try/except habría abortado combinaciones que sí eran
válidas por culpa de un fallo no relacionado.

---

## 2026-07-14 — Timestamps en UTC

**Decisión**: usar `datetime.now(timezone.utc)` en vez de `datetime.now()` para
los timestamps de la capa raw.

**Por qué**: el pipeline eventualmente correrá en un servidor cloud (probablemente
UTC por defecto), y comparar timestamps generados en local (hora de Madrid, con
cambio de horario de verano/invierno) contra timestamps del servidor introduciría
desfases inconsistentes.

---

## 2026-07-14 — Naming de la capa raw: timestamp antes que dominio

**Decisión**: `data/raw/{entity}/{timestamp}_{identifier}.json`, no
`{identifier}_{timestamp}.json`.

**Por qué**: en la capa raw lo relevante es el linaje de extracción (cuándo se
obtuvo cada dato, para poder auditar y depurar el propio pipeline). En capas
silver/gold el criterio cambia a agrupar por dominio (competición/temporada),
que es como se consulta para análisis.

---

## 2026-07-13 — Usar uv para la gestion de enviroments y paquetes

**Decisión**: usar `uv` en vez de `pip + venv`.

**Por qué**: Lockfile determinista, más rápido, estándar emergente en 2026 y una nueva herramienta para aprender.

---

## 2026-07-13 — Usar requests como nuestra libreria HTTP

**Decisión**: usar `requests` en vez de `httpx`.

**Por qué**: Nuestro proyecto no va a requerir llamadas asincronas, asi que elegimos la libreria mas sencilla.

---

## 2026-07-13 — Separación de responsabilidades por módulo (extract / raw / main)

**Decisión**: dividir el pipeline en módulos con una única responsabilidad cada uno,
sin dependencias directas entre ellos: `extract.py` solo sabe hablar con la API
(construir la petición, autenticar, devolver el JSON), `raw.py` solo sabe persistir
un diccionario ya obtenido a disco, y ninguno de los dos importa ni llama al otro.
`main.py` es el único módulo que conoce a ambos y orquesta el flujo completo
(llama a `extract`, pasa el resultado a `raw`).

Dentro de `extract.py`, además, se usa `response.raise_for_status()` en vez de
comprobar `response.status_code` a mano: lanza una excepción específica y
reconocible (`requests.exceptions.HTTPError`) si la API devuelve un error, en vez
de una condición genérica que habría que replicar en cada función.

**Por qué**: cada módulo cambia por razones distintas y a ritmos distintos. Si
mañana cambio de fuente de datos (otra API de fútbol), el cambio debería quedar
contenido en `extract.py`, sin tocar cómo se guardan los datos. Si mañana cambio
de dónde guardo la capa raw (de disco local a S3, por ejemplo), el cambio debería
quedar contenido en `raw.py`, sin tocar cómo se extraen los datos.

Que `save_raw` reciba el diccionario ya obtenido como parámetro (en vez de llamar
internamente a `fetch_*`) es la pieza clave que hace esto real: permite testear
la persistencia con un diccionario de ejemplo escrito a mano, sin depender de una
llamada HTTP real cada vez, y permite reutilizar `save_raw` con datos que en el
futuro vengan de cualquier otra fuente.

---

## 2026-07-13 — Diseño de la capa raw

**Decisión**: la capa raw guarda una copia fiel y sin transformar de lo que
devuelve la API, con las siguientes reglas:

- Se guarda la respuesta **completa**, incluyendo metadatos como `resultSet`
  (conteo de partidos, jugados, fechas), no solo el array de `matches` que hoy
  parece ser "lo importante".
- Se guarda como **ficheros JSON en disco**, no en una tabla PostgreSQL.
- **No se filtra nada** en esta capa (por ejemplo, por `status = FINISHED`) — el
  filtrado es responsabilidad de `transform.py`.
- `season` es un parámetro **obligatorio** en `fetch_matches`, sin valor por
  defecto que dependa de "la temporada actual" de la API.
- Naming de fichero: `data/raw/{entity}/{timestamp}_{identifier}.json`, con el
  **timestamp primero**.
- El timestamp se genera en **UTC** (`datetime.now(timezone.utc)`), no en hora
  local.
- La carpeta `data/` está excluida de git.

**Por qué**: todas estas decisiones responden a la misma idea de fondo — la raw
es la fuente de verdad reproducible del pipeline, y su valor depende de ser una
copia exacta e íntegra de lo que existió en un momento dado, sin que nadie meta
opiniones de negocio en ella todavía.

- Guardar la respuesta completa evita tener que volver a pedir datos a la API
  (con su rate limit de 10 req/min) si dentro de un mes resulta que algo que hoy
  parecía prescindible (como `resultSet`) se vuelve útil, por ejemplo para
  validar que no falta ningún partido.
- JSON tolera cambios de forma en la API (schema-on-read): si mañana aparece o
  desaparece un campo, el fichero simplemente lo refleja. Una tabla Postgres con
  esquema fijo (schema-on-write) fallaría el insert o ignoraría el campo nuevo en
  silencio, perdiendo información sin avisar.
- No filtrar por `status` en la extracción mantiene la raw neutral: decidir qué
  partidos son "útiles" es una decisión de negocio, y pertenece a la capa de
  transformación, no a la de extracción.
- Obligar a `season` explícito evita que el mismo código, ejecutado en momentos
  distintos, devuelva datos distintos sin que el que lo llama lo haya pedido —
  necesario para poder reproducir el histórico de una temporada concreta.
- El timestamp primero en el nombre del fichero responde a cómo se consulta esta
  capa: en raw importa **cuándo se extrajo** cada dato (para auditar y depurar el
  propio pipeline), mientras que en capas posteriores (silver/gold) lo relevante
  pasa a ser el dominio (competición, temporada), que es como se consulta para
  análisis.
- UTC evita desfases de horario si el pipeline pasa de correr en local (hora de
  Madrid, con cambio de horario estacional) a correr en un servidor cloud
  (normalmente en UTC por defecto).
- `data/` fuera de git por tres razones: protección de datos, peso/coste del
  repositorio, y porque git no está pensado para versionar datos que cambian
  constantemente (cada commit duplicaría el historial completo).
