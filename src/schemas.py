from pydantic import BaseModel, Field
from typing import Optional


class ProductCreate(BaseModel):
    """Schema for creating a new product."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: str = Field(..., min_length=1, description="Product description")
    price: float = Field(..., gt=0, description="Product price (must be positive)")
    stock_quantity: int = Field(..., ge=0, description="Stock quantity (must be non-negative)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Example Product",
                "description": "A detailed description of the product.",
                "price": 29.99,
                "stock_quantity": 100
            }
        }


class ProductUpdate(BaseModel):
    """Schema for updating an existing product. All fields are optional."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, min_length=1, description="Product description")
    price: Optional[float] = Field(None, gt=0, description="Product price (must be positive)")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Stock quantity (must be non-negative)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "price": 34.99,
                "stock_quantity": 95
            }
        }


class ProductResponse(BaseModel):
    """Schema for product response."""
    
    id: str
    name: str
    description: str
    price: float
    stock_quantity: int
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Example Product",
                "description": "A detailed description of the product.",
                "price": 29.99,
                "stock_quantity": 100
            }
        }
