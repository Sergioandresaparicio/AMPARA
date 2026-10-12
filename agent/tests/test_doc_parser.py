"""
Pruebas Unitarias para Tool 3: Document Analyzer (AMPARA / Hermes)
Archivo: agent/tests/test_doc_parser.py
"""

import unittest
import os
from agent.tools.doc_parser import DocumentAnalyzer, ocr_and_document_parser

class TestDocumentAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = DocumentAnalyzer()

    def test_parse_formula_medica(self):
        text = """
        CLÍNICA COLSANITAS S.A.
        FÓRMULA MÉDICA Y ORDEN DE SERVICIO
        Paciente: MARÍA ELENA PÉREZ GÓMEZ
        Identificación: CC 52458912
        EPS: Sanitas
        Fecha: 15/09/2026
        Dr(a): CARLOS MENDOZA OVALLE
        Registro Médico: RM 8472910
        Diagnóstico: C50.9 Tumor maligno de la mama
        Prescribe:
        1. Trastuzumab 440 mg ampolla liofilizada, aplicar según protocolo oncológico.
        2. Ondansetrón 8 mg ampollas.
        Posología: Vía intravenosa cada 21 días.
        """
        res = ocr_and_document_parser(text)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["document_type"], "FORMULA_MEDICA")
        self.assertEqual(res["document_category"], "clinico")
        self.assertEqual(res["extracted_entities"]["patient_id"], "52458912")
        self.assertEqual(res["extracted_entities"]["patient_name"], "MARÍA ELENA PÉREZ GÓMEZ")
        self.assertIn("Sanitas", res["extracted_entities"]["eps_name"])
        self.assertEqual(res["extracted_entities"]["doctor_license"], "8472910")
        self.assertTrue(len(res["extracted_entities"]["prescribed_items"]) >= 1)
        # Debe haber alerta médica crítica por cáncer
        self.assertTrue(any("CRITICA" in a.upper() for a in res["critical_alerts"]))
        self.assertIn("Trastuzumab", res["summary_for_tutela"])

    def test_parse_carta_negacion_eps(self):
        text = """
        EPS SURA - GERENCIA REGIONAL DE SALUD
        CARTA DE NEGACIÓN DE SERVICIOS DE SALUD
        Afiliado: JUAN PABLO RODRÍGUEZ
        CC: 79843210
        Fecha: 22 de septiembre de 2026
        Informamos que la solicitud de suministro de medicamento no ha sido aprobada.
        Motivo de no autorizacion: Solicitud No POS / No PBS excluida del plan básico. Debe tramitarse por comité técnico Mipres.
        """
        res = ocr_and_document_parser(text)
        self.assertEqual(res["document_type"], "CARTA_NEGACION_EPS")
        self.assertEqual(res["document_category"], "administrativo")
        self.assertIn("Sura", res["extracted_entities"]["eps_name"])
        self.assertIsNotNone(res["extracted_entities"]["denial_reason"])
        self.assertIn("No POS", res["extracted_entities"]["denial_reason"])
        self.assertIn("Constancia expedida por", res["summary_for_tutela"])

    def test_parse_auto_judicial_medida_provisional(self):
        text = """
        RAMA JUDICIAL DEL PODER PÚBLICO
        JUZGADO 15 PENAL MUNICIPAL CON FUNCIÓN DE CONTROL DE GARANTÍAS DE BOGOTÁ
        Radicado: 11001400401520260012400
        Accionante: MARÍA ELENA PÉREZ GÓMEZ
        Accionada: EPS SANITAS

        AUTO DE TRÁMITE Y MEDIDA PROVISIONAL
        En virtud del artículo 7 del Decreto 2591 de 1991, este Despacho decreta MEDIDA PROVISIONAL urgente.
        Se ordena a la EPS SANITAS que dentro del término de 48 horas siguientes a la notificación,
        proceda a autorizar y entregar los medicamentos requeridos.
        Notifíquese y cúmplase.
        """
        res = ocr_and_document_parser(text)
        self.assertEqual(res["document_type"], "AUTO_JUDICIAL")
        self.assertEqual(res["document_category"], "judicial")
        court_info = res["extracted_entities"]["court_info"]
        self.assertIsNotNone(court_info)
        self.assertEqual(court_info["decision_type"], "DECRETA_MEDIDA_PROVISIONAL_ART7")
        self.assertEqual(court_info["deadline_granted"], "48 horas")
        self.assertEqual(court_info["case_filing_number"], "11001400401520260012400")
        self.assertTrue(any("TERMINO JUDICIAL" in a.upper() or "TÉRMINO JUDICIAL" in a.upper() for a in res["critical_alerts"]))

    def test_parse_fallo_tutela(self):
        text = """
        JUZGADO PRIMERO CIVIL DEL CIRCUITO
        SENTENCIA DE TUTELA DE PRIMERA INSTANCIA
        Radicado: 05001310300120260045000
        Administrando justicia en nombre de la República de Colombia y por autoridad de la ley:
        RESUELVE:
        PRIMERO: CONCEDE LA ACCIÓN DE TUTELA incoada para la protección de los derechos a la salud y vida digna.
        SEGUNDO: ORDENAR a la EPS Compensar la entrega inmediata del tratamiento.
        """
        res = ocr_and_document_parser(text)
        self.assertEqual(res["document_type"], "FALLO_TUTELA")
        self.assertEqual(res["extracted_entities"]["court_info"]["decision_type"], "CONCEDE_TUTELA")

    def test_scan_quality_warning_on_corrupted_ocr(self):
        corrupted_text = "§¢¬¶ %%## $$ 12 @@!! ¬¬ ¦¦ ~~~"
        res = ocr_and_document_parser(corrupted_text)
        self.assertEqual(res["status"], "warning")
        self.assertIn(res["scan_quality"]["status"], ["POOR_QUALITY_WARNING", "ILLEGIBLE"])
        self.assertTrue(res["requires_human_verification"])
        self.assertTrue(len(res["scan_quality"]["warnings"]) > 0)

    def test_pdf_extraction_real_file(self):
        pdf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw_documents", "decretos", "Decreto_306_de_1992.pdf")
        if os.path.exists(pdf_path):
            res = ocr_and_document_parser(pdf_path)
            self.assertEqual(res["status"], "success")
            self.assertGreater(res["file_info"]["word_count"], 100)
            self.assertIn("1992", res["raw_text_snippet"])

if __name__ == "__main__":
    unittest.main()
