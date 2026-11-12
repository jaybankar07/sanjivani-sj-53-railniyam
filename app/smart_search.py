from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.models import Record


class SmartSearch:
    def __init__(self, records: list[Record]):
        self.records = records
        self.vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vec.fit_transform([r.text() for r in records])

    def search(self, query: str, top_k: int = 5) -> list[tuple[Record, float]]:
        scores = cosine_similarity(self.vec.transform([query]), self.matrix).ravel()
        ranked = sorted(zip(self.records, scores), key=lambda x: x[1], reverse=True)
        return [(r, float(s)) for r, s in ranked[:top_k] if s > 0]
