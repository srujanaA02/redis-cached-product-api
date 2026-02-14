from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging
import uvicorn

from database import get_db, init_db
from schemas import ProductCreate, ProductUpdate, ProductResponse
from services import product_service
from cache import cache
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="High-Performance Product API",
    description="A production-ready Product API with Redis caching and cache invalidation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.on_event("startup")
async def startup_event():
    """Initialize database and seed data on application startup."""
    logger.info("Starting up application...")
    init_db()
    logger.info("Application startup complete")


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint to verify API and Redis status.
    
    Returns:
        JSON response with service health status
    """
    redis_healthy = cache.health_check()
    
    return {
        "status": "healthy",
        "api": "operational",
        "redis": "connected" if redis_healthy else "disconnected",
        "cache_fallback": "enabled"
    }


@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new product.
    
    - **name**: Product name (required, 1-255 characters)
    - **description**: Product description (required)
    - **price**: Product price (required, must be positive)
    - **stock_quantity**: Available stock (required, must be non-negative)
    
    Returns the created product with generated ID.
    """
    try:
        new_product = product_service.create_product(db, product)
        logger.info(f"API: Created product {new_product.id}")
        return ProductResponse.model_validate(new_product)
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating product"
        )


@app.get("/products/{product_id}", response_model=ProductResponse, status_code=status.HTTP_200_OK)
async def get_product(
    product_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a product by ID with cache-aside pattern.
    
    Cache-Aside Logic:
    1. Check Redis cache first (fast path)
    2. On cache miss, query database
    3. Cache the result from database for future requests
    
    - **product_id**: Unique product identifier (UUID)
    
    Returns the product details if found, 404 otherwise.
    """
    try:
        product = product_service.get_product_by_id(db, product_id)
        
        if not product:
            logger.info(f"API: Product not found {product_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id '{product_id}' not found"
            )
        
        logger.info(f"API: Retrieved product {product_id}")
        return ProductResponse.model_validate(product)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving product"
        )


@app.put("/products/{product_id}", response_model=ProductResponse, status_code=status.HTTP_200_OK)
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing product and invalidate its cache.
    
    Cache Invalidation Logic:
    1. Update database first
    2. On success, invalidate cache entry
    3. Next GET request will cache fresh data
    
    All fields are optional. Only provided fields will be updated.
    
    - **product_id**: Unique product identifier (UUID)
    - **name**: Product name (optional, 1-255 characters)
    - **description**: Product description (optional)
    - **price**: Product price (optional, must be positive)
    - **stock_quantity**: Available stock (optional, must be non-negative)
    
    Returns the updated product if found, 404 otherwise.
    """
    try:
        updated_product = product_service.update_product(db, product_id, product_update)
        
        if not updated_product:
            logger.info(f"API: Product not found for update {product_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id '{product_id}' not found"
            )
        
        logger.info(f"API: Updated product {product_id}")
        return ProductResponse.model_validate(updated_product)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating product"
        )


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a product and invalidate its cache.
    
    Cache Invalidation Logic:
    1. Delete from database first
    2. On success, invalidate cache entry
    
    - **product_id**: Unique product identifier (UUID)
    
    Returns 204 No Content if successful, 404 if product not found.
    """
    try:
        deleted = product_service.delete_product(db, product_id)
        
        if not deleted:
            logger.info(f"API: Product not found for deletion {product_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id '{product_id}' not found"
            )
        
        logger.info(f"API: Deleted product {product_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while deleting product"
        )


@app.exception_handler(422)
async def validation_exception_handler(request, exc):
    """Custom handler for validation errors."""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Invalid input data. Please check your request payload.",
            "errors": exc.errors() if hasattr(exc, 'errors') else str(exc)
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
