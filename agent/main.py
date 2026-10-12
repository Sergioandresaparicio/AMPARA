"""
Punto de Entrada Principal - Agente AMPARA
Asistente Jurídico Autónomo en Salud y Tutelas para Hermes
"""

import sys
import json
from pathlib import Path

# Asegurar que la raíz del proyecto esté en sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


from agent.tools import (
    state_machine_interview,
    legal_rag_search,
    ocr_and_document_parser,
    draft_template_engine,
    case_db_crud,
    semantic_compliance_eval
)

def run_demo():
    print("=" * 70)
    print("INICIANDO DEMOSTRACIÓN INTEGRAL DEL AGENTE AMPARA (HERMES 6 TOOLS)")
    print("=" * 70)



    # 1. Prueba de Case Interviewer (Tool 1)
    print("\n[Paso 1] Ejecutando Case Interviewer (Tool 1 - state_machine_interview)...")
    res1 = state_machine_interview("Sí, autorizo el uso y tratamiento confidencial de mis datos")
    print(f"Estado: {res1['current_state']} | Consentimiento: {res1['consent_status']}")
    
    # 2. Paso de clasificación con caso urgente
    res2 = state_machine_interview(
        "La EPS Sanitas no me entrega mi medicamento para quimioterapia contra el cáncer",
        case_state=res1["case_state"]
    )
    print(f"Tipo de caso: {res2['case_state']['facts'][0]['case_type']}")
    print(f"Nivel de riesgo detectado: {res2['risk_level']} (Alerta Crítica: {res2['critical_escalation']})")
    print(f"Requiere revisión humana (HITL): {res2['human_review_required']}")

    # 3. Prueba de Document Analyzer (Tool 3)
    print("\n[Paso 2] Ejecutando Document Analyzer (Tool 3 - ocr_and_document_parser)...")
    muestra_doc = """
    CLÍNICA COLSANITAS S.A.
    FÓRMULA MÉDICA Y ORDEN DE SERVICIO
    Paciente: MARÍA ELENA PÉREZ GÓMEZ
    Identificación: CC 52458912 | EPS: Sanitas | Fecha: 15/09/2026
    Dr(a): CARLOS MENDOZA OVALLE | RM 8472910
    Diagnóstico: C50.9 Tumor maligno de la mama
    Prescribe: Trastuzumab 440 mg ampolla liofilizada, dosis según protocolo oncológico.
    """
    doc_res = ocr_and_document_parser(muestra_doc)
    print(f"Documento clasificado como: {doc_res['document_type']} ({doc_res['document_description']})")
    print(f"Calidad del escaneo: {doc_res['scan_quality']['status']} (Score: {doc_res['scan_quality']['score']})")
    print(f"Paciente detectado: {doc_res['extracted_entities']['patient_name']} (CC {doc_res['extracted_entities']['patient_id']})")
    print(f"Medicamento(s): {doc_res['extracted_entities']['prescribed_items']}")
    print(f"Alertas de riesgo: {doc_res['critical_alerts']}")

    # 4. Prueba de Legal RAG en Base de Datos Vectorial SQLite (Tool 2)
    print("\n[Paso 3] Consultando Base de Datos Vectorial SQLite (Tool 2 - legal_rag_search)...")
    consulta = "medidas provisionales urgentes falta de medicamento vital"
    rag_res = legal_rag_search(consulta, top_k=3)
    print(f"Consulta: '{consulta}' | Total fuentes recuperadas: {rag_res['total_found']}")
    for i, r in enumerate(rag_res["results"], 1):
        print(f"  Fuente {i}: {r['chunk_id']} | Score: {r['score']} | {r['title'][:65]}...")

    # 5. Prueba de Petition Generator (Tool 4)
    print("\n[Paso 4] Ensamblando Acción de Tutela con Medidas Cautelares (Tool 4 - draft_template_engine)...")
    case_payload = {
        "patient_name": doc_res["extracted_entities"]["patient_name"],
        "patient_id": doc_res["extracted_entities"]["patient_id"],
        "eps_name": doc_res["extracted_entities"]["eps_name"],
        "diagnosis": "Tumor maligno de la mama (C50.9)",
        "urgency_level": res2["risk_level"],
        "critical_escalation": res2["critical_escalation"],
        "city": "Bogotá D.C."
    }
    petition_res = draft_template_engine(
        case_data=case_payload,
        legal_sources=rag_res["results"],
        document_analyses=[doc_res]
    )
    print(f"Acción Procesal: {petition_res['action_type']} | Materia: {petition_res['subject_matter']}")
    print(f"Medidas Cautelares Provisionales: {petition_res['metadata']['has_provisional_measures']}")
    print(f"Palabras generadas: {petition_res['metadata']['word_count']} (~{petition_res['metadata']['estimated_pages']} páginas)")

    # 6. Prueba de Case Tracker (Tool 5)
    print("\n[Paso 5] Registrando Expediente y Monitoreando Plazos en SQLite (Tool 5 - case_db_crud)...")
    created_case = case_db_crud(
        action="create",
        case_data={
            "patient_name": case_payload["patient_name"],
            "patient_id": case_payload["patient_id"],
            "eps_name": case_payload["eps_name"],
            "case_type": "medicamento",
            "urgency_level": case_payload["urgency_level"],
            "facts": [{"details": "Negación de Trastuzumab 440mg para cáncer de mama"}]
        }
    )
    case_id = created_case["case"]["case_id"]
    print(f"Expediente creado en SQLite: ID `{case_id}` (Fase: {created_case['case']['phase']})")

    # Simular radicación judicial y cálculo de términos constitucionales
    filing_res = case_db_crud(
        action="record_filing",
        case_id=case_id,
        court_filing_number="11001400401520260018800",
        court_name="Juzgado 15 Penal Municipal de Bogotá",
        filing_date="2026-10-07",
        action_type="TUTELA"
    )
    dl = filing_res["case"]["deadline_monitoring"]
    print(f"Radicado judicial: {filing_res['case']['court_filing_number']} ante {filing_res['case']['court_name']}")
    print(f"Fecha límite de fallo: {filing_res['case']['deadline_date']} | Estado del término: {dl['status']} ({dl['message']})")

    # 7. Prueba de Compliance Checker (Tool 6)
    print("\n[Paso 6] Evaluando Respuesta de la EPS y Detección de Desacato (Tool 6 - semantic_compliance_eval)...")
    respuesta_eps_simulada = """
    En atención a la orden judicial, informamos que el medicamento Trastuzumab 440mg
    se encuentra pendiente de aprobación ante el comité técnico científico y actualmente
    presentamos desabastecimiento en el dispensario por parte del laboratorio proveedor.
    """
    comp_eval = semantic_compliance_eval(
        eps_response_text=respuesta_eps_simulada,
        original_order_or_petition="Entrega inmediata de medicamento oncológico Trastuzumab 440mg"
    )
    print(f"Veredicto de Cumplimiento: {comp_eval['compliance_verdict']}")
    print(f"¿Es evasiva o dilatoria?: {comp_eval['is_evasive']} (Patrones detectados: {comp_eval['detected_evasive_patterns']})")
    print(f"Activación de Incidente de Desacato: {comp_eval['activate_contempt_action']}")
    print(f"Recomendación Procesal: \"{comp_eval['legal_recommendation'][:140]}...\"")

    # 8. Salida S4 de Hermes
    print("\n[Paso 7] Registro S4 de Operación Autónoma para Hermes:")
    s4_log = {
        "case_id": case_id,
        "category": "medicamentos",
        "current_phase": "contempt_recommended",
        "tools_executed": [
            "state_machine_interview",
            "ocr_and_document_parser",
            "legal_rag_search",
            "draft_template_engine",
            "case_db_crud",
            "semantic_compliance_eval"
        ],
        "sources_cited": petition_res["sources_for_s4"],
        "human_review_required": True,
        "compliance_status": comp_eval["compliance_verdict"],
        "contempt_recommended": comp_eval["activate_contempt_action"]
    }
    print(json.dumps(s4_log, indent=2, ensure_ascii=False))

    print("\n" + "=" * 70)
    print("MATRIZ DE 6 HERRAMIENTAS DE HERMES 100% OPERATIVA EN AMPARA")
    print("=" * 70)





if __name__ == "__main__":
    run_demo()
