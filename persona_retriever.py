#!/usr/bin/env python3
"""
Retrieval store for the Task 4 personas (local, free: numpy cosine search over MiniLM embeddings).

    from persona_retriever import Retriever
    r = Retriever("personas")
    r.search("s1_p1", "Spotify is raising Premium prices", k=8)   # -> list of dicts (uid, created_utc, text, sim)

Each persona searches ONLY its own pool of pre-cutoff posts.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd


class Retriever:
    def __init__(self, root="personas"):
        root = Path(root)
        self.rows = pd.read_parquet(root / "index" / "rows.parquet")
        self.emb = np.load(root / "index" / "embeddings.npy")
        self.meta = json.loads((root / "index" / "meta.json").read_text())
        self._by_persona = {p: np.where(self.rows.persona_id.values == p)[0] for p in self.rows.persona_id.unique()}
        self._model = None

    def embed(self, text):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.meta["embedding_model"])
        return self._model.encode([text[:1200]], normalize_embeddings=True)[0].astype("float32")

    def search(self, persona_id, query, k=8, query_vec=None):
        idx = self._by_persona[persona_id]
        q = self.embed(query) if query_vec is None else query_vec
        sims = self.emb[idx] @ q
        top = idx[np.argsort(-sims)[:k]]
        out = self.rows.iloc[top][["uid", "created_utc", "text"]].to_dict("records")
        for r, s in zip(out, np.sort(sims)[::-1][:k]):
            r["sim"] = float(s)
        return out


if __name__ == "__main__":
    r = Retriever(Path(__file__).resolve().parent / "personas")
    for hit in r.search("s1_p1", "Spotify Premium is getting more expensive", k=3):
        print(f"{hit['sim']:.2f} {hit['created_utc'][:10]} {hit['text'][:120]}")
