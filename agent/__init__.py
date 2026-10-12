"""
Módulo principal del Agente AMPARA
Asistente Jurídico Autónomo en Salud y Tutelas para Hermes, OpenClaw y MCP.
"""

from .agent import AmparaAgent, ampara_agent
from .tools import (
    state_machine_interview,
    legal_rag_search,
    ocr_and_document_parser,
    draft_template_engine,
    export_petition_to_docx,
    case_db_crud,
    semantic_compliance_eval
)

__version__ = "1.0.0"

__all__ = [
    "AmparaAgent",
    "ampara_agent",
    "state_machine_interview",
    "legal_rag_search",
    "ocr_and_document_parser",
    "draft_template_engine",
    "export_petition_to_docx",
    "case_db_crud",
    "semantic_compliance_eval"
]
