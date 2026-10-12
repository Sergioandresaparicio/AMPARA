"""
agent/agent.py - Clase Orquestadora Principal del Agente AMPARA
Unifica las 6 herramientas, el manifiesto, las reglas HITL y el ciclo autónomo para Hermes y OpenClaw.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

from agent.tools import (
    state_machine_interview,
    legal_rag_search,
    ocr_and_document_parser,
    draft_template_engine,
    export_petition_to_docx,
    case_db_crud,
    semantic_compliance_eval
)

BASE_DIR = Path(__file__).resolve().parent

class AmparaAgent:
    """
    Agente Jurídico Autónomo en Salud y Tutelas para Colombia.
    Orquestador de herramientas compatibles con Hermes, OpenClaw y servidores MCP.
    """

    def __init__(self):
        self.manifest_path = BASE_DIR / "manifest.json"
        self.soul_path = BASE_DIR / "SOUL.md"
        self.manifest = self._load_manifest()
        self.soul = self._load_soul()



    def _load_manifest(self) -> Dict[str, Any]:
        if self.manifest_path.exists():
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _load_soul(self) -> str:
        if self.soul_path.exists():
            with open(self.soul_path, "r", encoding="utf-8") as f:
                return f.read()
        return "AMPARA: Asistente Jurídico en Salud y Tutelas."

    # --- Tool 1: Case Interviewer ---
    def interview(
        self,
        user_message: str,
        case_state: Optional[Dict[str, Any]] = None,
        hitl_action: Optional[str] = None,
        hitl_feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        return state_machine_interview(
            user_message=user_message,
            case_state=case_state,
            hitl_action=hitl_action,
            hitl_feedback=hitl_feedback
        )

    # --- Tool 2: Legal Knowledge Search ---
    def search_legal_knowledge(
        self,
        query: str,
        top_k: int = 3,
        filter_type: str = "all"
    ) -> Dict[str, Any]:
        return legal_rag_search(
            query=query,
            top_k=top_k,
            filter_type=filter_type
        )

    # --- Tool 3: Document Analyzer ---
    def analyze_document(
        self,
        document_text: str,
        document_type_hint: str = "AUTO",
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        return ocr_and_document_parser(
            document_text=document_text,
            document_type_hint=document_type_hint,
            file_path=file_path
        )

    # --- Tool 4: Petition Generator & DOCX Exporter ---
    def generate_petition(
        self,
        case_data: Dict[str, Any],
        legal_sources: Optional[List[Dict[str, Any]]] = None,
        document_analyses: Optional[List[Dict[str, Any]]] = None,
        action_type: str = "AUTO",
        subject_matter: Optional[str] = None,
        export_docx: bool = False,
        output_docx_path: Optional[str] = None
    ) -> Dict[str, Any]:
        return draft_template_engine(
            case_data=case_data,
            legal_sources=legal_sources,
            document_analyses=document_analyses,
            action_type=action_type,
            subject_matter=subject_matter,
            export_docx=export_docx,
            output_docx_path=output_docx_path
        )

    def export_petition_docx(
        self,
        document_markdown: str,
        output_path: Optional[str] = None,
        case_data: Optional[Dict[str, Any]] = None,
        action_type: str = "TUTELA"
    ) -> str:
        """Exporta un texto de memorial a formato Word (.docx)."""
        return export_petition_to_docx(
            document_markdown=document_markdown,
            output_path=output_path,
            case_data=case_data,
            action_type=action_type
        )

    # --- Tool 5: Case Tracker ---
    def track_case(
        self,
        action: str,
        case_id: Optional[str] = None,
        case_data: Optional[Dict[str, Any]] = None,
        event_data: Optional[Dict[str, Any]] = None,
        filing_date: Optional[str] = None,
        action_type: Optional[str] = None
    ) -> Dict[str, Any]:
        return case_db_crud(
            action=action,
            case_id=case_id,
            case_data=case_data,
            event_data=event_data,
            filing_date=filing_date,
            action_type=action_type
        )

    # --- Tool 6: Compliance Checker ---
    def evaluate_compliance(
        self,
        petition_summary: str,
        eps_response_text: str,
        court_order_text: Optional[str] = None,
        patient_condition: Optional[str] = None
    ) -> Dict[str, Any]:
        return semantic_compliance_eval(
            petition_summary=petition_summary,
            eps_response_text=eps_response_text,
            court_order_text=court_order_text,
            patient_condition=patient_condition
        )

    # --- Telemetría S4 Hermes ---
    def generate_s4_log(
        self,
        case_id: str,
        category: str,
        tools_used: List[str],
        sources: List[Dict[str, str]],
        draft_generated: bool,
        human_review_required: bool,
        critical_escalation: bool = False,
        errors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        return {
            "case_id": case_id,
            "category": category,
            "tools_used": tools_used,
            "sources": sources,
            "draft_generated": draft_generated,
            "human_review_required": human_review_required,
            "critical_escalation": critical_escalation,
            "privacy_masking_applied": True,
            "errors": errors or [],
            "timestamp": datetime.now().isoformat()
        }

# Instancia global disponible para importación rápida
ampara_agent = AmparaAgent()
