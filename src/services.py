from sqlalchemy.orm import Session
from models import Product
from schemas import ProductCreate, ProductUpdate
from cache import cache
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ProductService:
    """Service layer for product operations with caching logic."""
    
    @staticmethod
    def create_product(db: Session, product_data: ProductCreate) -> Product:
        """
        Create a new product in the database.
        Cache invalidation is not needed here as it's a new product.
        
        Args:
            db: Database session
            product_data: Product creation data
            
        Returns:
            Created Product model instance
        """
        product = Product(
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            stock_quantity=product_data.stock_quantity
        )
        
        db.add(product)
        db.commit()
        db.refresh(product)
        
        logger.info(f"Created new product with id: {product.id}")
        return product
    
    @staticmethod
    def get_product_by_id(db: Session, product_id: str) -> Optional[Product]:
        """
        Get product by ID with cache-aside pattern.
        
        Cache-Aside Logic:
        1. Check Redis cache first (cache hit returns immediately)
        2. On cache miss, query database
        3. If found in database, store in cache with TTL
        4. Return product or None
        
        Args:
            db: Database session
            product_id: Product unique identifier
            
        Returns:
            Product model instance if found, None otherwise
        """
        # Step 1: Try to get from cache
        cached_product = cache.get_product_from_cache(product_id)
        if cached_product:
            # Cache hit - return cached data as Product-like dict
            # We need to convert to Product instance for consistency
            product = Product(**cached_product)
            product.id = cached_product["id"]  # Ensure ID is set
            return product
        
        # Step 2: Cache miss - query database
        product = db.query(Product).filter(Product.id == product_id).first()
        
        # Step 3: If found in database, cache it
        if product:
            cache.set_product_in_cache(product.to_dict())
            logger.info(f"Retrieved product from database and cached: {product_id}")
        else:
            logger.info(f"Product not found in database: {product_id}")
        
        return product
    
    @staticmethod
    def update_product(db: Session, product_id: str, product_data: ProductUpdate) -> Optional[Product]:
        """
        Update product and invalidate cache.
        
        Write Operation Logic:
        1. Update database first
        2. On success, invalidate cache entry
        3. Next read will cache fresh data from database
        
        Args:
            db: Database session
            product_id: Product unique identifier
            product_data: Update data (partial or full)
            
        Returns:
            Updated Product model instance if found, None otherwise
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            logger.info(f"Product not found for update: {product_id}")
            return None
        
        # Update only provided fields
        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        db.commit()
        db.refresh(product)
        
        # Invalidate cache after successful database update
        cache.invalidate_product_cache(product_id)
        
        logger.info(f"Updated product and invalidated cache: {product_id}")
        return product
    
    @staticmethod
    def delete_product(db: Session, product_id: str) -> bool:
        """
        Delete product and invalidate cache.
        
        Write Operation Logic:
        1. Delete from database first
        2. On success, invalidate cache entry
        
        Args:
            db: Database session
            product_id: Product unique identifier
            
        Returns:
            True if product was deleted, False if not found
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            logger.info(f"Product not found for deletion: {product_id}")
            return False
        
        db.delete(product)
        db.commit()
        
        # Invalidate cache after successful database deletion
        cache.invalidate_product_cache(product_id)
        
        logger.info(f"Deleted product and invalidated cache: {product_id}")
        return True


# Create a global service instance
product_service = ProductService()
