from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime, JSON, UniqueConstraint
from sqlalchemy.sql import func
from database import Base

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    description = Column(Text)
    image_url = Column(String)
    sizes = Column(JSON)  # {"S": 5, "M": 3, "L": 0}
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProductView(Base):
    __tablename__ = "product_views"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False)
    product_id = Column(Integer, nullable=False)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='unique_user_product_view'),
    )
