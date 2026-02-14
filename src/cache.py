import redis
import json
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache manager for product data."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis_client: Optional[redis.Redis] = None
        self.connect()
    
    def connect(self):
        """Establish connection to Redis server."""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Successfully connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def _get_cache_key(self, product_id: str) -> str:
        """Generate cache key for a product."""
        return f"product:{product_id}"
    
    def get_product_from_cache(self, product_id: str) -> Optional[dict]:
        """
        Retrieve product from Redis cache.
        
        Args:
            product_id: The unique identifier of the product
            
        Returns:
            Product dictionary if found in cache, None otherwise
        """
        if not self.redis_client:
            logger.warning("Redis client not available. Cache miss.")
            return None
        
        try:
            cache_key = self._get_cache_key(product_id)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                logger.info(f"Cache HIT for product_id: {product_id}")
                return json.loads(cached_data)
            else:
                logger.info(f"Cache MISS for product_id: {product_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving product from cache: {e}")
            return None
    
    def set_product_in_cache(self, product_dict: dict, ttl_seconds: Optional[int] = None):
        """
        Store product in Redis cache with TTL.
        
        Args:
            product_dict: Product data as dictionary (must include 'id' field)
            ttl_seconds: Time-to-live in seconds (defaults to settings.CACHE_TTL_SECONDS)
        """
        if not self.redis_client:
            logger.warning("Redis client not available. Skipping cache set.")
            return
        
        try:
            product_id = product_dict.get("id")
            if not product_id:
                logger.error("Product dictionary missing 'id' field. Cannot cache.")
                return
            
            cache_key = self._get_cache_key(product_id)
            ttl = ttl_seconds if ttl_seconds is not None else settings.CACHE_TTL_SECONDS
            
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(product_dict)
            )
            logger.info(f"Cached product_id: {product_id} with TTL: {ttl} seconds")
            
        except Exception as e:
            logger.error(f"Error setting product in cache: {e}")
    
    def invalidate_product_cache(self, product_id: str):
        """
        Invalidate (delete) product from Redis cache.
        
        Args:
            product_id: The unique identifier of the product to invalidate
        """
        if not self.redis_client:
            logger.warning("Redis client not available. Skipping cache invalidation.")
            return
        
        try:
            cache_key = self._get_cache_key(product_id)
            deleted_count = self.redis_client.delete(cache_key)
            
            if deleted_count > 0:
                logger.info(f"Invalidated cache for product_id: {product_id}")
            else:
                logger.info(f"No cache entry found to invalidate for product_id: {product_id}")
                
        except Exception as e:
            logger.error(f"Error invalidating product cache: {e}")
    
    def health_check(self) -> bool:
        """
        Check if Redis connection is healthy.
        
        Returns:
            True if Redis is accessible, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False


# Create a global cache instance
cache = RedisCache()
