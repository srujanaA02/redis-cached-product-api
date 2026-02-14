from sqlalchemy import Column, String, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class Product(Base):
    """SQLAlchemy model for Product table."""
    
    __tablename__ = "products"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, nullable=False)
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "stock_quantity": self.stock_quantity
        }
