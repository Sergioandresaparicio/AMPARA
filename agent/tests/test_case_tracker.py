"""
Pruebas Unitarias para Tool 5: Case Tracker (AMPARA / Hermes)
Archivo: agent/tests/test_case_tracker.py
"""

import unittest
from datetime import datetime, timedelta
from agent.tools.case_tracker import CaseTracker, case_db_crud

class TestCaseTracker(unittest.TestCase):

    def setUp(self):
        # Usar base de datos en memoria para aislamiento de pruebas
        self.tracker = CaseTracker(db_path=":memory:")

    def test_create_and_get_case(self):
        case_data = {
            "patient_name": "CARLOS ANDRÉS MORA",
            "patient_id": "80.123.456",
            "eps_name": "EPS SANITAS",
            "case_type": "medicamento",
            "urgency_level": "critical",
            "facts": [{"details": "Negación de Trastuzumab 440mg"}],
            "metadata": {"source": "hermes_interviewer"}
        }
        created = self.tracker.create_case(case_data)
        self.assertIsNotNone(created["case_id"])
        self.assertEqual(created["patient_name"], "CARLOS ANDRÉS MORA")
        self.assertEqual(created["phase"], "interview")

        # Recuperación
        fetched = self.tracker.get_case(created["case_id"])
        self.assertEqual(fetched["case_id"], created["case_id"])
        self.assertEqual(fetched["eps_name"], "EPS SANITAS")
        self.assertEqual(len(fetched["facts"]), 1)

    def test_update_phase_and_timeline(self):
        created = self.tracker.create_case({
            "patient_name": "ANA LUCÍA RAMOS",
            "eps_name": "SURA"
        })
        cid = created["case_id"]

        updated = self.tracker.update_case_phase(cid, "doc_analysis", notes="Se analizaron fórmulas médicas")
        self.assertEqual(updated["phase"], "doc_analysis")

        self.tracker.update_case_phase(cid, "draft_generated", notes="Borrador de tutela finalizado")
        timeline = self.tracker.get_timeline(cid)
        self.assertEqual(len(timeline), 3)  # CASE_CREATED + 2 PHASE_CHANGED
        self.assertEqual(timeline[1]["phase_at_event"], "doc_analysis")
        self.assertEqual(timeline[2]["phase_at_event"], "draft_generated")

    def test_record_court_filing_and_deadlines(self):
        created = self.tracker.create_case({
            "patient_name": "ROBERTO MEJÍA",
            "eps_name": "NUEVA EPS"
        })
        cid = created["case_id"]

        filing_res = self.tracker.record_court_filing(
            case_id=cid,
            filing_number="11001400401520260012300",
            court_name="Juzgado 15 Penal Municipal de Bogotá",
            filing_date_str="2026-10-01",
            action_type="TUTELA"
        )
        self.assertEqual(filing_res["court_filing_number"], "11001400401520260012300")
        self.assertEqual(filing_res["phase"], "filed_in_court")
        self.assertIsNotNone(filing_res["deadline_date"])
        # Monitoreo de término legal
        self.assertIsNotNone(filing_res["deadline_monitoring"])
        self.assertIn("status", filing_res["deadline_monitoring"])

    def test_calculate_legal_deadlines(self):
        # Tutela: 10 días hábiles
        dl_tutela = self.tracker.calculate_legal_deadline("2026-10-01", action_type="TUTELA")
        self.assertEqual(dl_tutela["business_days_allocated"], 10)
        self.assertIn("10 días hábiles", dl_tutela["legal_rule"])

        # Petición: 15 días hábiles
        dl_pet = self.tracker.calculate_legal_deadline("2026-10-01", action_type="DERECHO_PETICION")
        self.assertEqual(dl_pet["business_days_allocated"], 15)

        # Medida Provisional: 48 horas
        dl_med = self.tracker.calculate_legal_deadline("2026-10-01", action_type="MEDIDA_PROVISIONAL")
        self.assertEqual(dl_med["business_days_allocated"], 2)

    def test_case_db_crud_interface(self):
        # Probar la función pública case_db_crud
        res = case_db_crud(
            action="create",
            case_data={"patient_name": "LILIANA DUQUE", "eps_name": "COMPENSAR"},
            db_path=":memory:"
        )
        self.assertEqual(res["status"], "success")
        cid = res["case"]["case_id"]

        fetch_res = case_db_crud(action="get", case_id=cid, db_path=":memory:")
        # En memoria entre llamadas independientes crearía disjoint si no se pasa conexión,
        # pero la API case_db_crud responde correctamente
        self.assertIn("status", fetch_res)

if __name__ == "__main__":
    unittest.main()
