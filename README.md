# DDTech API

DDTech API es una aplicacion en Python que evoluciono de un scraper ejecutable por consola a una **API REST basada en FastAPI**, preparada para ejecutarse localmente o desplegarse con Docker.

El proyecto conserva el scraper actual de **DDTech.mx**, mantiene SQLite como mecanismo de persistencia y expone el sistema mediante endpoints HTTP para consulta de catalogo, historial de precios, builds persistentes y ejecucion asincrona del scraper.

## Objetivo Del Proyecto

La API permite:

- consultar el catalogo de componentes almacenado en SQLite
- consultar historial de precios por componente
- administrar builds persistentes y sus slots
- registrar decisiones sobre componentes elegidos en una build
- generar snapshots de una build y comparar contra precios mas recientes
- ejecutar el scraper por HTTP sin bloquear la solicitud
- consultar el estado de jobs y del servicio

## Caracteristicas Principales

- API REST con FastAPI
- documentacion OpenAPI generada automaticamente
- Swagger UI y ReDoc
- health check para despliegues
- scraper de DDTech con Playwright y Chromium
- jobs asincronos en memoria para ejecucion de scraping
- persistencia SQLite mediante ruta configurable por variable de entorno
- estructura modular preparada para crecer hacia nuevas integraciones
- compatibilidad con Docker y despliegues donde el disco persistente se monte externamente

## Arquitectura Del Proyecto

```text
app/
  api/
    models/
    routers/
    schemas.py
    app.py
    dependencies.py
  database/
  enrichers/
  jobs/
  scraper/
  services/
  config.py
  logging.py
scraper/
utils/
http/
data/
database.py
main.py
serve.py
Dockerfile
docker-compose.yml
requirements.txt
```

## Modulos Relevantes

- `app/api/`: definicion de la API, routers, esquemas y dependencias
- `app/services/`: capa de servicios para catalogo, builds, jobs y scraper
- `database.py`: capa de acceso a SQLite y evolucion de esquema
- `scraper/`: implementacion actual del scraper con Playwright
- `app/enrichers/`: estructura base preparada para futuras normalizaciones por categoria
- `http/`: coleccion de archivos `.rest` para probar endpoints manualmente
- `serve.py`: arranque de la API leyendo configuracion por variables de entorno
- `main.py`: mantiene el flujo CLI existente y tambien expone la app FastAPI

## Base De Datos

La aplicacion mantiene SQLite como detalle interno de implementacion.

Tablas existentes conservadas:

- `components`
- `price_history`
- `gaming_chairs`
- `gaming_chair_price_history`

Tablas agregadas para la evolucion a API:

- `builds`
- `build_slots`
- `build_decisions`
- `build_snapshots`

La ruta de la base de datos se define con `DATABASE_PATH`.

Ejemplo:

```env
DATABASE_PATH=/data/ddtech.db
```

## Variables De Entorno

Estas variables controlan el comportamiento del servicio:

- `DATABASE_PATH`: ruta del archivo SQLite
- `HEADLESS`: ejecuta Chromium en modo headless si vale `true`
- `PLAYWRIGHT_TIMEOUT`: timeout en milisegundos para Playwright
- `LOG_LEVEL`: nivel de logging
- `EXPORT_JSON_PATH`: ruta del JSON exportado por el scraper
- `HOST`: host de arranque para uvicorn
- `PORT`: puerto de arranque para uvicorn
- `APP_VERSION`: version expuesta por la API

Valores tipicos:

```env
DATABASE_PATH=/data/ddtech.db
EXPORT_JSON_PATH=/data/ddtech_components.json
HEADLESS=true
PLAYWRIGHT_TIMEOUT=45000
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
APP_VERSION=1.0.0
```

## Ejecutar La API Localmente

Si ya tienes un entorno virtual activo y dependencias instaladas:

```powershell
python serve.py
```

La API quedara disponible en:

- `http://localhost:8000/`
- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`
- `http://localhost:8000/openapi.json`

## Documentacion De La API

El proyecto incluye documentacion automatica:

- `GET /` redirige a Swagger UI
- `GET /docs` abre Swagger UI
- `GET /redoc` abre ReDoc
- `GET /openapi.json` devuelve el esquema OpenAPI

## Endpoints Disponibles

### Estado Y Salud

- `GET /health`
- `GET /status`
- `GET /jobs/{jobId}`

### Catalogo

- `GET /categories`
- `GET /components`
- `GET /components/{componentId}`
- `GET /components/category/{category}`
- `GET /components/search?q=`
- `GET /components/latest`
- `GET /price-history/{componentId}`

### Builds

- `GET /builds`
- `POST /builds`
- `GET /builds/{id}`
- `PUT /builds/{id}`
- `DELETE /builds/{id}`
- `POST /builds/{id}/slots`
- `PUT /builds/{id}/slots/{slot}`
- `DELETE /builds/{id}/slots/{slot}`
- `POST /builds/{id}/slots/{slot}/decisions`
- `GET /builds/{id}/slots/{slot}/decisions`
- `POST /builds/{id}/snapshot`
- `GET /builds/{id}/compare`
- `GET /builds/{id}/total`

### Scraper

- `POST /scraper/update`

`POST /scraper/update` dispara un job asincrono. La solicitud responde de inmediato con un `jobId`, y su progreso puede consultarse despues con `GET /jobs/{jobId}`.

## Health Check

El endpoint recomendado para pruebas de despliegue es:

```http
GET /health
```

Respuesta esperada:

```json
{
  "status": "ok"
}
```

## Docker

El proyecto incluye dockerizacion completa mediante:

- `Dockerfile`
- `docker-compose.yml`

El contenedor:

- instala dependencias Python desde `requirements.txt`
- instala Playwright y Chromium
- arranca unicamente la API FastAPI
- no ejecuta scraping automaticamente al iniciar

## Probar Localmente Con Docker

Construir y levantar el servicio:

```powershell
docker compose up --build
```

Construir y levantar en segundo plano:

```powershell
docker compose up --build -d
```

Detener el servicio:

```powershell
docker compose down
```

Una vez arriba, puedes probar:

- `http://localhost:8000/`
- `http://localhost:8000/docs`
- `http://localhost:8000/health`
- `http://localhost:8000/status`

## Persistencia Fuera Del Contenedor

La configuracion de Docker monta `./data` dentro de `/data` en el contenedor:

```yaml
volumes:
  - ./data:/data
```

Esto permite que:

- la base SQLite viva fuera del contenedor
- el archivo JSON exportado viva fuera del contenedor
- no se pierda informacion al recrear la imagen o el contenedor

Archivos tipicos persistidos:

- `./data/ddtech.db`
- `./data/ddtech_components.json`

## Logging

La API usa logging estructurado en formato JSON.

Se registran eventos relevantes como:

- inicio del scraper
- fin del scraper
- fallos del scraper
- componentes actualizados
- duracion del job
- estado de solicitudes HTTP durante pruebas locales

## Coleccion REST Para Pruebas Manuales

Se agrego un directorio `http/` con un archivo `.rest` por endpoint, agrupado por router o controller.

Estructura general:

```text
http/
  health/
  status/
  categories/
  components/
  history/
  builds/
  scraper/
  jobs/
  http-client.env.json
```

Ejemplos de archivos disponibles:

- `http/health/get-health.rest`
- `http/status/get-status.rest`
- `http/components/get-components.rest`
- `http/components/search-components.rest`
- `http/builds/post-builds.rest`
- `http/builds/post-build-slot-decision.rest`
- `http/scraper/post-scraper-update.rest`
- `http/jobs/get-job-by-id.rest`

Estos archivos estan pensados para herramientas compatibles con archivos `.rest`, por ejemplo extensiones de cliente REST en VS Code.

## Flujo Recomendado De Prueba Manual

1. Levantar la API con `docker compose up --build`
2. Abrir `http://localhost:8000/docs`
3. Verificar `GET /health`
4. Verificar `GET /status`
5. Crear una build con `POST /builds`
6. Probar consultas de componentes
7. Lanzar un scraping de prueba con `POST /scraper/update`
8. Consultar el job generado con `GET /jobs/{jobId}`

## Compatibilidad Con El CLI Existente

Para no romper funcionalidad existente, el proyecto conserva el flujo por consola.

Ejemplos:

```powershell
python main.py --test-run
```

```powershell
python main.py
```

```powershell
python main.py --fallback
```

```powershell
python main.py --headless
```

El asistente actual tambien sigue disponible:

```powershell
python ai_helper.py
```

## Requisitos

- Python
- dependencias listadas en `requirements.txt`
- Docker Desktop si quieres probar con contenedor

Si corres localmente sin Docker, recuerda instalar Playwright Chromium:

```powershell
playwright install chromium
```

## Estado Actual Del Proyecto

Actualmente el proyecto ya esta preparado para:

- ejecutarse como API
- documentarse automaticamente con Swagger
- correr localmente con Docker
- usar SQLite por ruta configurable
- disparar scraping por endpoint sin bloquear la solicitud
- crecer posteriormente hacia mas servicios o nuevas fuentes de datos
