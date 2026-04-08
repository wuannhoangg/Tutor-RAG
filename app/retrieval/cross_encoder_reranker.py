from typing import Any, Dict, List
from app.core import logging

logger = logging.logger.getChild("cross_encoder_reranker")

class CrossEncoderReranker:
    """
    Reranker using a Cross-Encoder model for high-accuracy semantic scoring.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        self.model = None
        try:
            from sentence_transformers import CrossEncoder
            # Model này nhỏ gọn, chạy tốt trên CPU và rất chuẩn cho bài toán RAG
            self.model = CrossEncoder(model_name)
            logger.info("Loaded CrossEncoder model: %s", model_name)
        except Exception as exc:
            logger.warning("Failed to load CrossEncoder model. Reason: %s", exc)

    def re_rank(self, candidates: List[Dict[str, Any]], query_text: str, top_k: int) -> List[Dict[str, Any]]:
        if not candidates or not query_text.strip():
            return []

        if self.model is None:
            logger.warning("CrossEncoder is not available. Bypassing reranking.")
            return candidates[:top_k]

        # Chuẩn bị input cho CrossEncoder: List các cặp (Query, Document)
        pairs = []
        for candidate in candidates:
            payload = candidate.get("payload", {}) or {}
            text = payload.get("text", "")
            pairs.append((query_text, text))

        # Predict điểm số
        scores = self.model.predict(pairs)

        reranked: List[Dict[str, Any]] = []
        for i, candidate in enumerate(candidates):
            item = dict(candidate)
            item["score"] = float(scores[i])
            
            # Đưa điểm Cross-Encoder vào metadata để sau này evaluation
            if "payload" in item:
                item["payload"]["cross_encoder_score"] = float(scores[i])
            
            reranked.append(item)

        # Sắp xếp lại theo điểm của Cross-Encoder
        reranked.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        
        return reranked[:top_k]