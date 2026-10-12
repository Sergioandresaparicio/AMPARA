import sqlite3
import json
import os
import hashlib
import numpy as np

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ampara_vector.db")

def cosine_similarity(blob_a, blob_b):
    if blob_a is None or blob_b is None:
        return 0.0
    a = np.frombuffer(blob_a, dtype=np.float32)
    b = np.frombuffer(blob_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

class DenseEmbeddingModel:
    """
    Generador de embeddings densos de 256 dimensiones basado en proyecciones
    semánticas y n-gramas sub-palabra con normalización L2.
    100% local, determinista, ultrarrápido y sin dependencias externas pesadas.
    """
    def __init__(self, dim: int = 256):
        self.dim = dim

    def embed(self, text: str) -> np.ndarray:
        if not text:
            return np.zeros(self.dim, dtype=np.float32)
        
        # Limpieza básica
        text_clean = text.lower()
        accents = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u', 'ñ': 'n'}
        for k, v in accents.items():
            text_clean = text_clean.replace(k, v)

        vec = np.zeros(self.dim, dtype=np.float32)
        words = text_clean.split()
        
        # Ponderar palabras completas y n-gramas de caracteres (3 a 5 caracteres)
        for w in words:
            # Hash de palabra completa
            h_val = int(hashlib.md5(w.encode('utf-8')).hexdigest()[:8], 16)
            idx = h_val % self.dim
            sign = 1.0 if (h_val & 1) else -1.0
            vec[idx] += sign * 2.0

            # Subwords
            if len(w) >= 3:
                for n in range(3, min(6, len(w) + 1)):
                    for i in range(len(w) - n + 1):
                        sub = w[i:i+n]
                        h_sub = int(hashlib.md5(sub.encode('utf-8')).hexdigest()[:8], 16)
                        idx_sub = h_sub % self.dim
                        sign_sub = 1.0 if (h_sub & 1) else -1.0
                        vec[idx_sub] += sign_sub * 0.5

        # Normalización L2
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.astype(np.float32)

class SQLiteVectorDB:
    """
    Base de datos vectorial implementada sobre SQLite (MySQL Lite local)
    para el almacenamiento semántico del corpus jurídico y expedientes de AMPARA.
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self._mem_conn = None
        if self.db_path != ":memory:":
            dirname = os.path.dirname(self.db_path)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
        else:
            self._mem_conn = sqlite3.connect(":memory:")
            self._mem_conn.row_factory = sqlite3.Row
            self._mem_conn.create_function("cosine_sim", 2, cosine_similarity)
        self.embedder = DenseEmbeddingModel(dim=256)
        self._init_database()

    def get_connection(self):
        if self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.create_function("cosine_sim", 2, cosine_similarity)
        return conn

    def _init_database(self):
        with self.get_connection() as conn:
            # Tabla Vectorial de Fragmentos Jurídicos (RAG)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS legal_chunks (
                chunk_id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                chunk_type TEXT,
                title TEXT,
                text TEXT,
                metadata_json TEXT,
                embedding BLOB
            )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc ON legal_chunks(doc_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_type ON legal_chunks(chunk_type)")

            # Tabla de Casos y Expedientes (Tool 5: Case Tracker)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                patient_name TEXT,
                eps_name TEXT,
                case_type TEXT,
                urgency_level TEXT,
                phase TEXT,
                facts_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

    def upsert_chunk(self, chunk_id: str, doc_id: str, chunk_type: str, title: str, text: str, metadata: dict, embedding: np.ndarray = None):
        if embedding is None:
            # Combinar título, metadatos y texto para enriquecer el vector
            kw = " ".join(metadata.get("palabras_clave", []))
            sub = " ".join(metadata.get("subtemas", []))
            tema = str(metadata.get("tema_principal", ""))
            content_to_embed = f"{title} {tema} {sub} {kw} {text}"
            embedding = self.embedder.embed(content_to_embed)

        emb_blob = embedding.tobytes()
        meta_str = json.dumps(metadata, ensure_ascii=False)

        with self.get_connection() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO legal_chunks (chunk_id, doc_id, chunk_type, title, text, metadata_json, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (chunk_id, doc_id, chunk_type, title, text, meta_str, emb_blob))

    def search_vector(self, query: str, top_k: int = 5, filters: dict = None) -> list:
        query_vec = self.embedder.embed(query)
        query_blob = query_vec.tobytes()

        sql = "SELECT chunk_id, doc_id, chunk_type, title, text, metadata_json, cosine_sim(embedding, ?) as similarity FROM legal_chunks"
        params = [query_blob]
        where_clauses = []

        if filters:
            if "doc_id" in filters:
                where_clauses.append("doc_id = ?")
                params.append(filters["doc_id"])
            if "chunk_type" in filters:
                where_clauses.append("chunk_type = ?")
                params.append(filters["chunk_type"])

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        sql += " ORDER BY similarity DESC LIMIT ?"
        params.append(top_k)

        results = []
        with self.get_connection() as conn:
            cursor = conn.execute(sql, params)
            for row in cursor.fetchall():
                meta = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
                results.append({
                    "chunk_id": row["chunk_id"],
                    "doc_id": row["doc_id"],
                    "chunk_type": row["chunk_type"],
                    "title": row["title"],
                    "text": row["text"],
                    "score": round(float(row["similarity"]), 4),
                    "metadata": meta,
                    "referencia": meta.get("referencia") or meta.get("titulo") or row["doc_id"],
                    "regla_juridica": meta.get("regla_juridica", "")
                })
        return results

    def count_chunks(self) -> int:
        with self.get_connection() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM legal_chunks")
            return cur.fetchone()[0]

    def clear_chunks(self):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM legal_chunks")

__all__ = ["SQLiteVectorDB", "DenseEmbeddingModel", "cosine_similarity"]
