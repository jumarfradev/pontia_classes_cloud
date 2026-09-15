# Laboratorio 1: RAG con Bedrock Knowledge Base (AWS CDK)

## 📋 Resumen del Despliegue

Este laboratorio despliega una aplicación RAG completa usando **AWS CDK con despliegue stack a stack**:

1. **Storage Stack** - S3 + DynamoDB (2-3 min)
2. **Knowledge Base Stack** - Bedrock Knowledge Base + S3 Data Source (5-10 min)
3. **Lambda Stack** - Upload + Query Functions (2-3 min)
4. **API Stack** - API Gateway REST (2-3 min)
5. **Frontend Stack** - S3 Static Hosting (1-2 min)

**Tiempo total:** ~15-25 minutos

**Ventaja:** Puedes monitorear cada paso y resolver problemas de forma aislada.

---

## 🏗️ Arquitectura Desplegada

### Componentes Principales

- **Frontend**: Aplicación web interactiva (HTML/CSS/JavaScript)
- **API Gateway**: Endpoints REST para upload y query
- **Lambda Functions**: Procesamiento de documentos y búsqueda RAG
- **Bedrock Knowledge Base**: Indexación semántica de documentos (reemplaza a Kendra)
- **Bedrock**: Generación de respuestas con IA (Claude 3 Haiku / modelo configurable)
- **S3**: Almacenamiento de documentos y frontend estático
- **DynamoDB**: Metadata de documentos y historial de consultas

### Flujo de Datos

```
Usuario → Frontend → API Gateway → Lambda → (Bedrock Knowledge Base + Bedrock) → DynamoDB
```

---

## 🚀 Despliegue Rápido (Comando Único)

Para desplegar toda la aplicación de una vez:

```bash
# Reemplaza "alumno" con tu nombre o apellido
cdk deploy --all --app "python3 cdk_app.py --lab-name rag-lab-alumno" --require-approval never
```

**Tiempo total:** ~15-25 minutos

---

## 📚 Despliegue Paso a Paso

### Paso 1 – Preparar el archivo ZIP localmente

En este paso, prepararemos el archivo ZIP con el código del proyecto para subirlo a CloudShell.

#### 1.1 – Comprimir la carpeta del proyecto

1. Abre una terminal en tu máquina local.
2. Navega a la carpeta padre de Laboratorio 1:

```bash
cd /Users/personal/Projects/Pontia/Clase\ 6
```

3. Crea un archivo ZIP con la carpeta Laboratorio 1:

```bash
zip -r rag-lab.zip Laboratorio\ 1/
```

> **👉 Resultado:** Se crea el archivo `rag-lab.zip` en la carpeta Clase 6.

---

### Paso 2 – Acceder a AWS CloudShell

1. Abre la consola de AWS en tu navegador.
2. En la barra superior, busca el icono de **CloudShell** (terminal) o haz clic en el icono de terminal.
3. Espera a que CloudShell se cargue (puede tardar unos segundos).

> **👉 Resultado:** Tienes una terminal en la nube lista para usar.

---

### Paso 3 – Subir el archivo ZIP a CloudShell

#### 3.1 – Usar el gestor de archivos de CloudShell

1. En CloudShell, haz clic en el icono de **Actions** (arriba a la derecha).
2. Selecciona **Upload file**.
3. Selecciona el archivo `rag-lab.zip` de tu máquina local.
4. Espera a que se complete la carga.

> **✅ Resultado esperado:** El archivo ZIP está en CloudShell.

#### 3.2 – Verificar que se subió correctamente

```bash
ls -lh rag-lab.zip
```

> **👉 Resultado:** Deberías ver el archivo listado con su tamaño.

---

### Paso 4 – Descomprimir y preparar el proyecto

```bash
# Descomprimir el archivo
unzip rag-lab.zip

# Navegar a la carpeta del proyecto
cd Laboratorio\ 1

# Verificar que los archivos están presentes
ls -la
```

> **👉 Resultado:** Ves los archivos `cdk_app.py`, `requirements.txt`, carpetas `stacks/`, `lambdas/`, `frontend/`.

---

### Paso 5 – Instalar dependencias en CloudShell

CloudShell ya tiene Python y Node.js instalados. Solo necesitas instalar las dependencias del proyecto:

```bash
# Instalar dependencias Python
pip install -r requirements.txt

# Instalar AWS CDK CLI (si no está instalado)
npm install -g aws-cdk

# Verificar que CDK está instalado
cdk --version
```

> **✅ Resultado esperado:** Todas las dependencias están instaladas.

---

### Paso 6 – Bootstrap del entorno CDK

El bootstrap prepara tu cuenta AWS para usar CDK:

```bash
# Obtener tu AWS Account ID
aws sts get-caller-identity --query Account --output text

# Bootstrap (reemplaza ACCOUNT_ID con tu ID)
cdk bootstrap aws://ACCOUNT_ID/eu-west-1
```

> **👉 Explicación:** Esto crea un bucket S3 y otros recursos necesarios para que CDK funcione en tu cuenta.

> **✅ Resultado esperado:** Ves un mensaje indicando que el bootstrap se completó.

---

### Paso 7 – Configurar tu nombre en cdk.json

Antes de desplegar, edita el fichero `cdk.json` y cambia `lab_name` con tu nombre o apellido:

```json
{
  "app": "python3 cdk_app.py",
  "context": {
    "lab_name": "rag-lab-alumno",
    "region": "eu-west-1",
    "upload_frontend": false
  }
}
```

> **👉** Cambia `rag-lab-alumno` por algo único, por ejemplo `rag-lab-garcia`. Esto evita colisiones de nombres en S3 y DynamoDB.

---

### Paso 8 – Desplegar Stack a Stack

Desplegaremos la infraestructura paso a paso. Los parámetros se leen automáticamente de `cdk.json`.

#### 8.1 – Desplegar Storage Stack

```bash
cdk deploy rag-lab-alumno-storage --require-approval never
```

> **💡 Nota:** El nombre del stack debe coincidir con el `lab_name` de `cdk.json` + `-storage`.

**Qué se crea:**
- S3 Bucket para documentos: `rag-lab-alumno-documents-{ACCOUNT_ID}`
- DynamoDB Table: `rag-lab-alumno-documents`
- DynamoDB Table: `rag-lab-alumno-queries`

**Tiempo:** ~2-3 minutos

> **✅ Resultado:** Storage desplegado correctamente.

#### 8.2 – Desplegar Knowledge Base Stack

```bash
cdk deploy rag-lab-alumno-storage rag-lab-alumno-kb --require-approval never
```

**Qué se crea:**
- Bedrock Knowledge Base: `rag-lab-alumno-kb` con embeddings Titan Embed Text v2
- OpenSearch Serverless collection e índice vectorial (creados automáticamente por el construct)
- S3 Data Source: `rag-lab-alumno-documents` apuntando al prefijo `documents/`

**Tiempo:** ~5-10 minutos (OpenSearch Serverless y Bedrock Knowledge Base tardan más en crearse)

> **✅ Resultado:** Knowledge Base creada y lista para indexar documentos.

#### 8.3 – Desplegar Lambda Stack

```bash
cdk deploy rag-lab-alumno-storage rag-lab-alumno-kb rag-lab-alumno-lambdas --require-approval never
```

**Qué se crea:**
- Lambda Function: `rag-lab-alumno-upload` - Procesa uploads de PDF y lanza ingestion job
- Lambda Function: `rag-lab-alumno-query` - Búsqueda + generación con Bedrock Knowledge Base
- IAM Role con permisos para S3, DynamoDB, Bedrock Agent y Bedrock Agent Runtime

**Tiempo:** ~2-3 minutos

> **✅ Resultado:** Lambda Functions desplegadas y configuradas.

#### 8.4 – Desplegar API Stack

```bash
cdk deploy rag-lab-alumno-storage rag-lab-alumno-kb rag-lab-alumno-lambdas rag-lab-alumno-api --require-approval never
```

**Qué se crea:**
- API Gateway: `rag-lab-alumno-api`
- Endpoints:
  - `POST /upload` - Subir documento
  - `POST /query` - Realizar búsqueda
  - `GET /documents` - Listar documentos
- CORS habilitado

**Tiempo:** ~2-3 minutos

> **✅ Resultado:** API Gateway completamente funcional.

---

### Paso 9 – Desplegar Frontend Stack

Ahora que el backend está completamente desplegado, subiremos el frontend. Primero pon `upload_frontend` a `true` en `cdk.json`:

```json
{
  "app": "python3 cdk_app.py",
  "context": {
    "lab_name": "rag-lab-alumno",
    "region": "eu-west-1",
    "upload_frontend": true
  }
}
```

Luego despliega todos los stacks a la vez:

```bash
cdk deploy --all --require-approval never
```

Este comando:
- Crea S3 Bucket para frontend: `rag-lab-alumno-frontend-{ACCOUNT_ID}`
- Sube el frontend (`index.html`, `styles.css`, `app.js`) al bucket S3
- Inyecta automáticamente la URL del API Gateway en el frontend
- Configura el website hosting en S3

**Qué se crea:**
- Website configuration en S3
- Archivos frontend subidos con preguntas sugeridas
- `config.json` con la URL del API Gateway

**Tiempo:** ~1-2 minutos

> **✅ Resultado:** Frontend está subido al bucket S3 y listo para usar.

---

### Paso 9 – Acceder a la aplicación

1. Abre tu navegador web.
2. Ve a la **FrontendUrl** que obtuviste en el despliegue:
   ```
   http://rag-lab-alumno-frontend-ACCOUNT_ID.s3-website-eu-west-1.amazonaws.com
   ```
3. Deberías ver la interfaz de la aplicación RAG con:
   - Panel de upload de documentos
   - Chat interactivo con preguntas sugeridas
   - Listado de documentos procesados

> **✅ Resultado esperado:** La aplicación carga correctamente.

---

### Paso 10 – Probar la aplicación

#### 10.1 – Subir un documento PDF

1. En el panel **📄 Subir Documentos**:
   - Arrastra un PDF o haz clic para seleccionar
   - Haz clic en **Subir Documento**
2. Abre la consola del navegador (F12) para ver los logs.

> **✅ Resultado esperado:**
> - El documento se sube a S3
> - Se registra en DynamoDB con status "processing"
> - Lambda lanza un *ingestion job* en Bedrock Knowledge Base
> - El estado cambiará a "completed" una vez finalice la indexación

#### 10.2 – Realizar una búsqueda

> **⚠️ Importante:** Bedrock Knowledge Base necesita unos minutos para indexar el documento tras subirlo. Puedes revisar el estado en la consola de Bedrock → Knowledge bases → Data source → Sync history.

1. En el panel **💬 Chat RAG**:
   - Usa las preguntas sugeridas o escribe tu propia pregunta
   - Ejemplo: "¿Cuál es la tasa de desempleo juvenil en España?"
2. Haz clic en **Enviar** o presiona Enter.
3. La aplicación consulta Bedrock Knowledge Base y genera la respuesta con Bedrock.

> **✅ Resultado esperado:**
> - Bedrock KB recupera los fragmentos de documentos más relevantes
> - Bedrock genera una respuesta contextualizada
> - Se muestra la respuesta con fuentes citadas

---

## 🧭 Navegación por Servicios AWS

### 📊 ¿Qué Hemos Desplegado?

#### 1. **Frontend - Interfaz de Usuario**
- **Propósito**: Aplicación web interactiva para usuarios finales
- **Tecnología**: HTML5, CSS3, JavaScript vanilla
- **Funcionalidades**:
  - Upload de documentos PDF con drag & drop
  - Chat RAG con preguntas sugeridas predefinidas
  - Listado de documentos con estado en tiempo real
  - Diseño responsive y moderno
- **Ubicación**: S3 Static Website Hosting

#### 2. **API Gateway - Puerta de Entrada**
- **Propósito**: Exponer endpoints REST para la aplicación
- **Endpoints**:
  - `POST /upload` - Procesa uploads de archivos PDF
  - `POST /query` - Realiza búsquedas RAG con IA
  - `GET /documents` - Lista todos los documentos
- **Características**: CORS habilitado, integración con Lambda

#### 3. **Lambda Functions - Lógica de Negocio**
- **Upload Lambda**:
  - Procesa archivos PDF subidos
  - Guarda en S3 y registra metadata en DynamoDB
  - Lanza un `StartIngestionJob` en Bedrock Knowledge Base
- **Query Lambda**:
  - Consulta Bedrock Knowledge Base con `RetrieveAndGenerate`
  - Recibe respuestas con citas de fuentes
  - Guarda historial en DynamoDB

#### 4. **Bedrock Knowledge Base - Búsqueda Semántica**
- **Propósito**: Indexación y búsqueda semántica de documentos (reemplaza a Amazon Kendra)
- **Configuración**:
  - Modelo de embeddings: `Amazon Titan Embed Text v2`
  - Vector store: OpenSearch Serverless (creado automáticamente)
  - Data Source S3 con prefijo `documents/`
  - Sincronización manual o mediante ingestion job desde Lambda
- **Ventaja**: Integración nativa con Bedrock para retrieve + generate

#### 5. **Bedrock - Generación de IA**
- **Propósito**: Generación de respuestas con lenguaje natural
- **Modelo**: `Amazon Nova 2 Lite` (versión del inference profile `eu.amazon.nova-2-lite-v1:0`, configurable en `lambdas/query_handler.py`)
- **Función**: Procesa el contexto recuperado por Bedrock KB y genera respuestas coherentes

> **Nota sobre modelos:** Muchas regiones de AWS (incluido `eu-west-1`) requieren usar el **ID del inference profile** en lugar del ID del foundation model para evitar errores de *on-demand throughput*. El valor por defecto usa el inference profile `eu.amazon.nova-2-lite-v1:0`. Si necesitas cambiarlo, busca primero los perfiles disponibles con `aws bedrock list-inference-profiles --region eu-west-1` y actualiza `GENERATION_MODEL_ID` en `lambdas/query_handler.py`.

#### 6. **S3 - Almacenamiento**
- **Bucket de Documentos**: Almacena archivos PDF originales
- **Bucket de Frontend**: Hosting de archivos web estáticos
- **Características**: Versioning, lifecycle policies, acceso privado

#### 7. **DynamoDB - Base de Datos**
- **Tabla de Documentos**: Metadata, estado, rutas S3
- **Tabla de Queries**: Historial de búsquedas, respuestas, timestamps
- **Ventajas**: Escalable, serverless, baja latencia

### 🔍 Cómo Navegar y Verificar los Servicios

#### AWS Management Console

1. **CloudFormation**
   - Busca los stacks: `rag-lab-alumno-storage`, `rag-lab-alumno-kb`, etc.
   - Revisa los outputs y recursos creados

2. **S3**
   - Bucket: `rag-lab-alumno-documents-{ACCOUNT_ID}`
   - Revisa carpeta `documents/` para los PDFs subidos
   - Bucket: `rag-lab-alumno-frontend-{ACCOUNT_ID}`
   - Verifica archivos `index.html`, `styles.css`, `app.js`

3. **DynamoDB**
   - Tabla: `rag-lab-alumno-documents` - metadata de archivos
   - Tabla: `rag-lab-alumno-queries` - historial de búsquedas

4. **Lambda**
   - Función: `rag-lab-alumno-upload` - logs de procesamiento
   - Función: `rag-lab-alumno-query` - logs de búsquedas RAG

5. **API Gateway**
   - API: `rag-lab-alumno-api` - endpoints y configuración
   - Testea los endpoints directamente desde la consola

6. **Bedrock → Knowledge bases**
   - Knowledge Base: `rag-lab-alumno-kb`
   - Revisa el estado, el data source y el historial de sincronizaciones

7. **CloudWatch**
   - Logs de Lambda para debugging
   - Métricas de rendimiento y errores

#### Comandos AWS CLI Útiles

```bash
# Verificar Knowledge Base
data_source_id=$(aws cloudformation describe-stacks \
  --stack-name rag-lab-alumno-kb \
  --query 'Stacks[0].Outputs[?OutputKey==`DataSourceId`].OutputValue' \
  --output text --region eu-west-1)
kb_id=$(aws cloudformation describe-stacks \
  --stack-name rag-lab-alumno-kb \
  --query 'Stacks[0].Outputs[?OutputKey==`KnowledgeBaseId`].OutputValue' \
  --output text --region eu-west-1)

# Listar ingestion jobs
aws bedrock-agent list-ingestion-jobs \
  --knowledge-base-id "$kb_id" \
  --data-source-id "$data_source_id" \
  --region eu-west-1

# Listar documentos en DynamoDB
aws dynamodb scan --table-name rag-lab-alumno-documents --region eu-west-1

# Ver historial de consultas
aws dynamodb scan --table-name rag-lab-alumno-queries --region eu-west-1

# Revisar logs de Lambda
aws logs tail /aws/lambda/rag-lab-alumno-query --follow --region eu-west-1
```

### 🎯 Flujo Completo de una Consulta RAG

1. **Usuario** escribe pregunta en el frontend
2. **Frontend** envía a API Gateway (`POST /query`)
3. **API Gateway** invoca Lambda Query
4. **Lambda** llama a `bedrock-agent-runtime.retrieve_and_generate` con la Knowledge Base
5. **Bedrock Knowledge Base** recupera fragmentos relevantes de los documentos indexados
6. **Bedrock** genera respuesta contextualizada con citas
7. **Lambda** guarda consulta en DynamoDB
8. **Frontend** muestra respuesta con fuentes

---

## 🔧 Troubleshooting

### Error: "SSM parameter /cdk-bootstrap/hnb659fds/version not found"

**Solución:** Ejecutar bootstrap primero:
```bash
cdk bootstrap aws://ACCOUNT_ID/eu-west-1
```

### Error: "Bedrock model not found" / "Model is marked by provider as Legacy" / "on-demand throughput isn’t supported"

**Solución:** Verifica que Bedrock esté habilitado en tu región:
```bash
aws bedrock list-foundation-models --region eu-west-1
aws bedrock list-inference-profiles --region eu-west-1
```

Asegúrate de tener acceso concedido a:
- `Amazon Titan Embed Text v2` (embeddings)
- El modelo de generación configurado en `lambdas/query_handler.py`

En `eu-west-1`, muchos modelos requieren el **ID del inference profile** (p. ej. `eu.amazon.nova-2-lite-v1:0`). Si ves errores de *Legacy* o *on-demand throughput*, actualiza `GENERATION_MODEL_ID` en `lambdas/query_handler.py` con un inference profile activo y redepliega:
```bash
cdk deploy --all --app "python3 cdk_app.py --lab-name rag-lab-alumno --stack lambdas"
```

### Bedrock Knowledge Base no indexa documentos

**Solución:** Lanza la sincronización manualmente desde la consola de Bedrock:
1. Bedrock → Knowledge bases → `rag-lab-alumno-kb`
2. Selecciona el Data Source
3. Haz clic en **Sync**

O usa AWS CLI:
```bash
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id KB_ID \
  --data-source-id DATA_SOURCE_ID \
  --region eu-west-1
```

### La aplicación no carga

**Solución:** Recarga la página con Ctrl+Shift+R para limpiar la caché del navegador.

### Error de Lambda con Decimal

**Solución:** El código ya incluye manejo de tipos Decimal de DynamoDB.

---

## 🧹 Limpieza (Opcional)

Para eliminar todos los recursos creados:

```bash
cdk destroy --app "python3 cdk_app.py --lab-name rag-lab-alumno"
```

> **👉 Nota:** CDK eliminará automáticamente todos los recursos (Knowledge Base, OpenSearch Serverless, Lambda, DynamoDB, API Gateway, S3, IAM roles, etc.).

---

## 🎓 Resultado Esperado

Al finalizar este laboratorio, cada alumno debe haber:

- ✅ **Desplegado** una aplicación RAG completa con AWS CDK
- ✅ **Configurado** Bedrock Knowledge Base para búsqueda semántica
- ✅ **Integrado** Bedrock para generación de respuestas
- ✅ **Creado** una interfaz web moderna con preguntas sugeridas
- ✅ **Procesado** documentos PDF con metadata en DynamoDB
- ✅ **Implementado** búsqueda RAG con fuentes citadas
- ✅ **Verificado** todos los servicios AWS desplegados
- ✅ **Comprendido** la arquitectura serverless y sus interacciones
- ✅ **Aprendido** a usar AWS CDK para infraestructura como código
- ✅ **Entendido** la integración de múltiples servicios AWS

### 🚀 **Aplicación RAG 100% Funcional**

**Frontend**: http://rag-lab-alumno-frontend-{ACCOUNT_ID}.s3-website-eu-west-1.amazonaws.com  
**API**: https://{api-id}.execute-api.eu-west-1.amazonaws.com/prod/

La aplicación está lista para producción con todas las funcionalidades RAG implementadas.
