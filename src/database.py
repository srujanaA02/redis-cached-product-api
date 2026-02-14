from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, Product
from config import settings
import logging

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database and create tables."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
    
    # Seed initial data if database is empty
    seed_database()


def seed_database():
    """Seed the database with initial sample products if empty."""
    db = SessionLocal()
    try:
        # Check if database already has products
        existing_count = db.query(Product).count()
        if existing_count > 0:
            logger.info(f"Database already has {existing_count} products. Skipping seeding.")
            return
        
        # Sample products to seed
        sample_products = [
            Product(
                name="Wireless Mouse",
                description="Ergonomic wireless mouse with adjustable DPI settings",
                price=24.99,
                stock_quantity=150
            ),
            Product(
                name="Mechanical Keyboard",
                description="RGB mechanical keyboard with blue switches",
                price=89.99,
                stock_quantity=75
            ),
            Product(
                name="USB-C Hub",
                description="7-in-1 USB-C hub with HDMI, USB 3.0, and SD card reader",
                price=39.99,
                stock_quantity=200
            ),
            Product(
                name="Laptop Stand",
                description="Aluminum laptop stand with adjustable height",
                price=34.99,
                stock_quantity=100
            ),
            Product(
                name="Webcam HD",
                description="1080p HD webcam with built-in microphone",
                price=59.99,
                stock_quantity=50
            )
        ]
        
        db.add_all(sample_products)
        db.commit()
        logger.info(f"Successfully seeded database with {len(sample_products)} sample products")
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


def get_db() -> Session:
    """Dependency function to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
