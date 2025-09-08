"""
Shared Pydantic models for wine data extraction with per-field sources.

These models define the structure for wine data with inline sources,
used by both Jina DeepSearch and OpenAI extraction scripts.
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field


class Source(BaseModel):
    """A source reference with URL and verbatim extract."""

    link: str = Field(..., description="Source URL")
    extract: str = Field(..., description="Verbatim snippet from the source")


class ValuedField(BaseModel):
    """A field with its value and supporting sources."""

    value: str = Field(..., description="The field value")
    sources: List[Source] = Field(..., min_length=1, description="Supporting sources")


class NumericValuedField(BaseModel):
    """A field with numeric or string value and supporting sources."""

    value: Union[str, int, float] = Field(..., description="The field value")
    sources: List[Source] = Field(..., min_length=1, description="Supporting sources")


class GrapeVariety(BaseModel):
    """A grape variety with percentage and sources."""

    name: str = Field(..., description="Grape variety name")
    percent: Optional[float] = Field(None, description="Percentage of blend")
    sources: List[Source] = Field(..., min_length=1, description="Supporting sources")


class SimpleGrapeVariety(BaseModel):
    """A grape variety without sources (for Jina)."""

    name: str = Field(..., description="Grape variety name")
    percent: Optional[float] = Field(None, description="Percentage of blend")


class SimpleWine(BaseModel):
    """Simplified wine data without sources (for Jina DeepSearch)."""

    normalized_name: str = Field(..., description="Wine name")
    producer: Optional[str] = Field(None, description="Producer/winery name")
    region: Optional[str] = Field(None, description="Wine region")
    appellation: Optional[str] = Field(None, description="Appellation/designation")
    vintage: Optional[Union[str, int, float]] = Field(None, description="Vintage year")
    grapes: Optional[List[SimpleGrapeVariety]] = Field(
        None, description="Grape varieties"
    )
    fermentation: Optional[str] = Field(None, description="Fermentation process")
    aging: Optional[str] = Field(None, description="Aging process")
    notes: Optional[str] = Field(None, description="Tasting notes")
    alcohol_by_volume: Optional[Union[str, int, float]] = Field(None, description="ABV")
    soil_type: Optional[str] = Field(None, description="Soil characteristics")


class SimpleWineExtraction(BaseModel):
    """Root model for simplified wine extraction (Jina)."""

    wine: SimpleWine = Field(..., description="Extracted wine data")


class Wine(BaseModel):
    """Complete wine data with per-field sources."""

    normalized_name: ValuedField = Field(..., description="Wine name")
    producer: ValuedField = Field(..., description="Producer/winery name")
    region: ValuedField = Field(..., description="Wine region")
    appellation: ValuedField = Field(..., description="Appellation/designation")
    vintage: NumericValuedField = Field(..., description="Vintage year")
    grapes: List[GrapeVariety] = Field(..., min_length=1, description="Grape varieties")
    fermentation: Optional[ValuedField] = Field(
        None, description="Fermentation process"
    )
    aging: Optional[ValuedField] = Field(None, description="Aging process")
    notes: Optional[ValuedField] = Field(None, description="Tasting notes")
    alcohol_by_volume: Optional[NumericValuedField] = Field(None, description="ABV")
    soil_type: Optional[ValuedField] = Field(None, description="Soil characteristics")


class WineExtraction(BaseModel):
    """Root model for wine extraction results."""

    wine: Wine = Field(..., description="Extracted wine data")


def wine_schema_for_jina() -> dict:
    """Generate simplified JSON schema for Jina DeepSearch API (no sources)."""
    return SimpleWineExtraction.model_json_schema()


def wine_schema_for_openai() -> dict:
    """Generate JSON schema for OpenAI structured outputs."""
    schema = WineExtraction.model_json_schema()

    # OpenAI requires all properties to be in required array for strict mode
    # But we'll only require core fields and make others optional
    def make_selective_required(obj, path=""):
        if isinstance(obj, dict):
            if "properties" in obj and "type" in obj and obj["type"] == "object":
                # Only require core wine fields, make others optional
                if path == "properties.wine":
                    obj["required"] = [
                        "normalized_name",
                        "producer",
                        "region",
                        "appellation",
                        "vintage",
                        "grapes",
                    ]
                else:
                    # For other objects, require all properties
                    if "properties" in obj:
                        obj["required"] = list(obj["properties"].keys())
                # Remove additionalProperties for OpenAI compatibility
                obj.pop("additionalProperties", None)
            # Recursively process nested objects
            for key, value in obj.items():
                if isinstance(value, dict):
                    make_selective_required(value, f"{path}.{key}" if path else key)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            make_selective_required(item, f"{path}.{key}[]")

    make_selective_required(schema)

    return {
        "name": "wine_extraction",
        "schema": schema,
        "strict": True,
    }
