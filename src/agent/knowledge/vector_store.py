# -*- coding: utf-8 -*-
"""
Chroma 向量库封装
=================
提供本地向量存储能力，支持文档嵌入与语义检索
降级方案：当 Chroma 不可用时使用内存字典模拟
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path

# 向量库持久化路径
_CHROMA_PATH = str(Path(__file__).resolve().parent.parent.parent.parent / "data" / "chroma_db")


class SimpleVectorStore:
    """
    简易向量存储（Chroma 不可用时的降级方案）
    使用 TF-IDF 简单匹配模拟语义检索
    """

    def __init__(self, collection_name: str = "default"):
        self.collection_name = collection_name
        self._documents: List[Dict[str, Any]] = []
        self._metadatas: List[Dict[str, Any]] = []

    def add_documents(self, documents: List[str], metadatas: Optional[List[Dict]] = None):
        """添加文档到向量库"""
        for i, doc in enumerate(documents):
            meta = metadatas[i] if metadatas and i < len(metadatas) else {}
            self._documents.append(doc)
            self._metadatas.append(meta)

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """基于关键词匹配的简单检索"""
        if not self._documents:
            return []

        results = []
        query_lower = query.lower()
        query_chars = set(query_lower.replace(" ", ""))

        for i, doc in enumerate(self._documents):
            doc_lower = doc.lower()
            # 计算简单相似度：字符重叠比例
            doc_chars = set(doc_lower.replace(" ", ""))
            if not doc_chars:
                continue
            overlap = len(query_chars & doc_chars) / max(len(query_chars), 1)

            # 关键词加分
            keywords = query_lower.split()
            keyword_hits = sum(1 for kw in keywords if kw in doc_lower)
            score = overlap * 0.5 + (keyword_hits / max(len(keywords), 1)) * 0.5

            if score > 0.1:
                results.append({
                    "content": doc,
                    "metadata": self._metadatas[i] if i < len(self._metadatas) else {},
                    "score": round(score, 3),
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def count(self) -> int:
        return len(self._documents)

    def clear(self):
        self._documents.clear()
        self._metadatas.clear()


class ChromaVectorStore:
    """Chroma 向量库封装"""

    def __init__(self, collection_name: str = "default"):
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._init_chroma()

    def _init_chroma(self):
        """初始化 Chroma 客户端"""
        try:
            import chromadb
            from chromadb.config import Settings
            os.makedirs(_CHROMA_PATH, exist_ok=True)
            self._client = chromadb.PersistentClient(path=_CHROMA_PATH)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except ImportError:
            raise ImportError("chromadb 未安装，将使用 SimpleVectorStore 降级方案")

    def add_documents(self, documents: List[str], metadatas: Optional[List[Dict]] = None,
                      ids: Optional[List[str]] = None):
        """添加文档"""
        if not self._collection:
            raise RuntimeError("Chroma 未初始化")
        if ids is None:
            import hashlib
            ids = [hashlib.md5(d.encode()).hexdigest()[:12] for d in documents]
        self._collection.add(
            documents=documents,
            metadatas=metadatas or [{}] * len(documents),
            ids=ids,
        )

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """语义检索"""
        if not self._collection:
            return []
        results = self._collection.query(query_texts=[query], n_results=top_k)
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]
        return [
            {"content": d, "metadata": m, "score": round(1 - dist, 3)}
            for d, m, dist in zip(docs, metas, dists)
        ]

    def count(self) -> int:
        if not self._collection:
            return 0
        return self._collection.count()


def get_vector_store(collection_name: str = "default"):
    """工厂方法：优先使用 Chroma，不可用时降级"""
    try:
        return ChromaVectorStore(collection_name)
    except (ImportError, Exception):
        return SimpleVectorStore(collection_name)
