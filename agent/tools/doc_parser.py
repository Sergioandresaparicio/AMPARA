"""
Document Analyzer - Tool 3 para Hermes (AMPARA)
Módulo: agent/tools/doc_parser.py

Extractor y analizador integral de documentos médico-jurídicos para acciones de tutela:
- Órdenes médicas y fórmulas (medicamentos, insumos, tecnologías, Mipres)
- Historias clínicas, epicrisis y evoluciones
- Cartas de negación de EPS y respuestas administrativas
- Derechos de petición previos radicados
- Autos judiciales (admisorios, medidas provisionales Art. 7 Dec. 2591/91, requerimientos y desacatos)
- Fallos de tutela (primera y segunda instancia)
- Documentos de identidad y pruebas de incapacidad económica

Incluye evaluación de calidad de escaneo/OCR (scan_quality_score) y detección de alertas críticas.
"""

import os
import re
import string
import unicodedata
from typing import Dict, Any, List, Optional, Union

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

def normalize_text(text: str) -> str:
    """Normaliza texto removiendo acentos y pasando a minúsculas para búsquedas robustas."""
    if not text:
        return ""
    nfkd = unicodedata.normalize('NFKD', text.lower())
    return "".join([c for c in nfkd if not unicodedata.combining(c)])


# =====================================================================
# CONSTANTES Y CATÁLOGOS DEL DOMINIO JURÍDICO-SANITARIO COLOMBIANO
# =====================================================================

DOCUMENT_TYPES = {
    "FORMULA_MEDICA": {
        "categoria": "clinico",
        "keywords": ["formula medica", "orden medica", "prescripcion", "receta", "posologia", "via de administracion", "mipres", "cantidad recetada", "principio activo"],
        "descripcion": "Fórmula u orden médica expedida por profesional tratante"
    },
    "HISTORIA_CLINICA": {
        "categoria": "clinico",
        "keywords": ["historia clinica", "epicrisis", "resumen de atencion", "evolucion medica", "anamnesis", "cie-10", "cie 10", "diagnostico principal", "antecedentes"],
        "descripcion": "Historia clínica, resumen de atención o epicrisis hospitalaria"
    },
    "CARTA_NEGACION_EPS": {
        "categoria": "administrativo",
        "keywords": ["negacion de servicios", "no pos", "no pbs", "carta de no autorizacion", "no autorizado", "solicitud no aprobada", "fuera de red", "sin convenio", "exclusion del plan", "no cumple criterios"],
        "descripcion": "Carta formal o constancia de negación de servicios de salud expedida por EPS/IPS"
    },
    "DERECHO_PETICION": {
        "categoria": "administrativo",
        "keywords": ["derecho de peticion", "articulo 23", "respetuosa solicitud", "radicado de peticion", "peticionario", "solicito formalmente", "peticion de salud"],
        "descripcion": "Memorial previo de derecho de petición presentado ante la EPS"
    },
    "AUTO_JUDICIAL": {
        "categoria": "judicial",
        "keywords": ["auto", "juzgado", "tribunal", "medida provisional", "auto admisorio", "desacato", "tramite incidental", "requiérase", "requierase", "traslado", "notifiquese", "termino de 48 horas", "termino de 3 dias"],
        "descripcion": "Providencia judicial (Auto admisorio, medida provisional o requerimiento de desacato)"
    },
    "FALLO_TUTELA": {
        "categoria": "judicial",
        "keywords": ["sentencia", "fallo de tutela", "administrando justicia", "concede la accion de tutela", "ampara el derecho fundamental", "niega la tutela", "resuelve", "primera instancia", "segunda instancia"],
        "descripcion": "Sentencia o fallo definitivo que decide la acción de tutela"
    },
    "INCAPACIDAD_ECONOMICA": {
        "categoria": "probatorio",
        "keywords": ["incapacidad economica", "sin recursos", "declaracion juramentada", "sisben", "certificado de ingresos", "desempleado", "falta de capacidad de pago"],
        "descripcion": "Constancia o declaración de falta de capacidad económica"
    },
    "DOCUMENTO_IDENTIDAD": {
        "categoria": "identidad",
        "keywords": ["cedula de ciudadania", "tarjeta de identidad", "cedula de extranjeria", "registro civil", "republica de colombia", "identificacion personal"],
        "descripcion": "Documento de identificación ciudadana del paciente o accionante"
    },
    "GENERIC_LEGAL": {
        "categoria": "general",
        "keywords": [],
        "descripcion": "Documento genérico o anexo procesal"
    }
}

EPS_KNOWN_LIST = [
    "SURA", "SANITAS", "NUEVA EPS", "FAMISANAR", "COMPENSAR", "SALUD TOTAL", 
    "COOSALUD", "SAVIA SALUD", "CAPITAL SALUD", "ASMET SALUD", "MALLAMAS", 
    "MUTUAL SER", "EMSSANAR", "SOS", "ALIANSALUD", "CAPRESOCA", "PIJAOS SALUD",
    "MEDIMAS", "COOMEVA", "CRUZ BLANCA", "CAFESALUD" # Liquidada/histórica para antecedentes
]

CRITICAL_HEALTH_KEYWORDS = [
    "cancer", "oncolog", "quimioterapia", "radioterapia", "dialisis", "renal cronica",
    "urgencia vital", "uci", "unidad de cuidados intensivos", "metastasis", "leucemia",
    "trasplante", "cirugia urgente", "riesgo de muerte", "danio irreparable", "daño irreparable",
    "cuidados paliativos", "infarto", "aneurisma"
]

CIE10_COMMON_MAP = {
    "C50": "Tumor maligno de la mama",
    "C61": "Tumor maligno de la próstata",
    "C34": "Tumor maligno de bronquios o pulmón",
    "C18": "Tumor maligno del colon",
    "C91": "Leucemia linfoide",
    "E10": "Diabetes mellitus insulinodependiente",
    "E11": "Diabetes mellitus no insulinodependiente",
    "I10": "Hipertensión esencial (primaria)",
    "I50": "Insuficiencia cardíaca",
    "N18": "Enfermedad renal crónica",
    "M05": "Artritis reumatoide seropositiva",
    "G35": "Esclerosis múltiple",
    "F32": "Episodio depresivo",
    "B24": "Enfermedad por VIH"
}


# =====================================================================
# CLASE PRINCIPAL: DocumentAnalyzer
# =====================================================================

class DocumentAnalyzer:
    """
    Analizador integral de documentos de tutela en salud para Hermes.
    Procesa PDFs, textos escaneados y transcripciones OCR.
    """

    def __init__(self):
        pass

    def extract_text_from_file(self, file_path: str) -> str:
        """Extrae texto de un archivo PDF o archivo de texto plano."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo no existe: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            if not HAS_PYPDF:
                raise ImportError("pypdf no está instalado para procesar archivos PDF.")
            text_parts = []
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n\n".join(text_parts)
        elif ext in [".txt", ".md", ".json", ".rtf"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        else:
            raise ValueError(f"Formato no soportado directamente: {ext}")

    def evaluate_scan_quality(self, text: str) -> Dict[str, Any]:
        """
        Evalúa la legibilidad y calidad del texto escaneado/OCR.
        Retorna score (0.0 a 1.0), categoría y advertencias.
        """
        warnings = []
        if not text or len(text.strip()) == 0:
            return {
                "score": 0.0,
                "status": "ILLEGIBLE",
                "warnings": ["El documento está completamente vacío o el OCR no extrajo caracteres."]
            }

        total_chars = len(text)
        words = text.split()
        total_words = len(words)

        if total_words < 10:
            warnings.append("Documento con muy pocas palabras identificadas (<10 palabras).")
            return {
                "score": 0.25,
                "status": "POOR_QUALITY_WARNING",
                "warnings": warnings
            }

        # 1. Ratio de caracteres legibles (alfanuméricos + puntuación estándar)
        printable_clean = sum(1 for c in text if c.isalnum() or c.isspace() or c in ",.-;:()/'\"")
        legible_char_ratio = printable_clean / max(total_chars, 1)

        # 2. Ratio de caracteres 'basura' típicos de OCR dañado (ej. ¬§¢¶¥¦)
        garbage_chars = sum(1 for c in text if c in "¬§¢¶¥¦~`^°|{}[]<>+=_*#@%$&")
        garbage_ratio = garbage_chars / max(total_chars, 1)

        # 3. Longitud media de palabras legibles
        avg_word_len = sum(len(w) for w in words) / max(total_words, 1)
        word_len_penalty = 0.0
        if avg_word_len < 2.5 or avg_word_len > 18.0:
            word_len_penalty = 0.20
            warnings.append("Patrón de palabras fragmentadas o concatenadas propio de OCR de baja resolución.")

        # Cálculo de puntaje
        score = (legible_char_ratio * 0.70) + (max(0.0, 1.0 - garbage_ratio * 5.0) * 0.30) - word_len_penalty
        score = max(0.0, min(1.0, round(score, 3)))

        if score >= 0.82:
            status = "EXCELLENT"
        elif score >= 0.60:
            status = "ACCEPTABLE"
        elif score >= 0.35:
            status = "POOR_QUALITY_WARNING"
            warnings.append("Calidad de escaneo regular. Puede haber omisiones en nombres de medicamentos o fechas.")
        else:
            status = "ILLEGIBLE"
            warnings.append("Documento borroso, corrupto o ilegible. Requiere revisión o nuevo escaneo por parte del usuario.")

        return {
            "score": score,
            "status": status,
            "warnings": warnings
        }

    def detect_document_type(self, text: str, user_hint: Optional[str] = None) -> Dict[str, str]:
        """
        Clasifica automáticamente el tipo de documento según palabras clave y encabezados normalizados.
        """
        if user_hint and user_hint.upper() in DOCUMENT_TYPES:
            doc_key = user_hint.upper()
            return {
                "type": doc_key,
                "category": DOCUMENT_TYPES[doc_key]["categoria"],
                "description": DOCUMENT_TYPES[doc_key]["descripcion"]
            }

        norm_text = normalize_text(text)
        best_type = "GENERIC_LEGAL"
        max_matches = 0

        # 1. Reglas prioritarias específicas (ordenadas de más específico a más general)
        if any(term in norm_text for term in ["administrando justicia", "concede la accion", "concede el amparo", "niega la tutela", "fallo de tutela", "sentencia de tutela"]):
            best_type = "FALLO_TUTELA"
        elif any(term in norm_text for term in ["medida provisional", "auto admisorio", "auto de tramite", "requierase", "desacato", "tramite incidental"]):
            best_type = "AUTO_JUDICIAL"
        elif any(term in norm_text for term in ["negacion de servicios", "no pos", "no pbs", "no autorizado", "carta de negacion", "motivo de no autorizacion"]):
            best_type = "CARTA_NEGACION_EPS"
        elif any(term in norm_text for term in ["formula medica", "orden medica", "receta medica", "posologia", "mipres"]):
            best_type = "FORMULA_MEDICA"
        elif any(term in norm_text for term in ["historia clinica", "epicrisis", "anamnesis", "evolucion medica"]):
            best_type = "HISTORIA_CLINICA"
        elif any(term in norm_text for term in ["derecho de peticion", "articulo 23 de la constitucion"]):
            best_type = "DERECHO_PETICION"
        elif any(term in norm_text for term in ["cedula de ciudadania", "tarjeta de identidad", "identificacion personal"]):
            best_type = "DOCUMENTO_IDENTIDAD"
        elif any(term in norm_text for term in ["incapacidad economica", "falta de recursos", "sin capacidad de pago"]):
            best_type = "INCAPACIDAD_ECONOMICA"
        else:
            # Conteo de palabras clave secundarias normalizadas
            for doc_key, doc_info in DOCUMENT_TYPES.items():
                if doc_key == "GENERIC_LEGAL":
                    continue
                matches = sum(1 for kw in doc_info["keywords"] if normalize_text(kw) in norm_text)
                if matches > max_matches:
                    max_matches = matches
                    best_type = doc_key

        return {
            "type": best_type,
            "category": DOCUMENT_TYPES[best_type]["categoria"],
            "description": DOCUMENT_TYPES[best_type]["descripcion"]
        }

    def extract_entities(self, text: str, doc_type: str) -> Dict[str, Any]:
        """
        Extrae entidades estructuradas relevantes según el tipo de documento.
        """
        text_clean = text.replace("\r", "")
        entities: Dict[str, Any] = {
            "patient_name": None,
            "patient_id": None,
            "eps_name": None,
            "ips_name": None,
            "doctor_name": None,
            "doctor_license": None,
            "diagnosis": [],
            "prescribed_items": [],
            "denial_reason": None,
            "court_info": None,
            "dates": []
        }

        # 1. Extracción de Identificación y Nombre del Paciente
        id_match = re.search(r'(?:C\.?C\.?|T\.?I\.?|C\.?E\.?|Identificación|Identificacion|Documento|No\.?)\s*[:#]?\s*(\d{6,11})', text_clean, re.IGNORECASE)
        if id_match:
            entities["patient_id"] = id_match.group(1).strip()

        name_match = re.search(r'(?:Paciente|Usuario|Nombre|Accionante|Afiliado|Ciudadano)\s*[:#\-]?\s*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]{5,40})(?:\n|,|CC|TI|Edad|$)', text_clean)
        if name_match:
            cand = name_match.group(1).strip()
            if len(cand) > 3 and not any(kw in cand.lower() for kw in ["identificacion", "documento", "historia"]):
                entities["patient_name"] = cand

        # 2. Extracción de EPS e IPS
        for eps in EPS_KNOWN_LIST:
            if re.search(rf'\b{eps}\b', text_clean, re.IGNORECASE):
                entities["eps_name"] = f"EPS {eps.title()}" if not eps.startswith("EPS") else eps.title()
                break

        ips_match = re.search(r'(?:IPS|Institución|Clinica|Hospital|Centro Médico)\s*[:#\-]?\s*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]{5,45})(?:\n|,|$)', text_clean, re.IGNORECASE)
        if ips_match:
            entities["ips_name"] = ips_match.group(1).strip()

        # 3. Extracción de Fechas
        dates = re.findall(r'\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{1,2}\s+de\s+[a-zA-Z]+\s+de\s+\d{4})\b', text_clean)
        if dates:
            entities["dates"] = list(dict.fromkeys(dates))[:4]

        # 4. Extracción de Diagnóstico y Código CIE-10
        cie10_matches = re.findall(r'\b([A-Z]\d{2}(?:\.\d{1,2})?)\b', text_clean)
        diagnoses = []
        for code in set(cie10_matches):
            code_prefix = code[:3]
            desc = CIE10_COMMON_MAP.get(code_prefix, "Diagnóstico codificado CIE-10")
            diagnoses.append({"code": code, "description": desc})

        # Búsqueda textual de diagnósticos si no hay código numérico explícito
        for kw in ["cáncer", "cancer", "diabetes", "hipertension", "insuficiencia renal", "artritis", "leucemia", "esclerosis"]:
            if kw in text_clean.lower() and not any(d["code"].lower() in kw for d in diagnoses):
                diagnoses.append({"code": "CLINICAL", "description": kw.capitalize()})
        entities["diagnosis"] = diagnoses

        # 5. Extracción de Médico y Registro
        doc_match = re.search(r'(?:Dr\(a\)\.?|Médico|Doctor|Profesional|Especialista)\s*[:#\-]?\s*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]{5,35})', text_clean, re.IGNORECASE)
        if doc_match:
            entities["doctor_name"] = doc_match.group(1).strip()
        reg_match = re.search(r'(?:R\.?M\.?|Registro Médico|Tarjeta Profesional)\s*[:#\-]?\s*(\d{4,10})', text_clean, re.IGNORECASE)
        if reg_match:
            entities["doctor_license"] = reg_match.group(1).strip()

        # 6. Extracción de Ítems Prescritos / Medicamentos / Tecnologías
        item_patterns = [
            r'(?:Medicamento|Producto|Tecnología|Prescribe|Insumo)\s*[:#\-]?\s*([^\n]+)',
            r'([A-ZÁÉÍÓÚa-záéíóú]{4,25}\s+\d+\s*(?:mg|ml|mcg|gr|ui)(?:[^\n]*))',
            r'\b(silla de ruedas|pañales|oxigeno|protesis|valvula|sonda|glucómetro)\b[^\n]*'
        ]
        items = []
        for pat in item_patterns:
            matches = re.findall(pat, text_clean, re.IGNORECASE)
            for m in matches:
                item_str = m.strip() if isinstance(m, str) else m[0].strip()
                if 4 < len(item_str) < 80 and item_str not in items:
                    items.append(item_str)
        entities["prescribed_items"] = items[:8]

        # 7. Extracción de Razón de Negación (si es Carta de Negación)
        if doc_type == "CARTA_NEGACION_EPS" or "negacion" in text_clean.lower() or "no autorizado" in text_clean.lower():
            denial_match = re.search(r'(?:motivo de no autorizacion|causal de negacion|justificacion|concepto)\s*[:#\-]?\s*([^\n\.]+(?:\.[^\n\.]+){0,2})', text_clean, re.IGNORECASE)
            if denial_match:
                entities["denial_reason"] = denial_match.group(1).strip()
            else:
                for kw in ["no pos", "no pbs", "sin convenio", "falta de autorizacion previa", "fuera de red", "exclusion"]:
                    if kw in text_clean.lower():
                        entities["denial_reason"] = f"Negación fundamentada en: {kw.upper()}"
                        break

        # 8. Extracción de Información Judicial (si es Auto o Fallo)
        if doc_type in ["AUTO_JUDICIAL", "FALLO_TUTELA"]:
            court_data = {
                "court_name": None,
                "case_filing_number": None,
                "decision_type": None,
                "deadline_granted": None
            }
            court_match = re.search(r'(Juzgado[^\n,]+|Tribunal[^\n,]+|Corte Constitucional)', text_clean, re.IGNORECASE)
            if court_match:
                court_data["court_name"] = court_match.group(1).strip()

            rad_match = re.search(r'(?:Radicado|Expediente|Proceso|Acción de Tutela No\.?)\s*[:#\-]?\s*(\d{10,25}|\d{4}-\d{3,6})', text_clean, re.IGNORECASE)
            if rad_match:
                court_data["case_filing_number"] = rad_match.group(1).strip()

            if "medida provisional" in text_clean.lower():
                court_data["decision_type"] = "DECRETA_MEDIDA_PROVISIONAL_ART7"
            elif "desacato" in text_clean.lower():
                court_data["decision_type"] = "TRAMITE_INCIDENTAL_DESACATO"
            elif "ampara" in text_clean.lower() or "concede" in text_clean.lower():
                court_data["decision_type"] = "CONCEDE_TUTELA"
            elif "niega" in text_clean.lower():
                court_data["decision_type"] = "NIEGA_TUTELA"
            else:
                court_data["decision_type"] = "AUTO_ADMISORIO_TRAMITE"

            deadline_match = re.search(r'(?:término de|plazo de|dentro de las)\s*(\d+\s*(?:horas|días|dias))', text_clean, re.IGNORECASE)
            if deadline_match:
                court_data["deadline_granted"] = deadline_match.group(1).strip()

            entities["court_info"] = court_data

        return entities

    def detect_critical_risks(self, text: str, entities: Dict[str, Any]) -> List[str]:
        """
        Detecta factores de riesgo inminente, urgencia vital o términos perentorios.
        """
        risks = []
        norm_text = normalize_text(text)

        # 1. Riesgo vital / salud crítica por palabras clave
        has_critical_condition = False
        for kw in CRITICAL_HEALTH_KEYWORDS:
            if kw in norm_text:
                risks.append(f"ALERTA MEDICA CRITICA: Se detecta condicion prioritaria ({kw}). Posible riesgo de dano irreparable.")
                has_critical_condition = True
                break

        # 2. Riesgo vital respaldado por CIE-10 (C00-C97 oncológicos, N18 renal crónica)
        if not has_critical_condition and entities.get("diagnosis"):
            for diag in entities["diagnosis"]:
                code = diag.get("code", "")
                desc_norm = normalize_text(diag.get("description", ""))
                if code.startswith("C") or code.startswith("N18") or "maligno" in desc_norm or "cancer" in desc_norm:
                    risks.append(f"ALERTA MEDICA CRITICA: Diagnostico prioritario ({diag['description']}).")
                    break

        # 3. Término judicial perentorio
        if entities.get("court_info") and entities["court_info"].get("deadline_granted"):
            plazo = entities["court_info"]["deadline_granted"]
            risks.append(f"TERMINO JUDICIAL ACTIVO: Providencia concede {plazo}. Monitoreo perentorio de cumplimiento requerido.")

        # 4. Negación de servicio en patología grave
        if entities.get("denial_reason") and any(kw in norm_text for kw in ["cancer", "oncolog", "dialisis", "infarto"]):
            risks.append("VULNERACION AGRAVADA: Negacion formal de EPS sobre patologia de alto costo o riesgo vital.")

        return risks

    def build_tutela_summary(self, doc_type: str, entities: Dict[str, Any], quality_status: str) -> str:
        """
        Construye una redacción condensada lista para ser incorporada
        como Hecho o acápite de Pruebas en el memorial de tutela.
        """
        parts = []
        if quality_status in ["POOR_QUALITY_WARNING", "ILLEGIBLE"]:
            parts.append("[ADVERTENCIA: Documento aportado con baja legibilidad. Debe ratificarse con original].")

        if doc_type == "FORMULA_MEDICA":
            items = ", ".join(entities["prescribed_items"]) if entities["prescribed_items"] else "tecnologías en salud indicadas"
            dr = f" por el Dr(a). {entities['doctor_name']}" if entities["doctor_name"] else ""
            parts.append(f"Fórmula médica expedida{dr} donde se prescribió con carácter necesario: {items}.")

        elif doc_type == "CARTA_NEGACION_EPS":
            eps = entities.get("eps_name") or "la Entidad Promotora de Salud"
            motivo = entities.get("denial_reason") or "trámites administrativos internos"
            parts.append(f"Constancia expedida por {eps} en la cual negó la prestación requerida bajo el argumento: '{motivo}'.")

        elif doc_type == "HISTORIA_CLINICA":
            diags = [d["description"] for d in entities["diagnosis"]]
            diag_str = ", ".join(diags) if diags else "afectación en salud"
            parts.append(f"Resumen de historia clínica donde se certifica el diagnóstico y necesidad clínica de: {diag_str}.")

        elif doc_type == "AUTO_JUDICIAL":
            court = entities.get("court_info", {}).get("court_name") or "el Despacho Judicial"
            dec = entities.get("court_info", {}).get("decision_type") or "providencia judicial"
            plazo = entities.get("court_info", {}).get("deadline_granted") or "término legal"
            parts.append(f"Providencia dictada por {court} en la que se adoptó decisión ({dec}) fijando un término perentorio de {plazo}.")

        elif doc_type == "DERECHO_PETICION":
            eps = entities.get("eps_name") or "la EPS accionada"
            parts.append(f"Copia de Derecho de Petición radicado formalmente ante {eps} solicitando el suministro oportuno sin respuesta efectiva.")

        else:
            parts.append(f"Documento de soporte ({doc_type}) aportado al expediente procesal.")

        return " ".join(parts)

    def parse_document(
        self,
        input_source: Union[str, bytes],
        doc_type_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Punto de entrada principal para procesar un documento (ruta a archivo o texto en memoria).
        """
        # 1. Obtención del texto crudo
        if isinstance(input_source, str) and os.path.exists(input_source):
            raw_text = self.extract_text_from_file(input_source)
            source_type = "file"
            file_name = os.path.basename(input_source)
        elif isinstance(input_source, str):
            raw_text = input_source
            source_type = "text"
            file_name = "in_memory_text"
        else:
            raise ValueError("input_source debe ser una ruta de archivo existente o un string de texto.")

        # 2. Evaluación de Calidad de Escaneo / OCR
        quality = self.evaluate_scan_quality(raw_text)

        # 3. Clasificación del Tipo de Documento
        doc_classification = self.detect_document_type(raw_text, user_hint=doc_type_hint)

        # 4. Extracción de Entidades Específicas
        entities = self.extract_entities(raw_text, doc_classification["type"])

        # 5. Detección de Riesgos Críticos
        critical_alerts = self.detect_critical_risks(raw_text, entities)

        # 6. Generación del Hecho Procesal
        tutela_summary = self.build_tutela_summary(
            doc_classification["type"],
            entities,
            quality["status"]
        )

        words_count = len(raw_text.split())

        return {
            "status": "success" if quality["status"] not in ["POOR_QUALITY_WARNING", "ILLEGIBLE"] else "warning",
            "file_info": {
                "source_type": source_type,
                "file_name": file_name,
                "word_count": words_count,
                "char_count": len(raw_text)
            },
            "document_type": doc_classification["type"],
            "document_category": doc_classification["category"],
            "document_description": doc_classification["description"],
            "scan_quality": quality,
            "extracted_entities": entities,
            "critical_alerts": critical_alerts,
            "requires_human_verification": (quality["status"] in ["POOR_QUALITY_WARNING", "ILLEGIBLE"] or len(critical_alerts) > 0),
            "summary_for_tutela": tutela_summary,
            "raw_text_snippet": raw_text[:300].strip() + ("..." if len(raw_text) > 300 else "")
        }


# =====================================================================
# FUNCIÓN OFICIAL PARA HERMES: ocr_and_document_parser
# =====================================================================

def ocr_and_document_parser(
    input_source: Union[str, bytes],
    doc_type_hint: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Función de nivel superior registrada como herramienta oficial en Hermes.
    Permite procesar cualquier documento médico o legal relevante para la tutela.
    """
    analyzer = DocumentAnalyzer()
    return analyzer.parse_document(input_source=input_source, doc_type_hint=doc_type_hint)
