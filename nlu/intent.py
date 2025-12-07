import math
from typing import Dict, List, Tuple

from .preprocess import tokenize_and_map

DEFAULT_INTENT_THRESHOLD = 0.3


def _compute_idf(samples: List[List[str]]) -> Dict[str, float]:
    df: Dict[str, int] = {}
    n_docs = len(samples)

    for toks in samples:
        seen = set(toks)
        for t in seen:
            df[t] = df.get(t, 0) + 1

    idf: Dict[str, float] = {}
    for t, c in df.items():
        idf[t] = math.log((1 + n_docs) / (1 + c)) + 1.0
    return idf


def _tf(toks: List[str]) -> Dict[str, float]:
    counts: Dict[str, int] = {}
    for t in toks:
        counts[t] = counts.get(t, 0) + 1

    total = float(len(toks)) or 1.0
    return {t: c / total for t, c in counts.items()}


def _centroid(vecs: List[Dict[str, float]]) -> Dict[str, float]:
    agg: Dict[str, float] = {}
    for v in vecs:
        for k, val in v.items():
            agg[k] = agg.get(k, 0.0) + val

    norm = math.sqrt(sum(v * v for v in agg.values())) or 1.0
    return {k: v / norm for k, v in agg.items()}


def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a

    s = 0.0
    for k, va in a.items():
        vb = b.get(k)
        if vb is not None:
            s += va * vb
    return s


class IntentDetector:
    def __init__(
            self,
            intent_samples: Dict[str, List[List[str]]],
            intent_keyword_backoff: Dict[str, str],
            threshold: float = DEFAULT_INTENT_THRESHOLD,
    ) -> None:
        self.intent_samples = intent_samples
        self.threshold = threshold

        self.idf: Dict[str, float] = {}
        self.intent_centroids: Dict[str, Dict[str, float]] = {}
        self._build_intent_centroids()

    def _tfidf_vec(self, toks: List[str]) -> Dict[str, float]:
        tf = _tf(toks)
        vec = {t: tf[t] * self.idf.get(t, 0.0) for t in tf}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: v / norm for t, v in vec.items()}

    def _build_intent_centroids(self) -> None:
        all_samples: List[List[str]] = []
        for samples in self.intent_samples.values():
            all_samples.extend(samples)

        self.idf = _compute_idf(all_samples) if all_samples else {}

        centroids: Dict[str, Dict[str, float]] = {}
        for intent, samples in self.intent_samples.items():
            vecs = [self._tfidf_vec(s) for s in samples]
            centroids[intent] = _centroid(vecs) if vecs else {}

        self.intent_centroids = centroids

    def detect(
            self, text: str, synonym_map: Dict[str, str], normalize_for_kw_fn
    ) -> Tuple[str, float]:
        q_tokens = tokenize_and_map(text, synonym_map)
        q_vec = self._tfidf_vec(q_tokens)

        best_intent = ""
        best_score = 0.0
        for intent, centroid in self.intent_centroids.items():
            score = (
                    _cosine(q_vec, centroid)
            )
            if score > best_score:
                best_score = score
                best_intent = intent

        if best_intent and best_score >= self.threshold:
            return best_intent, best_score
        return "fallback", best_score
