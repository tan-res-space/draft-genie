"""
Vector API endpoints
"""
from typing import List
from fastapi import APIRouter, HTTPException, Query, Depends, status

from app.models.correction_vector import CorrectionVectorResponse
from app.services.vector_service import VectorService, get_vector_service
from app.services.draft_service import DraftService, get_draft_service
from app.repositories.draft_repository import DraftRepository
from app.db.mongodb import get_database
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/vectors", tags=["vectors"])


async def get_vector_service_dependency() -> VectorService:
    """Dependency to get VectorService instance"""
    db = await get_database()
    draft_repository = DraftRepository(db)
    draft_service = get_draft_service(draft_repository)
    return get_vector_service(db, draft_service)


@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_vectors(
    draft_id: str = Query(..., description="Draft ID to generate vector for"),
    service: VectorService = Depends(get_vector_service_dependency),
) -> dict:
    """
    Generate correction vector for a specific draft
    
    Extracts correction patterns and generates embedding
    """
    try:
        logger.info(f"POST /api/v1/vectors/generate - draft_id={draft_id}")
        
        # Get draft
        draft = await service.draft_service.get_draft_by_id(draft_id)
        if not draft:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Draft {draft_id} not found",
            )
        
        # Generate vector
        vector = await service.generate_vector_for_draft(draft)
        
        return {
            "message": "Successfully generated correction vector",
            "vector_id": vector.vector_id,
            "draft_id": vector.draft_id,
            "speaker_id": vector.speaker_id,
            "total_corrections": vector.total_corrections,
            "unique_patterns": vector.unique_patterns,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating vector: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate vector: {str(e)}",
        )


@router.post("/generate/speaker/{speaker_id}", status_code=status.HTTP_201_CREATED)
async def generate_vectors_for_speaker(
    speaker_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of drafts"),
    service: VectorService = Depends(get_vector_service_dependency),
) -> dict:
    """
    Generate correction vectors for all unprocessed drafts of a speaker
    """
    try:
        logger.info(f"POST /api/v1/vectors/generate/speaker/{speaker_id}")
        
        vectors = await service.generate_vectors_for_speaker(speaker_id, limit)
        
        return {
            "message": f"Successfully generated {len(vectors)} correction vectors",
            "speaker_id": speaker_id,
            "count": len(vectors),
            "vector_ids": [v.vector_id for v in vectors],
        }
        
    except Exception as e:
        logger.error(f"Error generating vectors for speaker: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate vectors: {str(e)}",
        )


@router.get("/{vector_id}", response_model=CorrectionVectorResponse)
async def get_vector(
    vector_id: str,
    service: VectorService = Depends(get_vector_service_dependency),
) -> CorrectionVectorResponse:
    """
    Get a specific correction vector by ID
    """
    try:
        logger.info(f"GET /api/v1/vectors/{vector_id}")
        
        vector = await service.get_vector_by_id(vector_id)
        
        if not vector:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vector {vector_id} not found",
            )
        
        return CorrectionVectorResponse(
            _id=str(vector.id),
            vector_id=vector.vector_id,
            speaker_id=vector.speaker_id,
            draft_id=vector.draft_id,
            patterns=vector.patterns,
            total_corrections=vector.total_corrections,
            unique_patterns=vector.unique_patterns,
            category_counts=vector.category_counts,
            qdrant_point_id=vector.qdrant_point_id,
            embedding_model=vector.embedding_model,
            metadata=vector.metadata,
            created_at=vector.created_at,
            updated_at=vector.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vector: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vector: {str(e)}",
        )


@router.get("/speaker/{speaker_id}", response_model=List[CorrectionVectorResponse])
async def get_speaker_vectors(
    speaker_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: VectorService = Depends(get_vector_service_dependency),
) -> List[CorrectionVectorResponse]:
    """
    Get all correction vectors for a specific speaker
    """
    try:
        logger.info(f"GET /api/v1/vectors/speaker/{speaker_id}")
        
        vectors = await service.get_vectors_by_speaker(speaker_id, skip, limit)
        
        return [
            CorrectionVectorResponse(
                _id=str(v.id),
                vector_id=v.vector_id,
                speaker_id=v.speaker_id,
                draft_id=v.draft_id,
                patterns=v.patterns,
                total_corrections=v.total_corrections,
                unique_patterns=v.unique_patterns,
                category_counts=v.category_counts,
                qdrant_point_id=v.qdrant_point_id,
                embedding_model=v.embedding_model,
                metadata=v.metadata,
                created_at=v.created_at,
                updated_at=v.updated_at,
            )
            for v in vectors
        ]
        
    except Exception as e:
        logger.error(f"Error getting speaker vectors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get speaker vectors: {str(e)}",
        )


@router.get("/speaker/{speaker_id}/statistics")
async def get_speaker_statistics(
    speaker_id: str,
    service: VectorService = Depends(get_vector_service_dependency),
) -> dict:
    """
    Get statistics for a speaker's correction vectors
    """
    try:
        logger.info(f"GET /api/v1/vectors/speaker/{speaker_id}/statistics")
        
        stats = await service.get_speaker_statistics(speaker_id)
        
        return {
            "speaker_id": speaker_id,
            **stats,
        }
        
    except Exception as e:
        logger.error(f"Error getting speaker statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get speaker statistics: {str(e)}",
        )


@router.post("/search")
async def search_similar_vectors(
    speaker_id: str = Query(..., description="Speaker ID to search for"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    score_threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity score"),
    service: VectorService = Depends(get_vector_service_dependency),
) -> dict:
    """
    Search for similar correction patterns
    
    Uses the speaker's recent patterns to find similar patterns from other speakers
    """
    try:
        logger.info(f"POST /api/v1/vectors/search - speaker_id={speaker_id}")
        
        results = await service.search_similar_vectors(
            speaker_id=speaker_id,
            limit=limit,
            score_threshold=score_threshold,
        )
        
        return {
            "speaker_id": speaker_id,
            "count": len(results),
            "results": results,
        }
        
    except Exception as e:
        logger.error(f"Error searching vectors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search vectors: {str(e)}",
        )

