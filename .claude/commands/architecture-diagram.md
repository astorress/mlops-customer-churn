---
name: architecture-diagram
description: Crea o actualiza en draw.io el diagrama de arquitectura de un proyecto o sub-servicio de cualquier monorepo, investigando por su cuenta todo el repo (docs, infraestructura como código, código y dependencias entre servicios) y dibujándolo con un estilo consistente (íconos de nube, grupos punteados por stack, pasos numerados, capas, cuadro de explicación). Úsala cuando pidan "haz el diagrama de <proyecto>", "agrega <proyecto> al draw.io", "documenta la arquitectura de <x>" o "revisa/ajusta este bosquejo de diagrama".
---

# Diagrama de arquitectura en draw.io

El usuario nombra un proyecto, sub-servicio o flujo (y a veces pasa un
bosquejo `.drawio`). Tú investigas el monorepo completo y produces **una
página en el archivo draw.io de arquitectura del repo**, con el estilo de
esta skill (o el que ya tenga el archivo, si existe).

No le preguntes al usuario nada que se pueda averiguar en el repo. Pregunta
solo decisiones que sean realmente suyas (p. ej. dos archivos draw.io
candidatos y ninguno es claramente el de arquitectura).

---

## 1. Ubicar el archivo y aprender su estilo

1. Busca archivos draw.io en todo el repo (excluye `node_modules`, `.git`,
   `dist`, `build`, `.venv`):
   `find . \( -name '*.drawio' -o -name '*.drawio.xml' -o -name '*.dio' \) -not -path '*/node_modules/*'`
   - Si hay uno de arquitectura general (típicamente `docs/architecture.drawio`),
     agrega ahí una página nueva.
   - Si no hay ninguno, crea `docs/architecture.drawio` (o la carpeta de docs
     que use el repo) con `<mxfile pages="1">`.
   - Un `.drawio` suelto junto a la docs suele ser un **bosquejo** del usuario:
     úsalo como punto de partida, no lo borres (ofrece hacerlo al final).
2. Si el archivo está comprimido (`<diagram>` con texto base64 en vez de
   `<mxGraphModel>`), descomprímelo (base64 → inflate raw → URL-decode) y
   escríbelo sin comprimir; draw.io lo abre igual.
3. **Si ya tiene páginas, apréndelas antes de dibujar**: por cada página,
   lista capas (hijos de la celda raíz), estilos de íconos (`resIcon`,
   `shape`, `fillColor`), grupos, marcadores numerados y el cuadro de
   explicación (su HTML, idioma, colores). **El estilo existente manda**
   sobre los valores por defecto de esta skill; copia estilos literalmente
   de las celdas existentes cuando puedas.
4. Si el usuario ya editó páginas a mano, respeta sus patrones (p. ej. si
   convirtió un servicio en un grupo con engranes, haz lo mismo con
   servicios equivalentes).

## 2. Investigar el proyecto en todo el monorepo

Objetivo: saber **cada recurso, quién llama a quién y qué lee/escribe
cada pieza**, con evidencia en el código. Para repos grandes delega la
exploración amplia a un agente de búsqueda, pero verifica tú las flechas
clave.

**a. Mapa del monorepo**
- `README`, `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING`, archivos de workspace
  (`package.json` workspaces, `pnpm-workspace.yaml`, `nx.json`, `turbo.json`,
  `lerna.json`, `go.work`, `Cargo.toml` workspace, `pyproject` multi-paquete),
  `docker-compose*.yml` en la raíz. Identifica los sub-proyectos y cuál es
  el pedido.

**b. Documentación del proyecto**
- `<proyecto>/README*`, `CLAUDE.md`, `.claude/rules/*`, `docs/**`, ADRs,
  diagramas mermaid/plantuml existentes. Suelen describir el flujo y las
  decisiones, pero **no son la fuente de verdad**.

**c. Infraestructura como código (la fuente de verdad)**. Busca lo que haya:

| Herramienta | Dónde mirar |
|---|---|
| Serverless Framework | `serverless.yml`, `functions*.yml`, `resources/*.yml`, `${file(...)}`, `${ssm:...}`, `events:` |
| AWS CDK | `cdk.json`, `lib/**/*stack*.{ts,py}`, `new s3.Bucket`, `new lambda.Function`, grants |
| SAM / CloudFormation | `template.y*ml`, `Resources:`, `Outputs`/`Export`, `!ImportValue` |
| Terraform / OpenTofu | `*.tf`, `resource "aws_..."`, `module`, `data "terraform_remote_state"` |
| Pulumi | `Pulumi.yaml`, `index.ts`/`__main__.py` |
| Kubernetes / Helm | `k8s/`, `charts/`, `Deployment`, `Service`, `Ingress`, `ConfigMap` |
| Contenedores | `Dockerfile`, `docker-compose*.yml`, Elastic Beanstalk (`.ebextensions`, `Dockerrun`), ECS task defs |
| CI/CD | `.gitlab-ci.yml`, `.github/workflows`, `buildspec.yml` (orden de despliegue, stacks) |

De ahí salen: recursos, triggers (colas, tópicos, eventos, cron, rutas de
API), **variables de entorno** (qué bucket/tabla/secreto/cola usa cada
función) y **permisos IAM** (qué toca realmente cada pieza).

**d. Código**
- Handlers/entrypoints, clientes de SDK (`boto3.client(...)`,
  `new S3Client`, `publish`, `send_message`, `put_object`,
  `generate_presigned_url`, `invoke`, consultas SQL, clientes HTTP/WebSocket).
  Confirma cada flecha: origen, destino y qué hace.

**e. Dependencias con otros sub-proyectos**
- Parámetros compartidos (SSM, exports de CloudFormation, remote state,
  variables `.env`): indican de qué stack viene cada recurso.
- Busca en todo el repo el nombre de los recursos, rutas y tópicos del
  proyecto (`grep -rI`): así encuentras **quién lo consume** (frontend,
  panel interno, otro servicio) y **de quién depende** (infra compartida,
  bases de datos, servicio de autenticación).

**f. Bosquejo del usuario (si hay)**
- Extrae cada celda (`value`, `resIcon`/`shape`, `source`/`target`).
- Contrasta elemento por elemento con el código y clasifícalos en: correcto,
  sobra (no existe en el código), falta (existe y no está), mal nombrado.

**Si la documentación y el código no coinciden, el diagrama sigue al
código** y se lo reportas al usuario.

## 3. Reglas de edición del archivo

- **Relee el archivo antes de cada escritura**: el usuario lo edita a mano
  entre sesiones.
- Haz un respaldo en el scratchpad antes de escribir.
- Toca **solo la página pedida**: insértala antes de `</mxfile>` o
  reemplaza únicamente su `<diagram id="<slug>-page">…</diagram>`. Actualiza
  `pages="N"` en `<mxfile>`.
- Al terminar, compara todas las demás páginas con el respaldo: deben ser
  idénticas.
- IDs con prefijo propio (`<slug>-1`, `<slug>-bg`…) para no chocar.
- Si el usuario ya editó a mano tu página, **no la regeneres**: modifica su
  XML en el lugar para no perder sus cambios.

## 4. Estilo (valores por defecto si el archivo no tiene uno propio)

### Flechas
- **Sin texto** (`value=""`), siempre: las etiquetas saturan el diagrama.
  Lo que diría una etiqueta (filtros, reintentos, URL firmadas, códigos de
  respuesta) va en el cuadro de explicación.
- **Siempre redondeadas**:
  `edgeStyle=orthogonalEdgeStyle;rounded=1;curved=0;orthogonalLoop=1;jettySize=auto;html=1;fontFamily=Verdana;`
- `dashed=1;` solo para caminos secundarios: DLQ, reintentos, descargas o
  accesos directos con URL firmada, accesos indirectos.
- Que no crucen íconos, etiquetas ni otras flechas: controla
  `exitX/exitY/entryX/entryY` (+ `exitPerimeter=0;entryPerimeter=0;`) y
  puntos intermedios `<Array as="points">`. Si varias flechas salen del
  mismo lado de un ícono, repártelas (0.25 / 0.5 / 0.75). Si la etiqueta de
  un ícono estorba, muévela (`labelPosition=left;verticalLabelPosition=middle;align=right;verticalAlign=middle;`).

### Numeración de pasos
- **Todo servicio o recurso lleva número**, incluidos los de soporte
  (secretos, tablas, buckets, colas de error). **Una flecha no es un paso**:
  acciones como "el panel revisa el bucket" se explican en el texto sin
  marcador propio.
- Marcador: celda de texto 48×52 arriba a la derecha del ícono (≈ `x+70, y-30`):
  `style="text;whiteSpace=wrap;html=1;fontFamily=Verdana;"`,
  `value='<font style="font-size: 25px; color: rgb(103, 171, 159);">➊</font>'`.
- Secuencia: ➊ ➋ ➌ ➍ ➎ ➏ ➐ ➑ ➒ ➓ ⓫ ⓬ ⓭ ⓮ ⓯ ⓰ ⓱ ⓲ ⓳ ⓴.
- Un color por flujo, cada flujo numera desde ➊: verde azulado
  `rgb(103, 171, 159)` para el flujo principal/interno, azul
  `rgb(0, 127, 255)` para el segundo (p. ej. un cliente externo o una API
  pública). Un recurso usado en dos momentos reutiliza su número.

### Capas
Hijas de la celda raíz, en este orden:
1. `background`: rectángulo blanco (`whiteSpace=wrap;html=1;strokeColor=none;`)
   que cubre toda la página.
2. `<slug>-common`: lo compartido por varios flujos (buckets, bases de
   datos, autenticación, la app de entrada), para que ocultar un flujo no
   deje flechas apuntando al vacío.
3. Una capa **por flujo o por stack** (`<slug>-generation`, `<slug>-api`,
   `<slug>-worker`…). Cada flecha va en la capa de su flujo.
4. `<slug>-info`: el cuadro de explicación.

### Grupos
- Un grupo punteado por **stack/unidad de despliegue** y por
  infraestructura compartida externa al proyecto. Son rectángulos detrás de
  los íconos (`container=0`), con el nombre del stack:
  ```
  points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=0;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud;strokeColor=default;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#232F3E;labelBackgroundColor=none;fontFamily=Verdana;dashed=1;dashPattern=8 8;
  ```
- **Las bases de datos van en su propio grupo, con el nombre de la base**
  ("Data <br>Warehouse", "MongoDB"), nunca dentro del grupo de
  infraestructura compartida.
- **Cada recurso compartido va en su propia cajita, nombrada por el stack
  de donde sale**, no todos juntos en un grupo genérico: el secreto con
  las credenciales de la base en "Database Infrastructure", el bucket
  compartido en "Common Infrastructure", y así con colas o tópicos de otros
  stacks. Usa el mismo nombre para el mismo stack en todas las páginas.
- Servicio interno sin ícono propio (servicio de auth, microservicio de
  otra área): grupo punteado con su nombre y dos `shape=mxgraph.aws4.gear`
  (47×47, `fillColor=#232F3D;strokeColor=none;`).
- Contenedor/app desplegada: grupo de la plataforma (p. ej. Elastic
  Beanstalk `grIcon=mxgraph.aws4.group_elastic_beanstalk;strokeColor=#D86613;fontColor=#D86613;dashed=0;`,
  ECS/EKS equivalente) con un rectángulo "Container"
  (`fillColor=none;strokeColor=#5A6C86;dashed=1;verticalAlign=top;fontColor=#5A6C86;`)
  y la app dentro (`shape=mxgraph.vvd.web_browser;fillColor=#434445;` 80×60).

### Actores y entradas
- Persona: `shape=mxgraph.aws4.user;fillColor=#232F3D;strokeColor=none;aspect=fixed;` 60×60.
- Portal/navegador: `shape=mxgraph.veeam2.laptop;fillColor=#CCCCCC;strokeColor=none;` 100×60.
- Sistema externo/cliente: mismo ícono de usuario con etiqueta
  "Client system (<nombre>)".
- Si varias páginas del archivo comparten la misma entrada (usuario →
  portal → app), **cópiala igual** en cada página.

### Íconos de recursos (78×78, etiqueta debajo, Verdana)
```
sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#232F3E;fillColor=<COLOR>;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.<ICON>;fontFamily=Verdana;
```

| Categoría | `resIcon` | `fillColor` |
|---|---|---|
| Cómputo (Lambda, ECS, EC2, Fargate) | `lambda`, `ecs`, `ec2`, `fargate` | `#ED7100` |
| Integración (SQS, SNS, EventBridge, Step Functions, API Gateway) | `sqs`, `sns`, `eventbridge`, `step_functions`, `api_gateway` | `#E7157B` |
| Almacenamiento (S3, EFS) | `s3`, `elastic_file_system` | `#7AA116` |
| Seguridad (Cognito, Secrets Manager, KMS, IAM) | `cognito`, `secrets_manager`, `key_management_service`, `identity_and_access_management` | `#DD344C` |
| Bases de datos (DynamoDB, RDS, Aurora, ElastiCache) | `dynamodb`, `rds`, `aurora`, `elasticache` | `#C925D1` |
| IA/ML (Bedrock, SageMaker, Textract) | `bedrock`, `sagemaker`, `textract` | `#01A88D` |
| Red (CloudFront, Route 53, ELB) | `cloudfront`, `route_53`, `elastic_load_balancing` | `#8C4FFF` |
| Observabilidad (CloudWatch) | `cloudwatch` | `#E7157B` |

Fuera de AWS: MongoDB `shape=mxgraph.webicons.mongodb;gradientColor=#DFDEDE;`
(88×83); Postgres/MySQL/Redis con `mxgraph.webicons.*` o
`mxgraph.aws4.rds`; Azure/GCP con sus librerías (`mxgraph.azure.*`,
`mxgraph.gcp2.*`) manteniendo tamaño y Verdana. Si no hay forma exacta
(p. ej. un servicio nuevo), usa la más cercana y distingue por la etiqueta;
avísalo en el resumen. Si el archivo ya tiene un ícono para ese recurso,
reutiliza su estilo exacto.

### Cuadro de explicación (capa `-info`, a la derecha, ~700 px de ancho)
```
text;html=1;spacing=20;spacingTop=-30;whiteSpace=wrap;overflow=hidden;rounded=1;fontSize=12;fontFamily=Helvetica;fillColor=#7EA6E0;strokeColor=none;arcSize=4;glass=0;shadow=0;opacity=25;
```
HTML (escapado dentro de `value`):
`<h1 style="line-height: 120%;"><font face="Verdana" style="font-size: 18px;"><Nombre> Flow</font></h1><div style="text-align: justify; line-height: 120%;"><font face="Verdana"><p>…</p></font></div>`

- **Idioma**: el de los cuadros existentes del archivo; si no hay, inglés.
- 1.er párrafo: qué hace, para quién, en qué stacks vive, qué no hace
  (p. ej. "only reads data").
- Un párrafo por etapa, recorriendo los pasos en orden; cada servicio en
  `<b>` seguido de su marcador inline
  (`<font style="font-size: 18px; color: rgb(103, 171, 159);">➋</font>`).
- Explica lo que no dicen las flechas: filtros, reintentos/DLQ,
  asincronía, validaciones y de dónde sale cada dato. Si un recurso se usa
  para algo que no es evidente (p. ej. la función lee un archivo del
  bucket), nómbralo con su número.
- **Sin detalles de implementación de bajo nivel**: nada de rutas/prefijos
  de buckets, nombres de keys, ARNs ni **nombres técnicos de permisos**
  (`POST/orders`, `Query/listUsers`…), **headers**
  (`x-tenant-id`, `Authorization`), dominios, nombres internos
  de resolvers/tools/funciones de código ni valores de enums; descríbelos en
  palabras ("only users allowed to call the API", "sending the user's
  session and the tenant they are working on"). Sí van los nombres de
  los recursos que aparecen en el diagrama (Lambdas, colas, tablas).
- Altura ajustada al texto, sin espacio vacío grande.

### Layout
Flujo de izquierda a derecha: actores y app de entrada a la izquierda,
stacks del proyecto al centro, infraestructura compartida (secretos, bases
de datos, buckets) en una columna a la derecha, un segundo flujo en una
franja inferior, cuadro de info al final a la derecha. 140–200 px entre
íconos; grupos sin solaparse.

## 5. Generarlo

Genera la página con un script Python en el scratchpad y mantenlo durante la
sesión: cada ajuste se hace editando el script y regenerando (salvo que el
usuario haya editado la página a mano, ver §3). Esqueleto:

```python
import re
from xml.sax.saxutils import escape
q = lambda s: escape(s, {'"': '&quot;'})
P, SLUG, NAME = 'docs/architecture.drawio', 'myservice', 'My Service'
cells, n, L = [], [0], f'{SLUG}-common'   # L = capa actual

def nid():
    n[0] += 1
    return f'{SLUG}-{n[0]}'

def v(value, style, x, y, w, h):
    i = nid()
    cells.append(f'<mxCell id="{i}" parent="{L}" style="{q(style)}" value="{q(value)}" vertex="1">'
                 f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" /></mxCell>')
    return i

def e(src, dst, style='', pts=None):
    i = nid()
    arr = '' if not pts else '<Array as="points">' + ''.join(
        f'<mxPoint x="{x}" y="{y}" />' for x, y in pts) + '</Array>'
    cells.append(f'<mxCell id="{i}" edge="1" parent="{L}" source="{src}" target="{dst}" '
                 f'style="{q(EDGE + style)}" value=""><mxGeometry relative="1" as="geometry">{arr}</mxGeometry></mxCell>')

def mark(ch, x, y, color='rgb(103, 171, 159)'):
    v(f'<font style="font-size: 25px; color: {color};">{ch}</font>',
      'text;whiteSpace=wrap;html=1;fontFamily=Verdana;', x, y, 48, 52)

# ... cambiar L por capa, crear grupos, íconos, marcadores y flechas ...

layers = ''.join(f'<mxCell id="{SLUG}-{k}" parent="{SLUG}-0" value="{SLUG}-{k}" />'
                 for k in ('common', 'flow-a', 'flow-b'))
page = (f'<diagram id="{SLUG}-page" name="{NAME}"><mxGraphModel grid="0" page="1" background="#ffffff"><root>'
        f'<mxCell id="{SLUG}-0" /><mxCell id="{SLUG}-bg" parent="{SLUG}-0" value="background" />'
        f'<mxCell id="{SLUG}-bgr" parent="{SLUG}-bg" style="whiteSpace=wrap;html=1;strokeColor=none;" value="" vertex="1">'
        f'<mxGeometry width="2700" height="1150" as="geometry" /></mxCell>'
        + layers + ''.join(cells) +
        f'<mxCell id="{SLUG}-info" parent="{SLUG}-0" value="{SLUG}-info" />'
        # + la celda del cuadro de explicación con parent="{SLUG}-info"
        '</root></mxGraphModel></diagram>')

s = open(P, encoding='utf-8').read()
# Replace the page in place (keeps page order); append only if it's new
m = re.search(rf'<diagram id="{SLUG}-page".*?</diagram>', s, flags=re.S)
s = s[:m.start()] + page + s[m.end():] if m else s.replace('</mxfile>', page + '\n</mxfile>', 1)
s = re.sub(r'(<mxfile\b[^>]*\bpages=")\d+(")', lambda m: f'{m[1]}{s.count("<diagram ")}{m[2]}', s, 1)
open(P, 'w', encoding='utf-8').write(s)
```

## 6. Verificar (siempre, antes de reportar)

1. **Estructura**: el XML parsea; IDs únicos; todo `source`/`target`
   existe; ninguna flecha tiene `value`; todas tienen `rounded=1`; las demás
   páginas son idénticas al respaldo.
2. **Visual**: exporta la página y mírala:
   ```bash
   # macOS: /Applications/draw.io.app/Contents/MacOS/draw.io
   # Linux: drawio (puede requerir xvfb-run)
   draw.io --export --format png --page-index <N> --scale 0.6 \
     --output <scratchpad>/page.png <archivo.drawio>
   ```
   `--page-index` empieza en **1**. Abre el PNG y busca: flechas que
   atraviesan íconos o etiquetas, flechas encimadas, marcadores tapados o
   faltantes, grupos solapados, cuadro de texto con espacio sobrante.
   Corrige y exporta de nuevo hasta que quede limpio.
   Si no hay CLI de draw.io, dilo y pide al usuario una captura.

## 7. Resumen al usuario

- Qué fuentes revisaste (docs, IaC, código) y, si hubo bosquejo, una tabla
  *bosquejo → código → qué hice*.
- Capas creadas y qué contiene cada una.
- Íconos aproximados y discrepancias entre documentación y código.
- Ofrece actualizar la documentación del proyecto que diga que el diagrama
  no lo incluye, y borrar el bosquejo si ya no sirve.
