from langchain_core.pydantic_v1 import BaseModel, Field


# from pydantic import BaseModel

class SaveCSV(BaseModel):
    """Save the document analysis as a CSV report."""
    summary: str = Field(..., description="Summary of the Page")
    include_or_exclude: str = Field(..., description="Include or Exclude")
    reason: str = Field(..., description="Reason")
