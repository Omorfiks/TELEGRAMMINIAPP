from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    price: int
    description: Optional[str] = None
    image_url: Optional[str] = None
    sizes: Optional[Dict[str, int]] = {}

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductViewCreate(BaseModel):
    user_id: int
    product_id: int
