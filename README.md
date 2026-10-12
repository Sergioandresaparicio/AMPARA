# AMPARA: Asistente Juridico Autonomo en Salud y Tutelas para Colombia

Sistema de inteligencia artificial y automatizacion forense disenado para la orientacion, estructuracion, fundamentacion jurisprudencial y redaccion procesal de Acciones de Tutela y tramites constitucionales en defensa del derecho fundamental a la salud en Colombia (Decreto 2591 de 1991, Decreto 306 de 1992 y jurisprudencia unificada de la Corte Constitucional).

Compatible con entornos de orquestacion autonoma como Hermes, OpenClaw, interfaces de linea de comandos (CLI) y ejecucion directa en Python.

### Integrantes del Proyecto
* **Sergio Aparicio**
* **Juan Diego Leon**

> 📄 **Documento Técnico Oficial:** Para consultar el análisis exhaustivo de arquitectura, motor vectorial, gobernanza HITL, pruebas unitarias y consumo detallado de tokens, accede al [Reporte Técnico Completo (REPORTE_TECNICO.md)](./REPORTE_TECNICO.md).

---


## Indice General y Navegacion por Paginas

* 📄 **[Reporte Técnico Completo (Whitepaper y Token Budget)](./REPORTE_TECNICO.md)**
1. [Pagina 1: Vision General y Fundamento Juridico-Constitucional](#pagina-1-vision-general-y-fundamento-juridico-constitucional)
2. [Pagina 2: Arquitectura Tecnica y Matriz de las 6 Herramientas](#pagina-2-arquitectura-tecnica-y-matriz-de-las-6-herramientas)
3. [Pagina 3: Motor RAG Hibrido y Base de Datos Vectorial SQLite](#pagina-3-motor-rag-hibrido-y-base-de-datos-vectorial-sqlite)
4. [Pagina 4: Estandar Forense de Redaccion Judicial y Exportacion DOCX](#pagina-4-estandar-forense-de-redaccion-judicial-y-exportacion-docx)
5. [Pagina 5: Politica de Seguridad HITL y Privacidad de Datos Sensibles (PHI)](#pagina-5-politica-de-seguridad-hitl-y-privacidad-de-datos-sensibles-phi)
6. [Pagina 6: Estructura del Proyecto](#pagina-6-estructura-del-proyecto)
7. [Pagina 7: Instalacion y Despliegue Automatizado](#pagina-7-instalacion-y-despliegue-automatizado)
8. [Pagina 8: Pruebas Unitarias y Validacion de Integridad](#pagina-8-pruebas-unitarias-y-validacion-de-integridad)
9. [Pagina 9: Integracion con Plataformas Externas (Hermes y OpenClaw)](#pagina-9-integracion-con-plataformas-externas-hermes-y-openclaw)
10. [Pagina 10: Licencia y Responsabilidad Legal](#pagina-10-licencia-y-responsabilidad-legal)

---

## Pagina 1: Vision General y Fundamento Juridico-Constitucional

### 1.1 Declaracion de Mision
AMPARA surge como respuesta a las barreras administrativas, dilaciones indebidas y negativas injustificadas impuestas por Entidades Promotoras de Salud (EPS), gestores farmaceuticos y redes prestadoras en Colombia. Su objetivo es brindar a pacientes, personeros municipales, consultorios juridicos y defensores de derechos humanos una herramienta tecnica rigurosa, inmediata y sustentada en precedente constitucional vinculante.

### 1.2 Marco Normativo Colombiano
El sistema opera bajo estricta sujecion a las normas rectoras del derecho procesal constitucional colombiano:
* **Constitucion Politica de Colombia:** Articulos 1, 2, 11 (Vida), 13 (Igualdad y sujetos de especial proteccion), 23 (Derecho de Peticion), 44, 48, 49 y 86 (Accion de Tutela).
* **Decreto 2591 de 1991:** Reglamentario de la Accion de Tutela. Articulo 7 (Medidas Cautelares Provisionales), Articulo 14 (Informalidad), Articulo 32 (Impugnacion) y Articulo 52 (Incidente de Desacato).
* **Decreto 306 de 1992:** Principios de celeridad, eficacia y tramite preferente de la tutela.
* **Decreto 1382 de 2000 (y Decretos compilatorios posteriores):** Reglas de reparto de la accion de tutela ante la Rama Judicial.
* **Ley Estatutaria 1751 de 2015:** Consagracion de la salud como derecho fundamental autonomo e irrenunciable.
* **Jurisprudencia Hito de la Corte Constitucional:**
  * *Sentencia T-760 de 2008:* Reestructuracion integral del sistema de salud y deberes prestacionales incondicionales.
  * *Sentencia SU-508 de 2020 y SU-1219 de 2001:* Reglas unificadas sobre competencia funcional, procedencia y aplicacion del precedente.

---

## Pagina 2: Arquitectura Tecnica y Matriz de las 6 Herramientas

El agente AMPARA esta estructurado bajo un patron modular de 6 herramientas especializadas y coordinadas por una clase orquestadora (`AmparaAgent` en `agent/agent.py`):

| Numero | Nombre Tecnico | Modulo Python | Descripcion Funcional |
| :---: | :--- | :--- | :--- |
| **Tool 1** | `state_machine_interview` | `agent.tools.interviewer` | Entrevista guiada por maquina de estados finitos. Valida consentimiento, clasifica la legitimacion, audita campos faltantes y detecta riesgo vital. |
| **Tool 2** | `legal_rag_search` | `agent.tools.rag_search` | Motor de recuperacion aumentado por generacion (RAG). Busqueda hibrida (vectorial densa 55% + lexica BM25 45%) sobre base SQLite local. |
| **Tool 3** | `ocr_and_document_parser` | `agent.tools.doc_parser` | Parser estructurado de documentos medicos y procesales para 8 tipologias (formulas, CIE-10, cartas EPS, fallos). Evalua calidad de escaneo. |
| **Tool 4** | `draft_template_engine` | `agent.tools.petition_engine` | Motor forense de redaccion judicial unificada en 12 acapites. Incluye modulo de exportacion a formato Word procesal (`export_petition_to_docx`). |
| **Tool 5** | `case_db_crud` | `agent.tools.case_tracker` | Gestion relacional del expediente digital (SQLite). Monitoreo de lineas de tiempo y calculo perentorio de terminos habiles legales. |
| **Tool 6** | `semantic_compliance_eval` | `agent.tools.compliance` | Auditor semantico de respuestas emitidas por la EPS para identificar evasivas o dilaciones burocraticas y fundamentar Incidentes de Desacato. |

---

## Pagina 3: Motor RAG Hibrido y Base de Datos Vectorial SQLite

### 3.1 Base de Datos Vectorial Autocontenida (`ampara_vector.db`)
A diferencia de arquitecturas tradicionales que requieren dependencias pesadas de terceros o servidores vectoriales en la nube, AMPARA implementa una base de datos vectorial nativa embebida en SQLite (`agent/data/ampara_vector.db`):
* **Modelo de Embeddings Local:** Modelo denso de 256 dimensiones basado en proyecciones deterministas de n-gramas sub-palabra con normalizacion L2, optimizado especificamente para el lexico juridico-sanitario en idioma espanol.
* **Similitud Coseno Integrada:** Funcion matematica de similitud de cosenos evaluada con aceleracion en NumPy.
* **Capacidad Precargada:** 228 fragmentos (*chunks*) juridicos semanticamente etiquetados.

### 3.2 Las 6 Consultas Base Constitucionales (Bateria RAG)
El corpus indexado clasifica la jurisprudencia en 6 nucleos tematicos fundamentales:
1. **Medicamentos y Continuidad:** Principio de continuidad terapeutica, prohibicion de suspension de tratamientos por causas administrativas o de operadores logisticos (ST-207/2007, ST-418/2011, ST-510/2024, ST-540/2002).
2. **Medicamentos No PBS y MIPRES:** Inoponibilidad de tramites burocraticos, justificacion medica e inviabilidad de barreras por costos (ST-001/2018, ST-239/2015, ST-776/2007).
3. **Citas Especializadas y Diagnostico:** Oportunidad en la asignacion de citas, prohibicion de agendas cerradas y derecho al diagnostico expedito (ST-118/2022, ST-507/2024, ST-610/2014, ST-972/2012).
4. **Cirugias, Procedimientos e Integralidad:** Cobertura integral, no fraccionamiento del servicio, suministro de insumos basicos, protesis y enfermeria domiciliaria (ST-445/2023, ST-742/2017, ST-399/2023, ST-167/2025, ST-023/2013).
5. **Sujetos de Especial Proteccion y Riesgo Vital:** Prevalencia para pacientes oncologicos, ninos, adultos mayores y personas en situacion de discapacidad (ST-1077/2012, ST-121/2007, ST-407/2024, ST-323/2007, ST-377/2012).
6. **Transporte, Viaticos y Barreras de Acceso:** Gastos de desplazamiento intermunicipal, alojamiento y acompanante para pacientes vulnerables (ST-122/2021, ST-528/2025, ST-461/2025).

---

## Pagina 4: Estandar Forense de Redaccion Judicial y Exportacion DOCX

### 4.1 La Estructura Procesal Unificada de 12 Acapites
Toda accion de tutela generada por el agente responde al estandar forense unificado de practica judicial ante jueces de la Republica:
1. **Encabezamiento y Designacion Judicial:** Competencia territorial y funcional del juez constitucional.
2. **Identificacion y Legitimacion en la Causa:** Determinacion precisa de actuar a titulo propio, por representacion legal o mediante agencia oficiosa procesal.
3. **Accionados y Vinculados en Garantia:** Identificacion de la EPS, IPS tratante, ADRES y Secretaria de Salud.
4. **Declaracion de Derechos Fundamentales Conculcados:** Determinacion de garantias vulneradas (vida digna, salud, seguridad social, integridad).
5. **Acapite Especial de Medidas Cautelares Provisionales de Urgencia:** Solicitud motivada bajo el Articulo 7 del Decreto 2591 de 1991 (plazo perentorio de 4 horas para entrega de medicamentos o programacion de intervenciones vitales).
6. **Fundamentos Facticos (Hechos):** Narrativa cronologica rigurosa, desglosada y numerada.
7. **Concepto de Violacion y Argumentacion Juridica:** Subuncion juridica vinculando los hechos con la ratio decidendi de la Corte Constitucional.
8. **Pretensiones Principales y Conexas:** Solicitudes concretas de proteccion inmediata y ordenes de hacer para la EPS.
9. **Principio de Tratamiento Integral:** Exigencia de cobertura total frente a patologias derivadas y futuras ordenes medicas.
10. **Sustentacion Probatoria:** Relacion documental de formulas medicas, historias clinicas y constancias de negativa.
11. **Juramento de No Presentacion Previa (Articulo 37):** Manifestacion solemne sobre ausencia de temeridad procesal.
12. **Notificaciones y Cierre:** Direcciones electronicas y fisicas de las partes para recepcion de autos y fallos.

### 4.2 Exportador Procesal a Microsoft Word (`export_petition_to_docx`)
La herramienta compila el memorial directamente a documentos ejecutables `.docx` cumpliendo las pautas tipograficas forenses colombianas: margenes reglamentarias de 2.54 cm, tipografia Arial procesal, interlineado de 1.15, encabezados institucionales y linea de firma formal. Los archivos se depositan en el directorio `tutelas_generadas/`.

---

## Pagina 5: Politica de Seguridad HITL y Privacidad de Datos Sensibles (PHI)

AMPARA implementa salvaguardas eticas de proteccion al usuario y cumplimiento de la Ley 1581 de 2012 (Habeas Data):

```text
[Interaccion Usuario]
         |
         v
[Nodo 1: Consentimiento Expreso PHI] ---> Si no consiente, detiene el procesamiento
         |
         v
[Nodo 2: Evaluacion de Riesgo Vital] ---> Si detecta riesgo critico, activa bandera HITL
         |
         v
[Nodo 3: Generacion del Memorial]
         |
         v
[Nodo 4: Revision Humana Obligatoria (HITL)] ---> Exige validacion por abogado o usuario
```

* **Human-in-the-Loop (HITL) Obligatorio:** Ningun memorial juridico es radicado automaticamente. Todo documento final se clasifica con la propiedad `human_review_required: true` para revision final del usuario o abogado patrocinador.
* **Escalamiento Vital de Emergencia:** Ante diagnosticos oncologicos, necesidades de dialisis, intervenciones cardiovasculares o urgencias criticas, la maquina de estados activa la alerta de prioridad inmediata y orienta al usuario para acudir a centros de urgencias de forma simultanea.

---

## Pagina 6: Estructura del Proyecto

```text
AMPARA/
├── .hermes/                 # Especificacion para orquestador Hermes
├── .opencode/               # Especificacion para entorno OpenClaw
├── agent/                   # Codigo fuente nuclear del agente
│   ├── core/                # Motor de embeddings y base vectorial SQLite
│   │   ├── __init__.py
│   │   └── vector_db.py     # SQLiteVectorDB y DenseEmbeddingModel
│   ├── data/                # Base vectorial y corpus normativo
│   │   ├── ampara_vector.db # Base de datos vectorial pre-indexada (SQLite)
│   │   ├── legal_corpus/    # Corpus en Markdown (Decretos y Sentencias)
│   │   └── raw_documents/   # Documentos originales
│   ├── tests/               # Bateria de 38 pruebas unitarias automatizadas
│   ├── tools/               # Matriz de las 6 herramientas operativas
│   │   ├── interviewer/     # Tool 1: Maquina de estados y grafo
│   │   ├── rag_search.py    # Tool 2: Legal RAG hibrido
│   │   ├── doc_parser.py    # Tool 3: Analizador de documentos medicos
│   │   ├── petition_engine.py # Tool 4: Generador de tutelas y DOCX
│   │   ├── case_tracker.py  # Tool 5: Base de casos y plazos legales
│   │   └── compliance.py    # Tool 6: Auditor semantico de desacato
│   ├── agent.py             # Clase orquestadora principal (AmparaAgent)
│   ├── main.py              # Punto de entrada y demo de herramientas
│   ├── manifest.json        # Manifiesto JSONSchema oficial de herramientas
│   └── SOUL.md              # System Prompt oficial y reglas deontologicas
├── skills/                  # Empaquetado estandar de habilidades
├── tutelas_generadas/       # Salida automatica de documentos Word (.docx)
├── deploy.ps1               # Script de despliegue automatizado para Windows
├── deploy.sh                # Script de despliegue automatizado para Linux/macOS
├── hermes_manifest.json     # Manifiesto raiz de interoperabilidad
├── main.py                  # Script ejecutable de demostracion integral
├── README.md                # Documentacion principal del repositorio
├── REPORTE_TECNICO.md       # Reporte tecnico exhaustivo, arquitectura y token budget
└── requirements.txt         # Especificacion de dependencias Python
```

---

## Pagina 7: Instalacion y Despliegue Automatizado

### 7.1 Requisitos del Sistema
* Python 3.11 o Python 3.12 instalado.
* Sistema Operativo: Windows 10/11, Ubuntu/Debian/Fedora o macOS 12+.

### 7.2 Opcion A: Despliegue Automatizado en Windows (PowerShell)
Ejecute el script de automatizacion incluido en la raiz:
```powershell
# En una consola de PowerShell dentro de la carpeta del proyecto:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\deploy.ps1
```
El script creara el entorno virtual `.venv`, instalara las dependencias, verificara la base vectorial SQLite y ejecutara la demostracion de las 6 herramientas.

### 7.3 Opcion B: Despliegue Automatizado en Linux o macOS (Bash)
Otorgue permisos de ejecucion y ejecute el script:
```bash
chmod +x deploy.sh
./deploy.sh
```

### 7.4 Opcion C: Instalacion Manual Paso a Paso
```bash
# 1. Crear entorno virtual
python -m venv .venv

# 2. Activar entorno virtual
# En Windows:
.\.venv\Scripts\activate
# En Linux/macOS:
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

---

## Pagina 8: Pruebas Unitarias y Validacion de Integridad

El proyecto cuenta con una cobertura integral de pruebas unitarias que validan la maquina de estados, el motor de embeddings, el RAG hibrido, el parser de documentos, el generador forense y el auditor semantico.

### 8.1 Ejecutar la Suite de Pruebas
Desde la raiz del proyecto:
```bash
python -m unittest discover -s agent/tests
```
**Resultado esperado:**
```text
Ran 38 tests in 0.8s
OK
```

### 8.2 Ejecutar la Demostracion Integral
Para presenciar la ejecucion coordinada de las 6 herramientas simulando un caso real de negacion de medicamento oncologico:
```bash
python main.py
```

El script validara:
1. Consentimiento de datos (Tool 1).
2. Clasificacion de urgencia vital oncologica (Tool 1).
3. Extraccion de entidades de formula medica con score de calidad (Tool 3).
4. Recuperacion jurisprudencial de medidas provisionales en SQLite (Tool 2).
5. Ensamblado de la tutela con medidas cautelares en 12 acapites (Tool 4).
6. Apertura del expediente judicial y calculo perentorio de 10 dias de fallo (Tool 5).
7. Evaluacion de respuesta dilatoria de la EPS y recomendacion de Desacato (Tool 6).

---

## Pagina 9: Integracion con Plataformas Externas (Hermes y OpenClaw)

### 9.1 Plataforma Hermes
El archivo `hermes_manifest.json` y `agent/manifest.json` definen los contratos formales JSONSchema para las 6 herramientas. Hermes importa este manifiesto directamente permitiendo al modelo orquestador invocar las funciones como *tool calls* de forma estructurada.

### 9.2 Entorno OpenClaw
El archivo `.opencode/agent/ampara.md` contiene la definicion de identidad, contexto y asignacion de herramientas para su consumo directo por el motor de OpenClaw.

### 9.3 Uso Directo como Paquete Python
```python
from agent.agent import AmparaAgent

# Instanciar el agente
agente = AmparaAgent()

# 1. Entrevista interactiva
respuesta = agente.interview("La EPS me nego la cirugia de reemplazo de cadera")
print("Fase actual:", respuesta["current_state"])

# 2. Consulta jurisprudencial RAG
jurisprudencia = agente.search_legal_knowledge(
    query="principio de integralidad cirugia cadera",
    top_k=3
)
print("Fuentes encontradas:", jurisprudencia["total_found"])
```

---

## Pagina 10: Licencia y Responsabilidad Legal

### 10.1 Descargo de Responsabilidad Legal (Disclaimer)
AMPARA es una herramienta de asistencia tecnica y generacion documental juridica basada en inteligencia artificial. Su uso no constituye asesoria juridica formal ni reemplaza el criterio, patrocinio o intervencion obligatoria de un profesional del derecho debidamente acreditado. Todo documento generado debe ser sometido a control y aprobacion humana previa a su radicacion ante despachos judiciales.

### 10.2 Licencia
Este proyecto se distribuye bajo los terminos de la **Licencia MIT**. Consulte los terminos de distribucion y uso academico o profesional para mas detalles.

### 10.3 Integrantes y Autores
* **Sergio Aparicio**
* **Juan Diego Leon**

