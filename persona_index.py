"""
Shared retrieval helpers for Tasks 4 and 5.

    from persona_index import PersonaIndex
    idx = PersonaIndex("task4_output")
    idx.persona("S1-P3")                         # profile dict
    idx.query("S1-P3", announcement_text, k=8)   # that persona's own most relevant real posts
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd


def embed_corpus(texts, backend, model_name="all-MiniLM-L6-v2", outdir=None, seed=42):
    texts = [t[:1200] for t in texts]
    if backend == "st":
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer(model_name)
        vecs = m.encode(texts, batch_size=128, show_progress_bar=True, normalize_embeddings=True)
        return np.asarray(vecs, dtype="float32"), {"backend": "st", "model": model_name}
    import joblib
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import normalize
    tf = TfidfVectorizer(max_features=30000, ngram_range=(1, 2), min_df=2, max_df=0.5, stop_words="english", sublinear_tf=True)
    X = tf.fit_transform(texts)
    svd = TruncatedSVD(n_components=max(2, min(150, X.shape[1] - 1, X.shape[0] - 1)), random_state=seed).fit(X)
    if outdir:
        joblib.dump((tf, svd), Path(outdir) / "tfidf_models.joblib")
    return normalize(svd.transform(X)).astype("float32"), {"backend": "tfidf"}


def embed_query(text, meta, index_dir):
    if meta["backend"] == "st":
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer(meta["model"])
        return np.asarray(m.encode([text[:1200]], normalize_embeddings=True)[0], dtype="float32")
    import joblib
    from sklearn.preprocessing import normalize
    tf, svd = joblib.load(Path(index_dir) / "tfidf_models.joblib")
    return normalize(svd.transform(tf.transform([text])))[0].astype("float32")


class PersonaIndex:
    def __init__(self, outdir):
        self.dir = Path(outdir)
        self.meta = json.loads((self.dir / "index" / "meta.json").read_text())
        self.rows = pd.read_csv(self.dir / "index" / "rows.csv")
        self.emb = np.load(self.dir / "index" / "embeddings.npy")
        self.personas = {p["persona_id"]: p for p in json.loads((self.dir / "personas.json").read_text())}
        self._by_persona = {pid: g.index.to_numpy() for pid, g in self.rows.groupby("persona_id")}
        self._model = None

    def persona(self, persona_id):
        return self.personas[persona_id]

    def query(self, persona_id, text, k=8):
        """Top-k most similar real posts from THIS persona's own evidence pool (all dated before the cutoff)."""
        idx = self._by_persona[persona_id]
        q = embed_query(text, self.meta, self.dir / "index")
        sims = self.emb[idx] @ q
        top = idx[np.argsort(-sims)[:k]]
        out = self.rows.loc[top, ["uid", "created_utc", "text"]].to_dict("records")
        for r, i in zip(out, top):
            r["similarity"] = round(float(self.emb[i] @ q), 3)
        return out
