import unittest
from agent.tools.rag_search import legal_rag_search, get_rag_engine

class TestLegalRAG(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = get_rag_engine()

    def test_engine_has_indexed_chunks(self):
        self.assertTrue(self.engine.is_indexed)
        self.assertGreater(len(self.engine.chunks), 20)
        self.assertIn("DEC-2591-1991", self.engine.doc_registry)
        self.assertIn("SC-543-1992", self.engine.doc_registry)

    def test_search_medidas_provisionales(self):
        res = legal_rag_search("medidas provisionales urgentes proteger derecho")
        self.assertGreater(res["total_found"], 0)
        chunk_ids = [r["chunk_id"] for r in res["results"]]
        found = any("ART-7" in cid or "DEC-306" in cid for cid in chunk_ids)
        self.assertTrue(found, f"No encontró medidas provisionales en {chunk_ids}")

    def test_search_presuncion_veracidad(self):
        res = legal_rag_search("presunción de veracidad informe no rendido")
        self.assertGreater(res["total_found"], 0)
        chunk_ids = [r["chunk_id"] for r in res["results"]]
        found = any("ART-20" in cid for cid in chunk_ids)
        self.assertTrue(found, f"No encontró presunción de veracidad en {chunk_ids}")

    def test_search_desacato(self):
        res = legal_rag_search("incidente de desacato sanción arresto multa")
        self.assertGreater(res["total_found"], 0)
        chunk_ids = [r["chunk_id"] for r in res["results"]]
        found = any("ART-52" in cid or "SC-132" in cid for cid in chunk_ids)
        self.assertTrue(found, f"No encontró desacato en {chunk_ids}")

    def test_search_peticion_evasiva(self):
        res = legal_rag_search("derecho de petición respuesta evasiva servicios públicos")
        self.assertGreater(res["total_found"], 0)
        chunk_ids = [r["chunk_id"] for r in res["results"]]
        found = any("ST-080" in cid or "ART-42" in cid for cid in chunk_ids)
        self.assertTrue(found, f"No encontró T-080 o Art. 42 en {chunk_ids}")

    def test_hermes_s4_sources_format(self):
        res = legal_rag_search("reparto de tutela competencia funcional")
        self.assertIn("sources_for_s4", res)
        self.assertGreater(len(res["sources_for_s4"]), 0)
        for s in res["sources_for_s4"]:
            self.assertIn("id", s)
            self.assertIn("ref", s)

    def test_bateria_entrada4_consultas_base(self):
        """Verifica que las 6 Consultas Base de la Entrada 4 recuperen fuentes pertinentes de la Vector DB."""
        consultas = [
            ("Consulta 1: Medicamentos", "entrega de medicamentos continuidad del tratamiento EPS gestor farmacéutico", ["ST-510", "ST-325", "ST-207", "ST-418", "ST-540"]),
            ("Consulta 2: No PBS/MIPRES", "medicamentos no incluidos en el plan de beneficios médico tratante MIPRES", ["ST-001", "ST-239", "ST-776", "ST-907"]),
            ("Consulta 3: Citas Especialistas", "asignación de citas médico especialista demora injustificada oportunidad", ["ST-118", "ST-507", "ST-610", "ST-972"]),
            ("Consulta 4: Cirugías e Integralidad", "principio de integralidad autorización de procedimiento cirugía tratamiento médico", ["ST-445", "ST-742", "ST-323", "ST-399", "ST-599"]),
            ("Consulta 5: Urgencias Vitales / Cáncer", "sujetos de especial protección constitucional cáncer quimioterapia menores edad", ["ST-1077", "ST-121", "ST-407", "ST-323", "ST-923"]),
            ("Consulta 6: Transporte y Viáticos", "servicio de transporte acompañante carencia de recursos remisión intermunicipal", ["ST-122", "ST-528", "ST-461", "ST-563", "ST-730"])
        ]
        for name, query, expected_prefixes in consultas:
            res = legal_rag_search(query, top_k=5)
            self.assertGreater(res["total_found"], 0, f"Fallo en {name}: total_found es 0")
            chunk_ids = [r["chunk_id"] for r in res["results"]]
            found = any(any(exp in cid for exp in expected_prefixes) for cid in chunk_ids)
            self.assertTrue(found, f"Fallo en {name}: ninguno de {expected_prefixes} apareció en {chunk_ids}")

if __name__ == "__main__":
    unittest.main()

