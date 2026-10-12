"""
Pruebas Unitarias para Tool 6: Compliance Checker (AMPARA / Hermes)
Archivo: agent/tests/test_compliance.py
"""

import unittest
from agent.tools.compliance import ComplianceChecker, semantic_compliance_eval

class TestComplianceChecker(unittest.TestCase):

    def setUp(self):
        self.checker = ComplianceChecker()

    def test_compliant_response(self):
        resp_eps = """
        EPS SANITAS INFORMA:
        Su solicitud de medicamento Trastuzumab 440mg ha sido debidamente AUTORIZADA.
        El producto se encuentra disponible para entrega inmediata y sin costo en el dispensario Cruz Verde de la Calle 100.
        """
        petition = "Entrega urgente de medicamento oncológico Trastuzumab 440mg para cáncer de mama"
        res = semantic_compliance_eval(resp_eps, petition)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["compliance_verdict"], "COMPLIANT")
        self.assertFalse(res["is_evasive"])
        self.assertFalse(res["activate_contempt_action"])
        self.assertGreater(res["compliance_score"], 0.8)

    def test_evasive_dilatory_response(self):
        resp_eps = """
        En atención a su requerimiento, le comunicamos que el medicamento no pos se encuentra actualmente
        en trámite ante el comité técnico científico y pendiente de validación por dirección médica.
        Asimismo, presentamos desabastecimiento en dispensario por parte del proveedor.
        """
        petition = "Entrega urgente de medicamento vital oncológico"
        res = semantic_compliance_eval(resp_eps, petition)
        self.assertEqual(res["compliance_verdict"], "EVASIVE_DILATORY")
        self.assertTrue(res["is_evasive"])
        self.assertTrue(len(res["detected_evasive_patterns"]) >= 1)
        self.assertTrue(res["activate_contempt_action"])
        self.assertIn("INCIDENTE DE DESACATO", res["legal_recommendation"])
        # Citas jurídicas obligatorias
        self.assertTrue(any("Artículo 52" in c for c in res["legal_citations"]))

    def test_outright_denial(self):
        resp_eps = """
        EPS SURA:
        Revisada la historia clínica, se niega la solicitud de tratamiento integral por considerarse improcedente.
        No se autoriza el suministro solicitado.
        """
        petition = "Tratamiento integral y cirugía prioritaria"
        res = semantic_compliance_eval(resp_eps, petition)
        self.assertEqual(res["compliance_verdict"], "OUTRIGHT_DENIAL")
        self.assertTrue(res["activate_contempt_action"])
        self.assertIn("DESACATO", res["legal_recommendation"])

    def test_silence_response(self):
        resp_eps = ""  # Silencio administrativo
        petition = "Entrega de medicamentos y cita con especialista"
        res = semantic_compliance_eval(resp_eps, petition)
        self.assertEqual(res["compliance_verdict"], "SILENCE")
        self.assertTrue(res["activate_contempt_action"])
        self.assertIn("DESACATO", res["legal_recommendation"])

    def test_partial_compliance(self):
        resp_eps = """
        Se autoriza el medicamento analgésico pero respecto a la prótesis debe volver a solicitar cita
        con médico general para actualizar orden médica por estar fuera de red.
        """
        petition = "Autorización de prótesis y medicamentos analgésicos"
        res = semantic_compliance_eval(resp_eps, petition)
        self.assertEqual(res["compliance_verdict"], "PARTIAL_COMPLIANCE")
        self.assertTrue(res["is_evasive"])

if __name__ == "__main__":
    unittest.main()
