import pytest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import time

from main import app
from database import get_db
from models import Base
from cache import cache

# Create test database
TEST_DATABASE_URL = "sqlite:///./test_products.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown():
    """Setup and teardown for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)
    # Clean up test database file
    if os.path.exists("test_products.db"):
        try:
            os.remove("test_products.db")
        except:
            pass


class TestProductAPI:
    """Test suite for Product API endpoints."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["api"] == "operational"
        assert "redis" in data
    
    def test_create_product_success(self):
        """Test successful product creation."""
        product_data = {
            "name": "Test Product",
            "description": "A test product description",
            "price": 49.99,
            "stock_quantity": 100
        }
        
        response = client.post("/products", json=product_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == product_data["name"]
        assert data["description"] == product_data["description"]
        assert data["price"] == product_data["price"]
        assert data["stock_quantity"] == product_data["stock_quantity"]
        assert "id" in data
        assert len(data["id"]) > 0
    
    def test_create_product_invalid_price(self):
        """Test product creation with invalid price."""
        product_data = {
            "name": "Test Product",
            "description": "A test product",
            "price": -10.99,  # Invalid negative price
            "stock_quantity": 100
        }
        
        response = client.post("/products", json=product_data)
        assert response.status_code == 400 or response.status_code == 422
    
    def test_create_product_missing_required_field(self):
        """Test product creation with missing required field."""
        product_data = {
            "name": "Test Product",
            # Missing description
            "price": 49.99,
            "stock_quantity": 100
        }
        
        response = client.post("/products", json=product_data)
        assert response.status_code == 400 or response.status_code == 422
    
    def test_get_product_success(self):
        """Test successful product retrieval."""
        # First create a product
        product_data = {
            "name": "Get Test Product",
            "description": "Product for GET testing",
            "price": 29.99,
            "stock_quantity": 50
        }
        
        create_response = client.post("/products", json=product_data)
        assert create_response.status_code == 201
        product_id = create_response.json()["id"]
        
        # Now retrieve it
        get_response = client.get(f"/products/{product_id}")
        assert get_response.status_code == 200
        
        data = get_response.json()
        assert data["id"] == product_id
        assert data["name"] == product_data["name"]
        assert data["price"] == product_data["price"]
    
    def test_get_product_not_found(self):
        """Test retrieving non-existent product."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/products/{fake_id}")
        assert response.status_code == 404
    
    def test_cache_hit_scenario(self):
        """Test that second GET request uses cache (cache hit)."""
        # Create a product
        product_data = {
            "name": "Cache Test Product",
            "description": "Product for cache testing",
            "price": 19.99,
            "stock_quantity": 75
        }
        
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Clear cache to ensure clean test
        cache.invalidate_product_cache(product_id)
        
        # First GET (cache miss - should hit database)
        response1 = client.get(f"/products/{product_id}")
        assert response1.status_code == 200
        
        # Second GET (cache hit - should use cache)
        response2 = client.get(f"/products/{product_id}")
        assert response2.status_code == 200
        
        # Both should return same data
        assert response1.json() == response2.json()
    
    def test_update_product_success(self):
        """Test successful product update."""
        # Create a product
        product_data = {
            "name": "Original Name",
            "description": "Original description",
            "price": 99.99,
            "stock_quantity": 10
        }
        
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Update the product
        update_data = {
            "price": 79.99,
            "stock_quantity": 5
        }
        
        update_response = client.put(f"/products/{product_id}", json=update_data)
        assert update_response.status_code == 200
        
        data = update_response.json()
        assert data["id"] == product_id
        assert data["price"] == update_data["price"]
        assert data["stock_quantity"] == update_data["stock_quantity"]
        # Name and description should remain unchanged
        assert data["name"] == product_data["name"]
        assert data["description"] == product_data["description"]
    
    def test_update_product_not_found(self):
        """Test updating non-existent product."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"price": 99.99}
        
        response = client.put(f"/products/{fake_id}", json=update_data)
        assert response.status_code == 404
    
    def test_cache_invalidation_on_update(self):
        """Test that cache is invalidated after product update."""
        # Create a product
        product_data = {
            "name": "Cache Invalidation Test",
            "description": "Test cache invalidation",
            "price": 50.00,
            "stock_quantity": 20
        }
        
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # GET to populate cache
        client.get(f"/products/{product_id}")
        
        # Update product (should invalidate cache)
        update_data = {"price": 60.00}
        client.put(f"/products/{product_id}", json=update_data)
        
        # GET again - should fetch from database with updated value
        get_response = client.get(f"/products/{product_id}")
        assert get_response.status_code == 200
        assert get_response.json()["price"] == 60.00
    
    def test_delete_product_success(self):
        """Test successful product deletion."""
        # Create a product
        product_data = {
            "name": "Delete Test Product",
            "description": "Product for deletion testing",
            "price": 15.99,
            "stock_quantity": 30
        }
        
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Delete the product
        delete_response = client.delete(f"/products/{product_id}")
        assert delete_response.status_code == 204
        
        # Verify product is deleted
        get_response = client.get(f"/products/{product_id}")
        assert get_response.status_code == 404
    
    def test_delete_product_not_found(self):
        """Test deleting non-existent product."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/products/{fake_id}")
        assert response.status_code == 404
    
    def test_cache_invalidation_on_delete(self):
        """Test that cache is invalidated after product deletion."""
        # Create a product
        product_data = {
            "name": "Delete Cache Test",
            "description": "Test cache on deletion",
            "price": 25.00,
            "stock_quantity": 15
        }
        
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # GET to populate cache
        client.get(f"/products/{product_id}")
        
        # Delete product (should invalidate cache)
        delete_response = client.delete(f"/products/{product_id}")
        assert delete_response.status_code == 204
        
        # GET again - should return 404 (not from cache)
        get_response = client.get(f"/products/{product_id}")
        assert get_response.status_code == 404
    
    def test_full_crud_workflow(self):
        """Test complete CRUD workflow."""
        # CREATE
        product_data = {
            "name": "CRUD Test Product",
            "description": "Full CRUD lifecycle test",
            "price": 100.00,
            "stock_quantity": 50
        }
        
        create_response = client.post("/products", json=product_data)
        assert create_response.status_code == 201
        product_id = create_response.json()["id"]
        
        # READ
        read_response = client.get(f"/products/{product_id}")
        assert read_response.status_code == 200
        assert read_response.json()["name"] == product_data["name"]
        
        # UPDATE
        update_data = {"price": 120.00, "stock_quantity": 40}
        update_response = client.put(f"/products/{product_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["price"] == 120.00
        
        # DELETE
        delete_response = client.delete(f"/products/{product_id}")
        assert delete_response.status_code == 204
        
        # VERIFY DELETION
        final_response = client.get(f"/products/{product_id}")
        assert final_response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
