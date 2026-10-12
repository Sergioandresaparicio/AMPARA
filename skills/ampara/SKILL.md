---
name: ampara
description: "Asistente Jurídico Autónomo para Acciones de Tutela y Derecho a la Salud en Colombia. Incluye entrevista guiada, análisis de documentos médicos, búsqueda de jurisprudencia constitucional, generación de memoriales judiciales y auditoría de cumplimiento."
version: 1.0.0
author: Equipo AMPARA
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [tutelas, salud, colombia, legal, derecho, corte-constitucional]
---

# AMPARA: Asistente Jurídico en Salud y Tutelas

## Descripción General
Esta habilidad proporciona el conjunto completo de 6 herramientas especializadas para tramitar y redactar acciones de tutela de salud en Colombia conforme al Decreto 2591 de 1991 y la jurisprudencia de la Corte Constitucional (Sentencia T-760 de 2008).

## Cuándo Usar Esta Habilidad
- Cuando el usuario solicite ayuda por negación de medicamentos, cirugías, tratamientos, citas con especialistas o traslados médicos por parte de una EPS.
- Cuando se requiera analizar fórmulas médicas, historias clínicas o cartas de negación de EPS.
- Cuando se deba redactar una Acción de Tutela con Medidas Cautelares Provisionales (Art. 7 Dec. 2591/91).
- Cuando se deba auditar si la EPS cumplió una orden judicial y proyectar un Incidente de Desacato (Art. 52 Dec. 2591/91).

## Herramientas Disponibles en `agent/tools`

1. **`state_machine_interview`**:
   - Entrevista estructurada al paciente con validación de consentimiento informado (Ley 1581/2012) y detección de urgencia vital crítica (HITL).
2. **`legal_rag_search`**:
   - Búsqueda híbrida (vectorial SQLite + BM25) sobre los 228 fragmentos normativos y jurisprudenciales organizados en las 6 Consultas Base de la Corte Constitucional (Entrada 4) en `agent/data/ampara_vector.db`.
3. **`ocr_and_document_parser`**:
   - Clasificación y extracción de 8 tipos de documentos (fórmulas médicas, CIE-10, cartas de EPS).
4. **`draft_template_engine`**:
   - Ensamblador procesal de la Acción de Tutela (Hechos, Derechos, Pretensiones, Pruebas y Cautelares).
5. **`case_db_crud`**:
   - Registro del expediente y cómputo de términos legales hábiles (10 días fallo tutela, 15 días derecho de petición, 48 horas cautelares).
6. **`semantic_compliance_eval`**:
   - Auditoría semántica de evasivas de la EPS y recomendación de Incidente de Desacato.

## Modo de Ejecución Rápida
Para ejecutar el ciclo integral del agente desde la terminal:
```powershell
python main.py
```

O importar individualmente las herramientas en Python:
```python
from agent.tools import (
    state_machine_interview,
    legal_rag_search,
    ocr_and_document_parser,
    draft_template_engine,
    case_db_crud,
    semantic_compliance_eval
)
```
