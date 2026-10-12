import unittest
import numpy as np
from agent.core.vector_db import SQLiteVectorDB, DenseEmbeddingModel, cosine_similarity

class TestSQLiteVectorDB(unittest.TestCase):
    def setUp(self):
        self.db = SQLiteVectorDB(":memory:")

    def test_dense_embedding_generation(self):
        model = DenseEmbeddingModel(dim=256)
        vec1 = model.embed("falta de entrega de medicamento para hipertensión")
        vec2 = model.embed("suministro urgente de fármacos antihipertensivos")
        vec3 = model.embed("reparto de tutela en juzgado administrativo")

        self.assertEqual(len(vec1), 256)
        self.assertAlmostEqual(float(np.linalg.norm(vec1)), 1.0, places=4)

        sim_meds = float(np.dot(vec1, vec2))
        sim_diff = float(np.dot(vec1, vec3))
        self.assertGreater(sim_meds, sim_diff)

    def test_sqlite_vector_search(self):
        self.db.upsert_chunk(
            chunk_id="TEST-1",
            doc_id="DOC-1",
            chunk_type="articulo",
            title="Artículo de Medicamentos",
            text="Obligación de suministrar medicamentos continuos al paciente.",
            metadata={"tema": "medicamento"}
        )
        self.db.upsert_chunk(
            chunk_id="TEST-2",
            doc_id="DOC-2",
            chunk_type="articulo",
            title="Artículo de Competencia",
            text="Los jueces municipales conocen en primera instancia.",
            metadata={"tema": "reparto"}
        )

        res = self.db.search_vector("suministro de pastillas o medicamentos", top_k=1)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["chunk_id"], "TEST-1")

if __name__ == "__main__":
    unittest.main()
