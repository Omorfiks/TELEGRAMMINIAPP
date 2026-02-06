from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Product, ProductView
from schemas import ProductCreate, ProductResponse, ProductViewCreate
import os
import uuid
from dotenv import load_dotenv
from pathlib import Path
import shutil

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="bro shop API")

# CORS для мини-приложения
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статические файлы для изображений
# Путь к media относительно корня проекта
project_root = Path(__file__).parent.parent
media_dir = project_root / "media"
media_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(media_dir)), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/products")
def get_products(db: Session = Depends(get_db)):
    """Получить список всех товаров"""
    products = db.query(Product).all()
    return [ProductResponse.model_validate(p) for p in products]

@app.get("/api/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Получить товар по ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse.model_validate(product)

@app.post("/api/views")
def create_view(view: ProductViewCreate, db: Session = Depends(get_db)):
    """Создать просмотр товара (уникальный для user_id + product_id)"""
    # Проверяем, существует ли уже такой просмотр
    existing = db.query(ProductView).filter(
        ProductView.user_id == view.user_id,
        ProductView.product_id == view.product_id
    ).first()
    
    if existing:
        return {"message": "View already exists", "id": existing.id}
    
    db_view = ProductView(**view.model_dump())
    db.add(db_view)
    db.commit()
    db.refresh(db_view)
    return {"message": "View created", "id": db_view.id}

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """Статистика для админки"""
    from sqlalchemy import func
    
    total_products = db.query(Product).count()
    
    # ТОП-5 просматриваемых товаров
    top_products = db.query(
        ProductView.product_id,
        func.count(ProductView.user_id.distinct()).label('unique_views')
    ).group_by(ProductView.product_id).order_by(
        func.count(ProductView.user_id.distinct()).desc()
    ).limit(5).all()
    
    top_products_data = []
    for product_id, views in top_products:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            top_products_data.append({
                "id": product.id,
                "name": product.name,
                "views": views
            })
    
    # Последние 3 товара
    recent_products = db.query(Product).order_by(Product.id.desc()).limit(3).all()
    
    return {
        "total_products": total_products,
        "top_products": top_products_data,
        "recent_products": [ProductResponse.model_validate(p) for p in recent_products]
    }

@app.post("/api/admin/upload")
async def upload_file(file: UploadFile = File(...)):
    """Загрузить файл (фото товара)"""
    # Генерируем уникальное имя файла
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = media_dir / unique_filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Возвращаем URL для доступа к файлу
    return {"url": f"/static/{unique_filename}"}

@app.post("/api/admin/products")
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Создать товар (для админки)"""
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return ProductResponse.model_validate(db_product)

@app.put("/api/admin/products/{product_id}")
def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    """Обновить товар (для админки)"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for key, value in product.model_dump().items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return ProductResponse.model_validate(db_product)

@app.get("/api/admin/products")
def list_products(db: Session = Depends(get_db)):
    """Список всех товаров для админки"""
    products = db.query(Product).order_by(Product.id.desc()).limit(20).all()
    return [ProductResponse.model_validate(p) for p in products]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
