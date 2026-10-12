import unittest
from agent.tools.interviewer import StateMachineInterview, INTERVIEW_GRAPH, state_machine_interview
from agent.tools.interviewer.state_machine import (
    get_user_consent,
    classify_case,
    required_fields,
    validate_answer,
    assess_risk,
    calculate_confidence,
    calculate_completion,
    current_time
)

class TestCaseInterviewer(unittest.TestCase):
    def test_legacy_functions_preserved(self):
        consent = get_user_consent()
        self.assertEqual(consent["status"], "accepted")
        
        self.assertEqual(classify_case("necesito un medicamento"), "medicamento")
        self.assertEqual(classify_case("solicito una cita médica"), "cita")
        self.assertEqual(classify_case("requiero un procedimiento"), "procedimiento")
        self.assertEqual(classify_case("requiero un tratamiento"), "tratamiento")
        self.assertEqual(classify_case("otro asunto"), "respuesta_administrativa")
        
        reqs = required_fields("medicamento")
        self.assertIn("documents.medical_order", reqs)
        self.assertIn("entity.name", reqs)
        
        val = validate_answer(" Sanitas ", "entity.name")
        self.assertEqual(val, " Sanitas ")
        self.assertIsNone(validate_answer("", "entity.name"))
        
        self.assertEqual(assess_risk({"impact.urgency": "Crítica"}), "high")
        self.assertEqual(assess_risk({"impact.urgency": "Alta"}), "medium")
        self.assertEqual(assess_risk({"impact.urgency": "Normal"}), "low")
        
        self.assertAlmostEqual(calculate_confidence({}), 0.95)
        self.assertAlmostEqual(calculate_completion({"a": "1", "b": None}), 0.5)
        self.assertTrue(len(current_time()) > 0)

    def test_state_machine_flow(self):
        sm = StateMachineInterview(graph_config=INTERVIEW_GRAPH)
        
        # 1. Consentimiento
        self.assertEqual(sm.current_state, "CONSENT")
        res1 = sm.process_step("Sí, acepto")
        self.assertEqual(res1["consent_status"], "accepted")
        self.assertEqual(sm.current_state, "CLASSIFICATION")
        
        # 2. Clasificación
        res2 = sm.process_step("La EPS no me entrega mi medicamento para la hipertensión")
        self.assertEqual(sm.case_type, "medicamento")
        self.assertEqual(sm.current_state, "COLLECTION")
        
        # 3. Recolección de campos faltantes
        while sm.current_state == "COLLECTION" and sm.get_missing_fields():
            missing_field = sm.get_missing_fields()[0]
            val = "Sanitas" if "entity" in missing_field else "Información de prueba"
            sm.process_step(val)
            
        # 4. Evaluación de Riesgo
        self.assertEqual(sm.current_state, "RISK_ASSESSMENT")
        res_risk = sm.process_step("Mi urgencia es Alta")
        self.assertEqual(sm.current_state, "COMPLETED")
        self.assertEqual(res_risk["phase"], "completed")
        self.assertEqual(sm.completion_score, 1.0)
        
        # 5. Serialización y deserialización
        data = sm.to_dict()
        self.assertIn("facts", data)
        self.assertIn("case_id", data)
        
        restored = StateMachineInterview.from_dict(data, graph_config=INTERVIEW_GRAPH)
        self.assertEqual(restored.case_id, sm.case_id)
        self.assertEqual(restored.current_state, "COMPLETED")

    def test_critical_trigger_detection(self):
        sm = StateMachineInterview(graph_config=INTERVIEW_GRAPH)
        sm.process_step("Sí, acepto")
        res = sm.process_step("Suspenden quimioterapia urgente para cáncer de mama")
        
        self.assertTrue(sm.is_critical())
        self.assertTrue(res["critical_escalation"])
        self.assertTrue(res["human_review_required"])
        self.assertEqual(sm.risk_level, "critical")

    def test_hermes_tool_function(self):
        result1 = state_machine_interview("Sí, autorizo el uso de mis datos")
        self.assertEqual(result1["consent_status"], "accepted")
        self.assertIn("case_state", result1)
        # La pregunta inicial al pasar a CLASSIFICATION debe incluir la consulta sobre título propio vs agente oficioso
        self.assertIn("título propio", result1["prompt"])
        self.assertIn("agente oficioso", result1["prompt"])
        
        result2 = state_machine_interview("No me entregan los medicamentos para quimioterapia", case_state=result1["case_state"])
        self.assertEqual(result2["current_state"], "COLLECTION")
        self.assertTrue(result2["critical_escalation"])

    def test_representation_detection_modes(self):
        # Caso Agente Oficioso / Abogado
        sm_agente = StateMachineInterview(graph_config=INTERVIEW_GRAPH)
        sm_agente.process_step("Sí, acepto")
        sm_agente.process_step("Soy abogado y actúo como agente oficioso de mi paciente a quien no le dan la insulina")
        self.assertEqual(sm_agente.representation["type"], "AGENTE_OFICIOSO")
        self.assertEqual(sm_agente.representation["person_mode"], "third_person")

        # Caso Título Propio
        sm_propio = StateMachineInterview(graph_config=INTERVIEW_GRAPH)
        sm_propio.process_step("Sí, autorizo")
        sm_propio.process_step("Es a título propio, yo soy el paciente directamente y requiero mi cirugía")
        self.assertEqual(sm_propio.representation["type"], "PROPIO")
        self.assertEqual(sm_propio.representation["person_mode"], "first_person")

if __name__ == "__main__":
    unittest.main()
