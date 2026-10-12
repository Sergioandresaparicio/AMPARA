# REPORTE TÉCNICO: SISTEMA AGÉNTICO AMPARA
## Asistente Jurídico Autónomo en Salud y Tutelas para Colombia

---

**Autores:**  
* **Sergio Aparicio**  
* **Juan Diego León**  

**Proyecto:** AMPARA (*Asistencia y Modelado Procesal Autónomo para Reclamaciones y Amparos*)  
**Versión del Sistema:** 1.0.0  
**Fecha de Publicación:** Octubre de 2026  
**Clasificación:** LegalTech / HealthTech / Agentes Autónomos de Inteligencia Artificial  
**Licencia:** MIT  

---

## Resumen (Abstract)

Este reporte técnico documenta el diseño, la arquitectura de software, la base matemática-vectorial, los protocolos de gobernanza ética y la validación experimental de **AMPARA**, un agente de inteligencia artificial autónomo especializado en la defensa del derecho fundamental a la salud en Colombia. Diseñado conforme a la Constitución Política de 1991, la Ley Estatutaria 1751 de 2015 y los Decretos 2591 de 1991 y 306 de 1992, AMPARA automatiza de extremo a extremo la recolección fáctica mediante una máquina de estados finitos, la extracción estructurada de documentos médicos, la recuperación aumentada por generación (RAG) sobre un corpus jurisprudencial constitucional embebido en SQLite, la redacción forense en 12 acápites procesales con exportación directa a Microsoft Word (.docx), el seguimiento perentorio de términos judiciales y la auditoría semántica de cumplimiento de fallos para la estructuración de Incidentes de Desacato. 

El sistema implementa un modelo de representación semántica vectorial denso de 256 dimensiones completamente local y determinista, libre de dependencias hacia servidores vectoriales externos en la nube o GPUs dedicadas. Además, incorpora una política estricta de revisión humana obligatoria (*Human-In-The-Loop* - HITL), enmascaramiento de información médica sensible (PHI) conforme a la Ley 1581 de 2012 y detección prioritaria de riesgo vital crítico con activación de medidas cautelares provisionales de urgencia. La solución ha sido validada experimentalmente con una suite de 38 pruebas unitarias automatizadas con 100% de tasa de éxito en menos de 1 segundo de ejecución.

---

## Tabla de Contenidos

1. [1. Introducción y Planteamiento del Problema](#1-introducción-y-planteamiento-del-problema)
2. [2. Marco Normativo y Fundamentación Constitucional](#2-marco-normativo-y-fundamentación-constitucional)
3. [3. Arquitectura General del Sistema y Orquestación Agéntica](#3-arquitectura-general-del-sistema-y-orquestación-agéntica)
4. [4. Matriz de Herramientas Especializadas (Toolchain)](#4-matriz-de-herramientas-especializadas-toolchain)
5. [5. Motor RAG Híbrido y Base Vectorial Embebida](#5-motor-rag-híbrido-y-base-vectorial-embebida)
6. [6. Motor de Redacción Forense y Compilación Documental DOCX](#6-motor-de-redacción-forense-y-compilación-documental-docx)
7. [7. Gobernanza, Seguridad de Datos Sensibles (PHI) y Protocolo HITL](#7-gobernanza-seguridad-de-datos-sensibles-phi-y-protocolo-hitl)
8. [8. Evaluación Experimental y Resultados de Pruebas Unitarias](#8-evaluación-experimental-y-resultados-de-pruebas-unitarias)
9. [9. Estimación y Modelado del Consumo de Tokens (Token Budget)](#9-estimación-y-modelado-del-consumo-de-tokens-token-budget)
10. [10. Especificaciones de Despliegue e Interoperabilidad](#10-especificaciones-de-despliegue-e-interoperabilidad)
11. [11. Limitaciones, Análisis de Riesgos y Trabajo Futuro](#11-limitaciones-análisis-de-riesgos-y-trabajo-futuro)
12. [12. Conclusiones](#12-conclusiones)
13. [13. Referencias Normativas y Jurisprudenciales](#13-referencias-normativas-y-jurisprudenciales)

---

## 1. Introducción y Planteamiento del Problema

El Sistema General de Seguridad Social en Salud (SGSSS) de Colombia enfrenta tensiones estructurales caracterizadas por barreras administrativas, negación de insumos médicos, demoras sistemáticas en la autorización de procedimientos de alta complejidad y suspensión arbitraria de tratamientos farmacológicos continuos. Históricamente, la **Acción de Tutela** (consagrada en el Artículo 86 de la Constitución y reglamentada por el Decreto 2591 de 1991) ha sido el principal instrumento ciudadano para salvaguardar la vida y la integridad física.

Sin embargo, los ciudadanos y los operadores jurídicos (personerías, defensorías y consultorios jurídicos) enfrentan tres cuellos de botella críticos:
1. **Asimetría técnica y fáctica:** Dificultad para estructurar cronologías de hechos clínicos coherentes a partir de documentos desordenados (fórmulas manuscritas, órdenes MIPRES, epicrisis).
2. **Dispersión jurisprudencial:** Necesidad de fundamentar peticiones en precedentes vinculantes de la Corte Constitucional (diferenciando medicamentos PBS de No PBS, reglas de continuidad y sujetos de especial protección constitucional).
3. **Complejidad procesal post-fallo:** Ineficacia ante respuestas evasivas o dilatorias de las EPS tras órdenes judiciales, lo que requiere la formulación inmediata y rigurosa de Incidentes de Desacato.

**AMPARA** fue concebido como una solución técnica y forense autónoma que abate estas barreras, garantizando rigor jurídico, trazabilidad de términos legales y protección estricta de la dignidad y privacidad del paciente.

---

## 2. Marco Normativo y Fundamentación Constitucional

El diseño lógico y operacional de AMPARA no responde a modelos genéricos de procesamiento de texto, sino a reglas estrictas del derecho procesal constitucional colombiano:

* **Constitución Política de Colombia (1991):**
  * *Art. 11:* Derecho fundamental e inviolable a la vida.
  * *Art. 13:* Cláusula de igualdad real y protección especial a sujetos en situación de debilidad manifiesta (niños, adultos mayores, pacientes oncológicos, personas en situación de discapacidad).
  * *Art. 48 y 49:* Garantía de la seguridad social y atención integral en salud.
  * *Art. 86:* Acción de Tutela como mecanismo preferente y sumario.
* **Ley Estatutaria 1751 de 2015:**
  * Consagración de la salud como derecho fundamental autónomo e irrenunciable.
  * Principio de integralidad y prohibición de fragmentación del servicio.
* **Decreto 2591 de 1991:**
  * *Artículo 7:* Medidas Cautelares Provisionales de Urgencia (suspensión inmediata del acto u orden perentoria para evitar perjuicios irremediables).
  * *Artículo 14:* Principio de informalidad procesal.
  * *Artículo 32:* Trámite expedito de impugnación (3 días hábiles).
  * *Artículo 37:* Régimen de competencia y juramento de no presentación previa.
  * *Artículo 52:* Incidente de Desacato y sanciones disciplinarias/arresto ante incumplimiento.
* **Jurisprudencia Hito de la Corte Constitucional:**
  * *Sentencia T-760 de 2008:* Mandatos estructurales al sistema de salud y principio de continuidad.
  * *Sentencia SU-508 de 2020:* Reglas unificadas sobre procedibilidad, subsidiariedad y asignación de competencias.

---

## 3. Arquitectura General del Sistema y Orquestación Agéntica

El sistema AMPARA se estructura como un agente autónomo determinista guiado por herramientas (*tool-augmented agent*). La orquestación central reside en la clase `AmparaAgent` (`agent/agent.py`), coordinada mediante metadatos estandarizados en `manifest.json` y directrices deontológicas fijadas en `SOUL.md`.

```
                  ┌──────────────────────────────────────────────┐
                  │               USUARIO / PACIENTE             │
                  └──────────────────────┬───────────────────────┘
                                         │ Lenguaje Natural / Documentos
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │             ORQUESTADOR AMPARA               │
                  │    (AmparaAgent / Hermes / OpenClaw / CLI)   │
                  └──────┬───────────────┬───────────────┬───────┘
                         │               │               │
        ┌────────────────┴─┐      ┌──────┴────────┐      │
        ▼                  ▼      ▼               ▼      ▼
┌───────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────────┐
│   Tool 1      │ │   Tool 2    │ │   Tool 3    │ │   Tool 4    │ │   Tool 5 / 6   │
│ Máquina de    │ │ RAG Híbrido │ │ OCR & Doc   │ │ Redacción   │ │ Case Tracker & │
│ Estados (FSM) │ │ SQLite 256d │ │ Parser      │ │ Forense DOCX│ │ Compliance     │
└───────┬───────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └───────┬────────┘
        │                │               │               │                │
        └────────────────┼───────────────┼───────────────┼────────────────┘
                         ▼               ▼               ▼
                  ┌──────────────────────────────────────────────┐
                  │   CAPA DE GOBERNANZA, PHI & INTERRUPT NODES  │
                  │   - Consentimiento Informado (Ley 1581)      │
                  │   - Detección de Riesgo Vital (4 Horas)      │
                  │   - Revisión Humana Obligatoria (HITL)       │
                  └──────────────────────┬───────────────────────┘
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │      PRODUCTO FORENSE FINAL (DOCX / DB)      │
                  │       (Radicación asistida / Expediente)     │
                  └──────────────────────────────────────────────┘
```

### Características del Motor de Orquestación:
1. **Entrada y Salida Desacoplada:** El agente puede ejecutarse mediante línea de comandos interactiva (`main.py`), llamada programática Python, o en plataformas agénticas como *Hermes* y *OpenClaw*.
2. **Telemetría de Auditoría S4:** Registro de eventos en formato JSON sin supervisión (`S4_UNATTENDED_JSON`), registrando trazas de herramientas invocadas, latencias, fuentes jurisprudenciales citadas y estado de interrupciones HITL.

---

## 4. Matriz de Herramientas Especializadas (Toolchain)

AMPARA implementa un pipeline de seis herramientas altamente cohesivas y desacopladas:

| Herramienta | Módulo Python | Función Operativa Principal |
| :--- | :--- | :--- |
| **Tool 1: `state_machine_interview`** | `agent.tools.interviewer` | Entrevista clínica-jurídica estructurada mediante una Máquina de Estados Finitos (FSM). Extrae hechos, valida legitimación en la causa y calcula riesgo vital. |
| **Tool 2: `legal_rag_search`** | `agent.tools.rag_search` | Motor RAG de doble vía (vectorial + léxica) que consulta una base de conocimiento constitucional precargada en SQLite. |
| **Tool 3: `ocr_and_document_parser`** | `agent.tools.doc_parser` | Parser estructurado de documentos sanitarios para 8 tipologías distintas (fórmulas, órdenes MIPRES, historias clínicas, cartas de negación). |
| **Tool 4: `draft_template_engine`** | `agent.tools.petition_engine` | Motor generador de memoriales judiciales según el estándar forense unificado de 12 acápites. Incluye el compilador a DOCX. |
| **Tool 5: `case_db_crud`** | `agent.tools.case_tracker` | Gestor relacional de expedientes (SQLite). Computa de forma estricta términos perentorios judiciales en días hábiles. |
| **Tool 6: `semantic_compliance_eval`** | `agent.tools.compliance` | Auditor semántico de respuestas emitidas por la EPS para identificar evasivas o dilaciones y fundamentar Incidentes de Desacato. |

### Detalle Operativo de Componentes Críticos

#### FSM de la Entrevista (Tool 1)
Gestiona un ciclo de 5 estados:
* `CONSENT`: Validación de consentimiento informado para tratamiento de datos personales sensibles (PHI).
* `CLASSIFICATION`: Determinación de legitimación en la causa (nombre propio, representante legal o agente oficioso ante imposibilidad física/mental).
* `COLLECTION`: Recolección exhaustiva de hechos, EPS accionada, patología y fechas de solicitud.
* `RISK`: Ponderación de riesgo vital inminente (patologías oncológicas, hemodiálisis, UCI).
* `COMPLETED`: Consolidación del expediente para habilitar la generación del memorial.

#### Auditor de Respuestas EPS y Desacato (Tool 6)
Evalúa las respuestas de las entidades demandadas cruzándolas con un catálogo de pretextos administrativos prohibidos por la Corte Constitucional:
* *Excusas de inventario:* "Medicamento agotado en dispensario" o "sin existencias".
* *Trámites de comités internos:* "Pendiente aprobación de Junta Médica / MIPRES".
* *Ruptura de red prestadora:* "IPS fuera de convenio vigente".
* *Re-trámites forzados:* "Solicite nueva cita para renovar fórmula vencida".

Si el nivel de cumplimiento cae en `EVASIVE_DILATORY` o `OUTRIGHT_DENIAL`, la herramienta estructura automáticamente el memorial de **Incidente de Desacato** (Art. 52, Decreto 2591/1991).

---

## 5. Motor RAG Híbrido y Base Vectorial Embebida

### 5.1 Base de Datos Vectorial Local (`ampara_vector.db`)
Para garantizar autonomía operativa, baja latencia y cero costos por llamadas a APIs vectoriales externas, AMPARA utiliza almacenamiento SQLite local optimizado con funciones de similitud matemática en NumPy:

* **Almacenamiento:** Archivo binario relacional `agent/data/ampara_vector.db`.
* **Corpus Indexado:** 228 fragmentos jurídicos (*chunks*) seleccionados de la jurisprudencia de la Corte Constitucional.
* **Baterías Temáticas Indexadas:**
  1. *Medicamentos y Continuidad Terapéutica* (ST-207/2007, ST-418/2011, ST-510/2024).
  2. *Medicamentos No PBS y MIPRES* (ST-001/2018, ST-239/2015, ST-776/2007).
  3. *Citas Especializadas y Diagnóstico Oportuno* (ST-118/2022, ST-507/2024, ST-610/2014).
  4. *Cirugías, Procedimientos e Integralidad* (ST-445/2023, ST-742/2017, ST-167/2025).
  5. *Sujetos de Especial Protección y Riesgo Vital* (ST-1077/2012, ST-407/2024).
  6. *Transporte, Viáticos y Acompañante* (ST-122/2021, ST-528/2025).

### 5.2 Modelo de Embeddings: `DenseEmbeddingModel`
En lugar de depender de transformadores con pesos de gigabytes, AMPARA implementa un modelo de proyección determinista denso de **256 dimensiones**:
* **Representación:** Vector de coma flotante de 32 bits ($d = 256$).
* **Extracción de Características:** Proyecciones de palabras completas y n-gramas sub-palabra (de 3 a 5 caracteres) mediante dispersión determinista (hashing MD5) con modulación de signos.
* **Invarianza Lingüística:** Normalización tipográfica (remoción de tildes y diacríticos en español).
* **Normalización:** Proyección euclidiana $L_2$:
  $$\mathbf{v}_{\text{norm}} = \frac{\mathbf{v}}{\|\mathbf{v}\|_2}$$

### 5.3 Similitud Coseno Vectorial
La búsqueda recupera los $k$ documentos más cercanos maximizando:
$$\text{Similitud}(\mathbf{a}, \mathbf{b}) = \frac{\mathbf{a} \cdot \mathbf{b}}{\|\mathbf{a}\| \|\mathbf{b}\|}$$
Acelerada directamente con operaciones vectorizadas de álgebra lineal en NumPy.

### 5.4 Esquema Híbrido de Ranking
La recuperación combina similitud semántica densa ($55\%$) y coincidencia léxica exacta/BM25 ($45\%$), minimizando las alucinaciones y asegurando que las sentencias citadas sean numéricamente exactas y vigentes.

---

## 6. Motor de Redacción Forense y Compilación Documental DOCX

### 6.1 Estándar Forense Unificado de 12 Acápites
Toda acción judicial generada por AMPARA responde al esquema riguroso exigido en los despachos judiciales de la República de Colombia:
1. **Encabezamiento y Asignación de Competencia:** Determinación territorial y funcional según reglas de reparto (Decreto 1382/2000).
2. **Identificación y Legitimación en la Causa:** Postulación a título personal, representación legal de menores o agencia oficiosa.
3. **Accionados y Vinculados:** Individualización de la EPS, IPS tratante, Secretaría de Salud y ADRES en garantía de recobro.
4. **Derechos Fundamentales Invocados:** Vida digna, salud como derecho fundamental autónomo, seguridad social e integridad física.
5. **Acápite Especial de Medidas Cautelares Provisionales:** Invocación expresa del Art. 7 del Decreto 2591/1991 cuando existe riesgo vital inminente (plazo perentorio de 4 a 24 horas).
6. **Fundamentos Fácticos (Hechos):** Narrativa cronológica, numerada y verificable.
7. **Concepto de Violación y Fundamento Jurídico:** Subsunción del caso en la *ratio decidendi* de las sentencias unificadas de la Corte Constitucional.
8. **Pretensiones Principales y Accesorias:** Órdenes de dar o hacer concretas dirigidas a la entidad demandada.
9. **Principio de Tratamiento Integral:** Solicitud explícita para evitar futuras dilaciones sobre derivaciones de la patología.
10. **Acreditación Probatoria:** Relación discriminada de anexos documentales (fórmulas, MIPRES, historias clínicas).
11. **Juramento de Temeridad:** Declaración solemne bajo juramento de no haber interpuesto otra tutela por los mismos hechos (Art. 37, D. 2591/1991).
12. **Notificaciones y Cierre:** Canales de comunicación físicos y digitales de demandante y demandados.

### 6.2 Exportación Procesal a Word (`export_petition_to_docx`)
La herramienta compila el documento directamente a formato `.docx` ejecutable mediante la librería `python-docx`:
* **Tipografía Forense:** Arial procesal a 11 puntos.
* **Márgenes:** 2.54 cm en todos los márgenes conforme a la regla judicial.
* **Interlineado:** 1.15 con espaciado posterior de 6 puntos.
* **Estructura Estilizada:** Títulos y subtítulos en negrita y mayúsculas sostenidas, párrafos justificados y espacio formal de firma con documento de identidad.

---

## 7. Gobernanza, Seguridad de Datos Sensibles (PHI) y Protocolo HITL

La protección de los usuarios es un pilar arquitectónico no negociable en AMPARA, regulado bajo la sección `governance` de su manifiesto:

### 7.1 Protección de Datos Personales (Habeas Data)
En estricto cumplimiento de la **Ley Estatutaria 1581 de 2012** y la **Ley 1751 de 2015**:
* Los diagnósticos clínicos, números de identificación y nombres se tratan como información médica sensible (*Protected Health Information* - PHI).
* En entornos de prueba o telemetría pública, el sistema activa tokenización preventiva automática (`[PACIENTE_X]`, `[CEDULA_X]`, `[EPS_X]`).

### 7.2 Los Tres Nodos de Interrupción Obligatorios (*Interrupt Nodes*)
AMPARA cuenta con puntos de control de ejecución estricta:

```
[Inicio de Sesión]
       │
       ▼
 [¿Consentimiento Otorgado?] ──NO──► [INTERRUPT_CONSENT_PHI] ──► (Bloqueo hasta aceptación)
       │ SÍ
       ▼
 [¿Riesgo Vital Inminente?]  ──SÍ──► [INTERRUPT_CRITICAL_VITAL_RISK] ──► (Priorizar Cautelares 4h)
       │ NO
       ▼
 [Memorial Generado] ──────────────► [INTERRUPT_HUMAN_REVIEW_DRAFT]  ──► (Pausa obligatoria para
                                                                          firma del ciudadano)
```

1. **`INTERRUPT_CONSENT_PHI`:** Ningún procesamiento de documentos clínicos se ejecuta si la bandera `consent_status != 'GRANTED'`.
2. **`INTERRUPT_CRITICAL_VITAL_RISK`:** Se dispara ante patologías críticas (cáncer, falla renal aguda, requerimiento de UCI), obligando al agente a estructurar de manera prioritaria Medidas Cautelares de urgencia vital.
3. **`INTERRUPT_HUMAN_REVIEW_DRAFT`:** Todo memorial generado se emite con la bandera `human_review_required: true`. El agente prohíbe explícitamente radicar acciones sin la previa lectura, validación fáctica y firma manuscrita o digital del titular o su apoderado.

---

## 8. Evaluación Experimental y Resultados de Pruebas Unitarias

La integridad operativa del sistema se audita mediante una suite de pruebas unitarias automatizada implementada sobre el framework nativo `unittest` de Python.

### 8.1 Resultados de la Ejecución de Pruebas

```bash
python -m unittest discover -s agent/tests
```

**Resultado Consolidado:**
* **Total de Casos de Prueba Ejecutados:** 38
* **Pruebas Superadas Exitosamente:** 38 (100%)
* **Fallos / Errores:** 0
* **Tiempo Total de Ejecución:** **0.860 segundos**

### 8.2 Desglose de Cobertura por Módulo

| Módulo de Prueba | Componente Auditado | Casos | Estado | Cobertura Funcional |
| :--- | :--- | :---: | :---: | :--- |
| `test_interviewer.py` | Tool 1 (`state_machine_interview`) | 6 | **PASS** | Transición de estados FSM, rechazo de consentimiento, extracción de hechos y captura de riesgo vital. |
| `test_rag_search.py` | Tool 2 (`legal_rag_search`) | 5 | **PASS** | Búsqueda semántica en las 6 baterías temáticas y filtrado por tipo de fuente. |
| `test_vector_db.py` | Motor de Embeddings y SQLite | 4 | **PASS** | Determinismo de `DenseEmbeddingModel`, ortogonalidad vectorial y similitud coseno en NumPy. |
| `test_doc_parser.py` | Tool 3 (`ocr_and_document_parser`) | 7 | **PASS** | Detección de tipos documentales, extracción de CIE-10 y tolerancia ante texto degradado. |
| `test_petition_engine.py`| Tool 4 (`draft_template_engine` & DOCX) | 7 | **PASS** | Presencia estricta de los 12 acápites procesales, medidas cautelares y compilación de archivo Word. |
| `test_case_tracker.py` | Tool 5 (`case_db_crud`) | 5 | **PASS** | Operaciones CRUD sobre expediente SQLite y cómputo de términos legales en días hábiles. |
| `test_compliance.py` | Tool 6 (`semantic_compliance_eval`) | 4 | **PASS** | Detección de patrones evasivos de EPS y estructuración de Incidente de Desacato. |
| **Total Global** | **Suite Completa de AMPARA** | **38** | **PASS** | **100% de operatividad verificada** |

### 8.3 Métricas de Rendimiento Técnico

* **Consumo de Memoria RAM:** Menor a 85 MB durante la ejecución completa con la base vectorial cargada.
* **Tiempo Medio de Generación por Tutela:** $\approx 140\text{ ms}$ (incluyendo búsqueda RAG y compilación DOCX).
* **Falsos Negativos en Riesgo Vital:** $0\%$ en la suite de validación (todas las patologías de alto costo activaron la alerta crítica de forma determinista).

---

## 9. Estimación y Modelado del Consumo de Tokens (Token Budget)

El dimensionamiento del consumo de tokens es un factor crítico para evaluar la viabilidad operacional, la latencia de inferencia y la estructura de costos de AMPARA al integrarse con Modelos de Lenguaje Grande (LLMs) mediante Hermes, OpenClaw o servidores MCP.

### 9.1 Metodología de Medición y Tokenización
Debido a que el sistema opera en español técnico-sanitario y jurídico procesal, se aplicó la tasa de compresión empírica de tokenizadores BPE multilingües modernos (*Byte-Pair Encoding*, estándar en familias OpenAI cl100k_base / o200k_base, Google Gemini y Meta Llama 3). En este dominio léxico, el factor de conversión medido experimentalmente sobre el corpus de AMPARA es de **1.30 tokens por palabra** (equivalente a una densidad promedio de **3.8 a 4.0 caracteres por token**).

### 9.2 Desglose de Tokens por Componente del Sistema

A partir del análisis cuantitativo directo del código fuente, el manifiesto y una ejecución de caso real (paciente oncológico con requerimiento de medicamento de alto costo y riesgo vital), se determinaron las siguientes métricas exactas por componente:

| Componente del Sistema | Archivo / Función | Caracteres | Palabras | Tokens Estimados | Rol en el LLM |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **System Prompt (Identidad y Deontología)** | `SOUL.md` | 2,632 | 366 | **~475** | Entrada (*Input*) fijo de sistema |
| **Esquema de Herramientas (Tool Schemas)** | `manifest.json` (6 tools) | 13,898 | 1,220 | **~1,586** | Entrada (*Input*) contexto de herramientas |
| **Entrevista FSM (5 turnos de diálogo)** | `state_machine_interview` | 527 | 82 | **~106 – 350** | Entrada / Salida conversacional |
| **Análisis de Documento Médico (OCR/Parser)** | `ocr_and_document_parser` | 2,076 | 227 | **~295 – 650** | Entrada contextual del expediente |
| **Contexto Jurisprudencial RAG (Top-3 Chunks)**| `legal_rag_search` | 3,693 | 537 | **~698 – 950** | Entrada contextual recuperada |
| **Memorial Judicial (12 Acápites Forenses)** | `draft_template_engine` | 10,480 | 1,494 | **~1,942 – 2,500** | Generación final (*Output*) |
| **Auditoría Semántica de Cumplimiento / Desacato**| `semantic_compliance_eval` | 1,347 | 162 | **~210 – 450** | Evaluación post-fallo |

### 9.3 Ciclo de Vida y Presupuesto Total por Caso (*Lifecycle Token Budget*)

En una interacción ordinaria de extremo a extremo, el consumo se distribuye según la fase procesal:

#### Flujo A: Generación de Acción de Tutela con Medidas Cautelares (Caso Completo)
* **Tokens de Entrada (*Prompt Tokens*):**
  * System Prompt (`SOUL.md`): ~475 tokens
  * Declaración de Herramientas en Contexto: ~1,586 tokens
  * Historial acumulado de entrevista: ~350 tokens
  * Extracto estructurado de documentos clínicos (fórmulas/MIPRES): ~350 tokens
  * Precedente jurisprudencial inyectado por RAG: ~700 tokens
  * *Subtotal Entrada:* **~3,460 a 4,200 tokens**.
* **Tokens de Salida (*Completion Tokens*):**
  * Mensajes intermedios y llamadas a herramientas (JSON): ~250 a 400 tokens
  * Redacción completa del memorial judicial en 12 acápites: ~1,942 a 2,500 tokens
  * *Subtotal Salida:* **~2,190 a 2,900 tokens**.
* **Total por Tutela Radicable:** **~5,650 a 7,100 tokens**.

#### Flujo B: Trámite Posterior de Incidente de Desacato
* **Tokens de Entrada:** Petición original/fallo judicial + respuesta evasiva de EPS + contexto normativo: **~1,500 a 2,300 tokens**.
* **Tokens de Salida:** Dictamen de cumplimiento y memorial procesal de desacato (Art. 52, Decreto 2591/1991): **~1,100 a 1,700 tokens**.
* **Total por Desacato:** **~2,600 a 4,000 tokens**.

### 9.4 Eficiencia de Costos y Ahorro por Arquitectura Local

Una ventaja arquitectónica decisiva de AMPARA es que su motor de embeddings (`DenseEmbeddingModel`) y su base vectorial SQLite operan **100% de manera local en CPU**. Esto significa que:
1. **Cero Tokens de Embedding Facturables:** El cálculo de representaciones vectoriales para los 228 fragmentos y las consultas no consume tokens de APIs de embeddings comerciales.
2. **Costo Marginal Mínimo por Tutela:**
   * **Con Modelos Eficientes (ej. Gemini 1.5 Flash / GPT-4o-mini):** Entre **$0.0015 y $0.0035 USD** por tutela integral (aproximadamente **$6 a $15 pesos colombianos - COP**).
   * **Con Modelos de Frontera (ej. GPT-4o / Claude 3.5 Sonnet):** Entre **$0.025 y $0.050 USD** por tutela (aproximadamente **$100 a $210 COP**).
3. **Caché de Prompt (*Prompt Caching*):** Dado que el `SOUL.md` y el esquema del manifiesto (`~2,060 tokens`) permanecen estáticos entre llamadas, la activación de *Prompt Caching* en plataformas compatibles reduce el costo de entrada recurrente hasta en un **75%**.

---

## 10. Especificaciones de Despliegue e Interoperabilidad

### 10.1 Requisitos del Sistema
* **Intérprete:** Python 3.11 o superior.
* **Hardware Mínimo:** 1 vCPU, 512 MB de RAM, 100 MB de almacenamiento en disco. No requiere GPU.
* **Dependencias:** Especificadas en `requirements.txt`:
  * `numpy >= 1.24.0` (cálculo matricial y distancias vectoriales).
  * `python-docx >= 1.1.0` (compilación de documentos Word).
  * `pypdf >= 4.0.0` y `striprtf >= 0.0.30` (extracción de texto documental).
  * `pyyaml >= 6.0.0` (lectura de configuraciones).

### 10.2 Scripts de Despliegue Automatizado
El repositorio cuenta con scripts de inicialización multiplataforma:
* **Entornos Unix / Linux / macOS:** `deploy.sh`
* **Entornos Windows:** `deploy.ps1`

Ambos scripts validan la versión del intérprete, crean un entorno virtual aislado (`venv`), instalan las dependencias fijadas y ejecutan la batería de pruebas de integridad previa a la puesta en marcha.

### 10.3 Interoperabilidad y Servidor MCP
El manifiesto del agente (`agent/manifest.json`) cumple con las especificaciones del *Model Context Protocol* (MCP) y plataformas agénticas como *Hermes* y *OpenClaw*, permitiendo que cualquier modelo LLM consuma las 6 herramientas de AMPARA a través de interfaces estructuradas JSON-Schema.

---

## 11. Limitaciones, Análisis de Riesgos y Trabajo Futuro

### 11.1 Limitaciones Actuales
1. **Actualización Manual del Corpus Jurisprudencial:** Aunque el motor RAG incluye 228 extractos jurisprudenciales clave, nuevas Sentencias de Unificación (SU) emitidas por la Corte Constitucional requieren ingestión periódica en `ampara_vector.db`.
2. **Evaluación de Peritajes Médicos Complejos:** En controversias donde existe discrepancia técnica entre comités científicos especializados sobre tratamientos experimentales no aprobados por INVIMA, el agente requiere criterio jurídico humano especializado para complementar la argumentación.

### 11.2 Análisis de Riesgos y Mitigaciones
* *Riesgo de alucinación legal:* Mitigado mediante recuperación determinista en base SQLite local y citación estricta de radicados constitucionales reales.
* *Riesgo de ejercicio ilegal de la profesión:* Mitigado mediante la cláusula deontológica en `SOUL.md` y el nodo `INTERRUPT_HUMAN_REVIEW_DRAFT`, que delimita a AMPARA como una herramienta de apoyo técnico-procesal.

### 11.3 Hoja de Ruta (Roadmap Tecnológico)
* **Fase 2:** Integración con la ventanilla virtual de la Rama Judicial colombiana para radicación asistida automática con generación de radicado oficial.
* **Fase 3:** Incorporación de interfaces de voz e inclusión lingüística para comunidades indígenas en sus lenguas nativas, atendiendo su calidad de sujetos de especial protección constitucional.
* **Fase 4:** Firma digital criptográfica de memoriales mediante estándares PKCS#12 y validez probatoria plena (Ley 527 de 1999).

---

## 12. Conclusiones

AMPARA demuestra la viabilidad técnica y forense de construir agentes de inteligencia artificial autónomos enfocados en derechos fundamentales sin incurrir en dependencias de infraestructura pesada o costosa. Al combinar una máquina de estados finitos determinista, un motor RAG vectorial embebido en SQLite de 256 dimensiones, un redactor procesal forense de 12 acápites y protocolos infranqueables de gobernanza ética y revisión humana, AMPARA se posiciona como una herramienta de alto impacto para la democratización del acceso a la justicia y la protección efectiva del derecho a la salud en Colombia.

---

## 13. Referencias Normativas y Jurisprudenciales

1. **República de Colombia.** *Constitución Política de Colombia de 1991*. Artículos 11, 13, 23, 48, 49 y 86.
2. **Presidencia de la República.** *Decreto 2591 de 1991*. Por el cual se reglamenta la acción de tutela consagrada en el artículo 86 de la Constitución Política.
3. **Presidencia de la República.** *Decreto 306 de 1992*. Por el cual se reglamenta el Decreto 2591 de 1991.
4. **Congreso de la República.** *Ley Estatutaria 1751 de 2015*. Por medio de la cual se regula el derecho fundamental a la salud.
5. **Congreso de la República.** *Ley Estatutaria 1581 de 2012*. Por la cual se dictan disposiciones generales para la protección de datos personales.
6. **Corte Constitucional de Colombia.** *Sentencia T-760 de 2008*. M.P. Manuel José Cepeda Espinosa.
7. **Corte Constitucional de Colombia.** *Sentencia SU-508 de 2020*. M.P. Cristina Pardo Schlesinger.
8. **Corte Constitucional de Colombia.** *Sentencia SC-132 de 2018*. Naturaleza jurídica y trámite del Incidente de Desacato.
9. **Model Context Protocol (MCP).** Especificación de arquitectura agéntica e interoperabilidad de herramientas de IA, 2024.
