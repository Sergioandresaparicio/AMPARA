"""
Compliance Checker - Tool 6 para Hermes (AMPARA)
Módulo: agent/tools/compliance.py

Evaluador semántico de cumplimiento y detector de respuestas evasivas de EPS:
- Compara la respuesta emitida por la EPS/IPS frente a la petición u orden judicial
- Utiliza análisis semántico vectorial (DenseEmbeddingModel + similitud coseno)
- Detecta barreras administrativas, evasivas dilatorias y negaciones veladas
- Clasifica el nivel de cumplimiento: COMPLIANT, PARTIAL_COMPLIANCE, EVASIVE_DILATORY, OUTRIGHT_DENIAL, SILENCE
- Genera recomendaciones procesales inmediatas: activación de Incidente de Desacato
  (Arts. 27 y 52 del Decreto 2591 de 1991 y Sentencia SC-132/18).
"""

import re
import unicodedata
from typing import Dict, Any, List, Optional, Union
from agent.core.vector_db import DenseEmbeddingModel, cosine_similarity

# =====================================================================
# CATÁLOGO DE PATRONES EVASIVOS Y DILATORIOS HABITUALES EN EPS
# =====================================================================

EVASIVE_PATTERNS = {
    "COMITE_MIPRES": {
        "keywords": ["comite tecnico", "comite cientifico", "pendiente junta medica", "en tramite mipres", "autorizacion de direccion medica"],
        "explicacion": "Dilación por trámite administrativo interno de comités técnicos o Mipres (prohibido por Sentencia T-760/08)."
    },
    "DESABASTECIMIENTO_INVENTARIO": {
        "keywords": ["sin existencia", "sin inventario", "agotado en farmacia", "desabastecimiento en dispensario", "pendiente de entrega por proveedor"],
        "explicacion": "Excusas de falta de stock o inventario en dispensarios (la EPS debe garantizar la entrega o entrega domiciliaria inmediata)."
    },
    "FALTA_CONVENIO_RED": {
        "keywords": ["sin convenio vigente", "fuera de red de prestadores", "ips no contratada", "pendiente contratacion"],
        "explicacion": "Traslado indebido de cargas de contratación de red al paciente."
    },
    "BARRERA_ADMINISTRATIVA_REPETICION": {
        "keywords": ["solicitar nueva cita", "cita con medico general", "volver a radicar", "actualizar orden medica", "orden vencida"],
        "explicacion": "Exigencia de re-trámites o citas innecesarias que interrumpen la continuidad del tratamiento."
    },
    "EXCLUSION_PBS_COPAGO": {
        "keywords": ["no incluido en el pbs", "no pos", "no cubierto", "excluido de cobertura", "debe cancelar copago"],
        "explicacion": "Negación por exclusión de cobertura cuando existe orden de juez o necesidad vital insustituible."
    }
}

POSITIVE_COMPLIANCE_KEYWORDS = [
    "autorizado", "aprobado", "se autoriza el suministro", "disponible para reclamar",
    "entrega efectiva", "cita asignada", "procedimiento programado", "se hace entrega",
    "dispensacion autorizada", "sin costo"
]

OUTRIGHT_DENIAL_KEYWORDS = [
    "no es procedente", "se niega la solicitud", "no se autoriza", "improcedente",
    "rechazada la solicitud", "solicitud no aprobada", "denegado"
]


def normalize_text(text: str) -> str:
    """Normaliza texto para comparación insensibles a mayúsculas y acentos."""
    if not text:
        return ""
    nfkd = unicodedata.normalize('NFKD', text.lower())
    return "".join([c for c in nfkd if not unicodedata.combining(c)])


class ComplianceChecker:
    """
    Evaluador semántico de respuestas de entidades de salud frente a peticiones o tutelas.
    """

    def __init__(self):
        self.embedding_model = DenseEmbeddingModel(dim=256)

    def evaluate_compliance(
        self,
        eps_response_text: str,
        original_order_or_petition: Union[str, Dict[str, Any]],
        court_ordered: bool = True
    ) -> Dict[str, Any]:
        """
        Evalúa semántica y jurídicamente si la respuesta de la EPS cumple la solicitud/fallo.
        """
        # 1. Normalización de entradas
        if isinstance(original_order_or_petition, dict):
            petition_text = original_order_or_petition.get("prescription_item", "") or str(original_order_or_petition.get("facts", ""))
        else:
            petition_text = str(original_order_or_petition)

        response_clean = eps_response_text.strip()
        resp_norm = normalize_text(response_clean)
        pet_norm = normalize_text(petition_text)

        # 2. Manejo de Silencio Administrativo
        if not response_clean or len(response_clean) < 15:
            return self._build_verdict(
                status="SILENCE",
                score=0.0,
                semantic_similarity=0.0,
                evasive_flags=["SILENCIO_ADMINISTRATIVO"],
                summary="La EPS no emitió respuesta de fondo ni acreditó cumplimiento dentro del término legal.",
                recommendation="ACTIVAR INCIDENTE DE DESACATO INMEDIATO (Art. 52 Dec. 2591/91). La omisión activa la presunción de veracidad del Art. 20.",
                court_ordered=court_ordered
            )

        # 3. Cálculo de Similitud Semántica Vectorial
        vec_response = self.embedding_model.embed(response_clean)
        vec_petition = self.embedding_model.embed(petition_text)
        semantic_sim = round(cosine_similarity(vec_response, vec_petition), 3)

        # 4. Análisis de Reglas y Patrones Evasivos
        evasive_flags = []
        evasive_explanations = []

        for category, info in EVASIVE_PATTERNS.items():
            for kw in info["keywords"]:
                if normalize_text(kw) in resp_norm:
                    if category not in evasive_flags:
                        evasive_flags.append(category)
                        evasive_explanations.append(info["explicacion"])
                    break

        # 5. Detección de Negación Expresa vs Aprobación
        has_denial = any(normalize_text(kw) in resp_norm for kw in OUTRIGHT_DENIAL_KEYWORDS) or ("no se autoriza" in resp_norm) or ("se niega" in resp_norm)

        has_positive = False
        candidates = POSITIVE_COMPLIANCE_KEYWORDS + ["se autoriza"]
        for kw in candidates:
            kw_norm = normalize_text(kw)
            if kw_norm in resp_norm:
                idx = resp_norm.find(kw_norm)
                preceding = resp_norm[max(0, idx - 6):idx].strip()
                if not preceding.endswith("no") and not preceding.endswith("sin"):
                    has_positive = True
                    break

        # 6. Clasificación del Veredicto
        if has_denial and not has_positive:
            verdict = "OUTRIGHT_DENIAL"
            score = 0.05
            summary = "La EPS denegó expresamente la autorización o entrega del servicio de salud requerido."
            recom = "RADICAR INCIDENTE DE DESACATO (Art. 52 Dec. 2591/91). Desacato formal a orden judicial obligatoria."
        elif has_positive and len(evasive_flags) > 0:
            verdict = "PARTIAL_COMPLIANCE"
            score = 0.60
            summary = "Cumplimiento parcial condicionado: La EPS aprueba la solicitud pero impone trabas o demoras para la entrega efectiva."
            recom = "REQUERIMIENTO JUDICIAL DE CUMPLIMIENTO EFECTIVO. Notificar al juez que la mera autorización en papel sin fecha de entrega vulnera la orden de tutela."
        elif len(evasive_flags) > 0:
            verdict = "EVASIVE_DILATORY"
            score = 0.20
            summary = f"Respuesta evasiva o dilatoria de la EPS fundamentada en barreras administrativas: {', '.join(evasive_explanations)}"
            recom = "PROMOVER INCIDENTE DE DESACATO. Conforme a la Sentencia 712 de 2001 y SC-132 de 2018, los fallos de tutela son de inmediato cumplimiento y no admiten dilaciones por trámites internos de comités o proveedores."
        elif has_positive:
            verdict = "COMPLIANT"
            score = 0.95
            summary = "Cumplimiento efectivo: La EPS autorizó y habilitó la prestación o entrega del servicio."
            recom = "CUMPLIDO. Constatar que el paciente reclame físicamente el medicamento o asista a la cita programada."
        else:
            if semantic_sim < 0.25:
                verdict = "EVASIVE_DILATORY"
                score = 0.30
                summary = "Respuesta incongruente que no se pronuncia sobre el objeto concreto solicitado."
                recom = "SOLICITAR REQUERIMIENTO JUDICIAL POR RESPUESTA INCONGRUENTE."
            else:
                verdict = "PARTIAL_COMPLIANCE"
                score = 0.50
                summary = "Pronunciamiento ambiguo sin constancia de autorización definitiva."
                recom = "REQUERIR ENTREGA INMEDIATA."

        return self._build_verdict(
            status=verdict,
            score=score,
            semantic_similarity=semantic_sim,
            evasive_flags=evasive_flags,
            summary=summary,
            recommendation=recom,
            court_ordered=court_ordered
        )

    def _build_verdict(
        self,
        status: str,
        score: float,
        semantic_similarity: float,
        evasive_flags: List[str],
        summary: str,
        recommendation: str,
        court_ordered: bool
    ) -> Dict[str, Any]:
        requires_contempt = (status in ["EVASIVE_DILATORY", "OUTRIGHT_DENIAL", "SILENCE"] and court_ordered)
        return {
            "status": "success",
            "compliance_verdict": status,
            "compliance_score": score,
            "semantic_similarity": semantic_similarity,
            "is_evasive": (len(evasive_flags) > 0 or status == "EVASIVE_DILATORY"),
            "detected_evasive_patterns": evasive_flags,
            "findings_summary": summary,
            "legal_recommendation": recommendation,
            "activate_contempt_action": requires_contempt,
            "legal_citations": [
                "Artículo 52 del Decreto 2591 de 1991 (Sanción por desacato: arresto y multa)",
                "Artículo 27 del Decreto 2591 de 1991 (Requerimiento al superior jerárquico)",
                "Sentencia SC-132 de 2018 (Carácter vinculante y sancionatorio del desacato)",
                "Sentencia 712 de 2001 (Órdenes de tutela concretas, perentorias e inmediatas)"
            ] if requires_contempt else []
        }


# =====================================================================
# FUNCIÓN OFICIAL PARA HERMES: semantic_compliance_eval
# =====================================================================

def semantic_compliance_eval(
    eps_response_text: str,
    original_order_or_petition: Union[str, Dict[str, Any]],
    court_ordered: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Función de nivel superior registrada como Tool 6 en Hermes.
    Evalúa semántica y jurídicamente las respuestas de la EPS para detectar evasivas y promover desacatos.
    """
    checker = ComplianceChecker()
    return checker.evaluate_compliance(
        eps_response_text=eps_response_text,
        original_order_or_petition=original_order_or_petition,
        court_ordered=court_ordered
    )
