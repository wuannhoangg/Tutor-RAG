from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field

class IngestionResponseData(BaseModel):
    """Data payload returned after a successful document ingestion."""
    
    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(description="The unique ID of the ingested document.")
    chunk_count: int = Field(description="Number of chunks successfully generated and indexed.")
    status: str = Field(default="indexed", description="Final status of the document.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Basic document metadata.")

class IngestionResponse(BaseModel):
    """Standardized API response for the upload endpoint."""
    
    success: bool = True
    message: str = "File uploaded and ingested successfully."
    data: IngestionResponseData