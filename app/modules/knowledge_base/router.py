from fastapi import (
    APIRouter,
    Depends,
    File,
    Query,
    UploadFile,
)
from fastapi.responses import JSONResponse

from app.database.models.user import User
from app.modules.auth.dependencies import (
    get_current_admin_user,
    get_current_user,
)
from app.modules.knowledge_base.schema import (
    ReindexRequest,
)
from app.modules.knowledge_base.service import (
    KnowledgeBaseService,
)
from app.schemas.response import APIResponse

router = APIRouter()
service = KnowledgeBaseService()


@router.post(
    "/upload",
    response_model=APIResponse,
    summary="Upload a document",
)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Query(default="general"),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "No file provided"},
        )

    content = await file.read()
    result = await service.upload_document(
        file_content=content,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        doc_type=doc_type,
        user=current_user,
    )

    return APIResponse(
        message="Document uploaded and processed",
        data=result.model_dump(),
    )


@router.get(
    "/documents",
    response_model=APIResponse,
    summary="List all documents",
)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    doc_type: str = Query(None),
    current_user: User = Depends(get_current_user),
):
    result = await service.list_documents(skip, limit, doc_type)
    return APIResponse(
        message="Documents retrieved",
        data={
            "documents": [
                d.model_dump() for d in result.documents
            ],
            "total": result.total,
        },
    )


@router.get(
    "/documents/{document_id}",
    response_model=APIResponse,
    summary="Get document details",
)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
):
    result = await service.get_document(document_id)
    return APIResponse(
        message="Document retrieved",
        data=result.model_dump(),
    )


@router.delete(
    "/documents/{document_id}",
    response_model=APIResponse,
    summary="Delete a document",
)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
):
    await service.delete_document(document_id)
    return APIResponse(message="Document deleted")


@router.post(
    "/reindex",
    response_model=APIResponse,
    summary="Re-index embeddings",
)
async def reindex_documents(
    data: ReindexRequest,
    current_user: User = Depends(get_current_user),
):
    result = await service.reindex_documents(
        data.document_id, data.full_reindex
    )
    return APIResponse(
        message="Reindex completed",
        data=result,
    )


@router.get(
    "/search",
    response_model=APIResponse,
    summary="Search knowledge base",
)
async def search_knowledge_base(
    q: str = Query(..., min_length=1),
    doc_type: str = Query(None),
    top_k: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
):
    try:
        from app.ai.rag.hybrid import HybridSearchService

        search_service = HybridSearchService()
        results = await search_service.search(
            query=q,
            top_k=top_k,
            doc_type=doc_type,
        )

        return APIResponse(
            message="Search results",
            data={
                "results": [
                    {
                        "content": r["content"],
                        "score": r["score"],
                        "source": r.get("source", ""),
                        "doc_type": r.get("doc_type", ""),
                    }
                    for r in results
                ]
            },
        )
    except Exception as e:
        return APIResponse(
            message=f"Search error: {str(e)}",
            data={"results": []},
        )


@router.get(
    "/search/explain",
    response_model=APIResponse,
    summary="Search with full pipeline breakdown",
)
async def search_explain(
    q: str = Query(..., min_length=1),
    doc_type: str = Query(None),
    top_k: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
):
    import time

    pipeline = {}
    total_start = time.perf_counter()

    # Step 1: Embedding
    step_start = time.perf_counter()
    try:
        from app.ai.rag.embeddings import EmbeddingService

        embedder = EmbeddingService()
        query_embedding = await embedder.embed_query(q)
        pipeline["embedding"] = {
            "status": "completed",
            "time_ms": round((time.perf_counter() - step_start) * 1000, 2),
            "dimension": len(query_embedding),
            "model": embedder.model_name,
        }
    except Exception as e:
        pipeline["embedding"] = {
            "status": "error",
            "time_ms": round((time.perf_counter() - step_start) * 1000, 2),
            "error": str(e),
        }
        return APIResponse(
            message="Embedding failed",
            data={"pipeline": pipeline},
        )

    # Step 2: Dense vector search
    step_start = time.perf_counter()
    dense_results = []
    try:
        from app.ai.rag.vector_store import VectorStoreService

        vector_store = VectorStoreService()
        dense_results = vector_store.search(query_embedding, top_k=top_k * 2)
        pipeline["dense_search"] = {
            "status": "completed",
            "time_ms": round((time.perf_counter() - step_start) * 1000, 2),
            "results_found": len(dense_results),
            "index_size": vector_store.index.ntotal if vector_store.index else 0,
            "top_scores": [
                {"id": r.get("id", ""), "score": round(r.get("score", 0), 4), "source": r.get("metadata", {}).get("filename", "")}
                for r in dense_results[:5]
            ],
        }
    except Exception as e:
        pipeline["dense_search"] = {
            "status": "error",
            "time_ms": round((time.perf_counter() - step_start) * 1000, 2),
            "error": str(e),
        }

    # Step 3: BM25 sparse search
    step_start = time.perf_counter()
    sparse_results = []
    try:
        from app.ai.rag.bm25 import BM25Retriever

        bm25 = BM25Retriever()
        all_docs = vector_store.documents if dense_results else []
        if all_docs:
            bm25.index_documents(all_docs)
            sparse_results = bm25.search(q, top_k=top_k * 2)
        pipeline["bm25_search"] = {
            "status": "completed",
            "time_ms": round((time.perf_counter() - step_start) * 1000, 2),
            "results_found": len(sparse_results),
            "documents_indexed": len(all_docs),
            "query_tokens": bm25._tokenize(q),
            "top_scores": [
                {"id": r.get("id", ""), "bm25_score": round(r.get("bm25_score", 0), 4), "source": r.get("metadata", {}).get("filename", "")}
                for r in sparse_results[:5]
            ],
        }
    except Exception as e:
        pipeline["bm25_search"] = {
            "status": "error",
            "time_ms": round((time.perf_counter() - step_start) * 1000, 2),
            "error": str(e),
        }

    # Step 4: Reciprocal Rank Fusion
    step_start = time.perf_counter()
    fused_results = []
    try:
        from app.ai.rag.hybrid import HybridSearchService

        hybrid = HybridSearchService()
        fused_results = hybrid._reciprocal_rank_fusion(dense_results, sparse_results)
        if doc_type:
            fused_results = [
                r for r in fused_results
                if r.get("doc_type") == doc_type
                or r.get("metadata", {}).get("doc_type") == doc_type
            ]
        pipeline["fusion"] = {
            "status": "completed",
            "time_ms": round((time.perf_counter() - step_start) * 1000, 2),
            "results_count": len(fused_results),
            "dense_weight": hybrid.dense_weight,
            "sparse_weight": hybrid.sparse_weight,
            "rrf_k": 60,
        }
    except Exception as e:
        pipeline["fusion"] = {
            "status": "error",
            "time_ms": round((time.perf_counter() - step_start) * 1000, 2),
            "error": str(e),
        }

    # Step 5: Reranking
    step_start = time.perf_counter()
    reranked_results = fused_results[:top_k]
    try:
        from app.ai.rag.reranker import CrossEncoderReranker

        reranker = CrossEncoderReranker()
        reranked_results = await reranker.rerank(q, fused_results, top_k=top_k)
        pipeline["reranking"] = {
            "status": "completed",
            "time_ms": round((time.perf_counter() - step_start) * 1000, 2),
            "model": reranker.model_name,
            "input_count": len(fused_results),
            "output_count": len(reranked_results),
        }
    except Exception as e:
        pipeline["reranking"] = {
            "status": "skipped",
            "time_ms": round((time.perf_counter() - step_start) * 1000, 2),
            "reason": str(e),
        }

    # Step 6: Compression
    step_start = time.perf_counter()
    compressed_context = ""
    try:
        from app.ai.rag.compressor import ContextCompressor

        compressor = ContextCompressor()
        compressed_context = await compressor.compress(q, reranked_results)
        pipeline["compression"] = {
            "status": "completed",
            "time_ms": round((time.perf_counter() - step_start) * 1000, 2),
            "original_length": sum(len(r.get("text", "")) for r in reranked_results),
            "compressed_length": len(compressed_context),
            "compression_ratio": round(
                len(compressed_context) / max(sum(len(r.get("text", "")) for r in reranked_results), 1), 2
            ),
        }
    except Exception as e:
        pipeline["compression"] = {
            "status": "error",
            "time_ms": round((time.perf_counter() - step_start) * 1000, 2),
            "error": str(e),
        }

    total_ms = round((time.perf_counter() - total_start) * 1000, 2)

    results = []
    for r in reranked_results:
        results.append({
            "id": r.get("id", ""),
            "text": r.get("text", ""),
            "content": r.get("text", ""),
            "score": round(r.get("score", 0), 4),
            "rerank_score": round(r.get("rerank_score", 0), 4) if "rerank_score" in r else None,
            "bm25_score": round(r.get("bm25_score", 0), 4) if "bm25_score" in r else None,
            "source": r.get("metadata", {}).get("filename", r.get("source", "")),
            "doc_type": r.get("metadata", {}).get("doc_type", r.get("doc_type", "")),
            "page": r.get("metadata", {}).get("page"),
            "chunk_index": r.get("metadata", {}).get("chunk_index"),
        })

    return APIResponse(
        message="Search completed",
        data={
            "query": q,
            "total_time_ms": total_ms,
            "results_count": len(results),
            "pipeline": pipeline,
            "results": results,
            "compressed_context": compressed_context[:500] + "..." if len(compressed_context) > 500 else compressed_context,
        },
    )
