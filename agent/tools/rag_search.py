import os
import re
import math
from collections import Counter
import yaml
from agent.core.vector_db import SQLiteVectorDB

CORPUS_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "legal_corpus")
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ampara_vector.db")

class LegalRAG:
    """
    Motor RAG para el Agente AMPARA impulsado por Base de Datos Vectorial en SQLite.
    Combina búsqueda vectorial densa (Embeddings + Cosine Similarity en SQL)
    con búsqueda de precisión léxica (BM25) para un RAG híbrido de alto rendimiento.
    """

    def __init__(self, corpus_dir: str = None, db_path: str = None):
        self.corpus_dir = corpus_dir or CORPUS_ROOT
        self.db_path = db_path or DEFAULT_DB_PATH
        self.vector_db = SQLiteVectorDB(self.db_path)
        self.chunks_cache = []
        self.doc_registry = {}
        self.inverted_index = {}
        self.doc_lengths = []
        self.avg_doc_len = 0.0
        self.is_indexed = False
        self.load_and_index()

    def _parse_yaml_frontmatter(self, file_content: str):
        if file_content.startswith("---"):
            parts = file_content.split("---", 2)
            if len(parts) >= 3:
                try:
                    meta = yaml.safe_load(parts[1]) or {}
                    body = parts[2].strip()
                    return meta, body
                except Exception:
                    pass
        return {}, file_content.strip()

    def _tokenize(self, text: str) -> list:
        text_clean = text.lower()
        accents = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u', 'ñ': 'n'}
        for k, v in accents.items():
            text_clean = text_clean.replace(k, v)
        tokens = re.findall(r'\b[a-z0-9_]{3,}\b', text_clean)
        stopwords = {
            'que', 'con', 'del', 'los', 'las', 'por', 'para', 'una', 'uno', 'unos',
            'como', 'pero', 'sus', 'les', 'este', 'esta', 'estos', 'estas', 'entre',
            'cuando', 'donde', 'cual', 'sobre', 'todo', 'toda', 'todos', 'todas'
        }
        return [t for t in tokens if t not in stopwords]

    def load_and_index(self, force_reload: bool = False):
        if not force_reload and self.vector_db.count_chunks() >= 220:
            # Ya está indexado en la base de datos SQLite con el corpus completo (228 chunks)
            self._load_from_db()
            self.is_indexed = True
            return

        self.vector_db.clear_chunks()
        self.chunks_cache = []
        self.doc_registry = {}

        if not os.path.exists(self.corpus_dir):
            return

        for root, _, files in os.walk(self.corpus_dir):
            for file in files:
                if file.endswith(".md") and file != "README.md":
                    fpath = os.path.join(root, file)
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        raw = f.read()
                    meta, body = self._parse_yaml_frontmatter(raw)
                    doc_id = meta.get("id", os.path.splitext(file)[0])
                    doc_type = meta.get("tipo", "documento")
                    doc_ref = meta.get("referencia") or meta.get("titulo") or doc_id

                    self.doc_registry[doc_id] = {
                        "meta": meta,
                        "ref": doc_ref,
                        "type": doc_type,
                        "path": fpath
                    }

                    if doc_type in ["decreto_reglamentario", "decreto", "ley"]:
                        # Chunking por artículos
                        art_pattern = re.compile(r'(###\s+Artículo\s+[\d]+[^\n]*)(.*?)(?=(?:###\s+Artículo\s+[\d]+)|\Z)', re.DOTALL)
                        matches = art_pattern.findall(body)
                        if matches:
                            for header, content in matches:
                                art_title = header.replace("###", "").strip()
                                art_num_match = re.search(r'Artículo\s+([\d]+)', art_title)
                                art_num = art_num_match.group(1) if art_num_match else "X"
                                chunk_id = f"{doc_id}-ART-{art_num}"
                                full_chunk_text = f"{doc_ref} - {art_title}\n{content.strip()}"
                                chunk_meta = dict(meta)
                                chunk_meta["articulo_numero"] = art_num
                                chunk_meta["referencia_completa"] = f"{doc_ref}, {art_title}"
                                
                                self.vector_db.upsert_chunk(
                                    chunk_id=chunk_id,
                                    doc_id=doc_id,
                                    chunk_type="articulo",
                                    title=f"{doc_ref} - {art_title}",
                                    text=full_chunk_text,
                                    metadata=chunk_meta
                                )
                        else:
                            self.vector_db.upsert_chunk(
                                chunk_id=doc_id,
                                doc_id=doc_id,
                                chunk_type="general",
                                title=doc_ref,
                                text=body,
                                metadata=meta
                            )

                    elif "sentencia" in doc_type or "auto" in doc_type:
                        ratio_match = re.search(r'###\s+Ratio Decidendi[^\n]*\n>(.*?)(?=\n###|\Z)', body, re.DOTALL)
                        if ratio_match:
                            ratio_text = ratio_match.group(1).replace(">", "").strip()
                            self.vector_db.upsert_chunk(
                                chunk_id=f"{doc_id}-RATIO",
                                doc_id=doc_id,
                                chunk_type="ratio_decidendi",
                                title=f"{doc_ref} (Ratio Decidendi)",
                                text=f"Ratio Decidendi de {doc_ref}:\n\"{ratio_text}\"",
                                metadata=meta
                            )

                        regla_juridica = meta.get("regla_juridica")
                        if regla_juridica:
                            self.vector_db.upsert_chunk(
                                chunk_id=f"{doc_id}-REGLA",
                                doc_id=doc_id,
                                chunk_type="regla_juridica",
                                title=f"{doc_ref} (Regla Jurídica)",
                                text=f"Regla Jurídica de {doc_ref}:\n{regla_juridica}",
                                metadata=meta
                            )

                        self.vector_db.upsert_chunk(
                            chunk_id=f"{doc_id}-TEXTO",
                            doc_id=doc_id,
                            chunk_type="jurisprudencia_contexto",
                            title=doc_ref,
                            text=f"{doc_ref}\n{body[:3000]}",
                            metadata=meta
                        )

                    else:
                        # Guías procesales, manuales y doctrina constitucional
                        ratio_match = re.search(r'###\s+Ratio Decidendi[^\n]*\n>(.*?)(?=\n###|\Z)', body, re.DOTALL)
                        if ratio_match:
                            ratio_text = ratio_match.group(1).replace(">", "").strip()
                            self.vector_db.upsert_chunk(
                                chunk_id=f"{doc_id}-RATIO",
                                doc_id=doc_id,
                                chunk_type="ratio_decidendi",
                                title=f"{doc_ref} (Ratio Decidendi)",
                                text=f"Ratio Decidendi de {doc_ref}:\n\"{ratio_text}\"",
                                metadata=meta
                            )
                        regla_juridica = meta.get("regla_juridica")
                        if regla_juridica:
                            self.vector_db.upsert_chunk(
                                chunk_id=f"{doc_id}-REGLA",
                                doc_id=doc_id,
                                chunk_type="regla_juridica",
                                title=f"{doc_ref} (Regla Jurídica)",
                                text=f"Regla Jurídica de {doc_ref}:\n{regla_juridica}",
                                metadata=meta
                            )
                        self.vector_db.upsert_chunk(
                            chunk_id=f"{doc_id}-TEXTO",
                            doc_id=doc_id,
                            chunk_type="guia_procesal",
                            title=doc_ref,
                            text=f"{doc_ref}\n{body[:3500]}",
                            metadata=meta
                        )

        self._load_from_db()
        self.is_indexed = True

    def _load_from_db(self):
        with self.vector_db.get_connection() as conn:
            cursor = conn.execute("SELECT chunk_id, doc_id, chunk_type, title, text, metadata_json FROM legal_chunks")
            self.chunks_cache = []
            for row in cursor.fetchall():
                import json
                meta = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
                self.chunks_cache.append({
                    "chunk_id": row["chunk_id"],
                    "doc_id": row["doc_id"],
                    "chunk_type": row["chunk_type"],
                    "title": row["title"],
                    "text": row["text"],
                    "metadata": meta
                })
                if row["doc_id"] not in self.doc_registry:
                    self.doc_registry[row["doc_id"]] = {
                        "meta": meta,
                        "ref": meta.get("referencia") or meta.get("titulo") or row["doc_id"],
                        "type": row["chunk_type"]
                    }
        self._build_bm25_index()

    def _build_bm25_index(self):
        self.inverted_index = {}
        self.doc_lengths = []
        total_len = 0

        for idx, chunk in enumerate(self.chunks_cache):
            kw = " ".join(chunk["metadata"].get("palabras_clave", []))
            sub = " ".join(chunk["metadata"].get("subtemas", []))
            tema = str(chunk["metadata"].get("tema_principal", ""))
            search_blob = f"{chunk['title']} {tema} {sub} {kw} {chunk['text']}"
            tokens = self._tokenize(search_blob)
            self.doc_lengths.append(len(tokens))
            total_len += len(tokens)

            tf = Counter(tokens)
            for token, count in tf.items():
                if token not in self.inverted_index:
                    self.inverted_index[token] = []
                self.inverted_index[token].append((idx, count))

        self.avg_doc_len = (total_len / len(self.chunks_cache)) if self.chunks_cache else 1.0

    def search(self, query: str, filters: dict = None, top_k: int = 4) -> list:
        # 1. Búsqueda Vectorial nativa en SQLite
        vec_results = self.vector_db.search_vector(query, top_k=top_k * 3, filters=filters)
        vec_scores = {r["chunk_id"]: r["score"] for r in vec_results}

        # 2. Búsqueda Léxica BM25
        query_tokens = self._tokenize(query)
        bm25_scores = {}
        if query_tokens and self.chunks_cache:
            k1 = 1.5
            b = 0.75
            n_chunks = len(self.chunks_cache)
            for token in query_tokens:
                if token in self.inverted_index:
                    postings = self.inverted_index[token]
                    df = len(postings)
                    idf = math.log((n_chunks - df + 0.5) / (df + 0.5) + 1.0)
                    for chunk_idx, tf in postings:
                        cid = self.chunks_cache[chunk_idx]["chunk_id"]
                        doc_len = self.doc_lengths[chunk_idx]
                        tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / self.avg_doc_len)))
                        bm25_scores[cid] = bm25_scores.get(cid, 0.0) + (idf * tf_norm)

        # 3. Fusión Híbrida (Hybrid Score = 0.55 * Vector_Sim + 0.45 * BM25_Norm)
        max_bm25 = max(bm25_scores.values()) if bm25_scores else 1.0
        max_bm25 = max_bm25 if max_bm25 > 0 else 1.0

        all_cids = set(vec_scores.keys()) | set(bm25_scores.keys())
        ranked = []
        chunk_lookup = {c["chunk_id"]: c for c in self.chunks_cache}

        for cid in all_cids:
            chunk = chunk_lookup.get(cid)
            if not chunk:
                continue

            if filters:
                if "doc_id" in filters and chunk["doc_id"] != filters["doc_id"]:
                    continue
                if "chunk_type" in filters and chunk["chunk_type"] != filters["chunk_type"]:
                    continue

            v_score = vec_scores.get(cid, 0.0)
            b_score = (bm25_scores.get(cid, 0.0) / max_bm25)

            # Ponderación híbrida
            hybrid_score = (0.55 * v_score) + (0.45 * b_score)

            # Bonificaciones por ratio y artículo
            if chunk["chunk_type"] == "ratio_decidendi":
                hybrid_score *= 1.25
            elif chunk["chunk_type"] == "articulo":
                hybrid_score *= 1.15

            if hybrid_score > 0:
                ranked.append((chunk, hybrid_score, v_score, b_score))

        ranked.sort(key=lambda x: x[1], reverse=True)
        results = []
        for c, h_score, v_score, b_score in ranked[:top_k]:
            results.append({
                "chunk_id": c["chunk_id"],
                "doc_id": c["doc_id"],
                "title": c["title"],
                "score": round(h_score, 3),
                "vector_score": round(v_score, 3),
                "bm25_score": round(b_score, 3),
                "text": c["text"],
                "chunk_type": c["chunk_type"],
                "referencia": c["metadata"].get("referencia") or c["metadata"].get("titulo") or c["doc_id"],
                "tipo": c["metadata"].get("tipo", ""),
                "decretos_asociados": c["metadata"].get("decretos_asociados", []),
                "regla_juridica": c["metadata"].get("regla_juridica", "")
            })

        return results

    @property
    def chunks(self):
        return self.chunks_cache

_global_rag_engine = None

def get_rag_engine() -> LegalRAG:
    global _global_rag_engine
    if _global_rag_engine is None:
        _global_rag_engine = LegalRAG()
    return _global_rag_engine

def legal_rag_search(query: str, filters: dict = None, top_k: int = 3) -> dict:
    engine = get_rag_engine()
    results = engine.search(query=query, filters=filters, top_k=top_k)

    sources_for_s4 = []
    citable_extracts = []

    for r in results:
        ref_text = r.get("referencia", r["doc_id"])
        if r.get("chunk_type") == "articulo" and "Artículo" in r.get("title", ""):
            art_part = r["title"].split("-")[-1].strip()
            ref_formatted = f"{ref_text}, {art_part}"
        else:
            ref_formatted = ref_text

        sources_for_s4.append({
            "id": r["chunk_id"],
            "ref": ref_formatted
        })

        if r.get("chunk_type") in ["ratio_decidendi", "articulo"]:
            citable_extracts.append({
                "source_id": r["chunk_id"],
                "referencia": ref_formatted,
                "extract": r["text"]
            })

    return {
        "query": query,
        "total_found": len(results),
        "results": results,
        "sources_for_s4": sources_for_s4,
        "citable_extracts": citable_extracts
    }

__all__ = ["LegalRAG", "legal_rag_search", "get_rag_engine"]
