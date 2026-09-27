from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import get_db
from security import get_api_key

router = APIRouter(dependencies=[Depends(get_api_key)])

@router.get("/categories", response_model=List[schemas.CategoryOut])
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()

@router.get("/news", response_model=List[schemas.ArticleOut])
def get_news(category: str = None, db: Session = Depends(get_db)):
    query = db.query(models.Article).order_by(models.Article.published_at.desc())
    if category:
        cat = db.query(models.Category).filter(models.Category.name == category).first()
        if cat:
            query = query.filter(models.Article.category_id == cat.id)
    return query.limit(50).all()

@router.get("/ticker", response_model=List[schemas.ArticleOut])
def get_ticker_news(db: Session = Depends(get_db)):
    return db.query(models.Article).filter(models.Article.is_breaking == True).order_by(models.Article.published_at.desc()).limit(10).all()

@router.post("/device-token")
def register_token(token_data: schemas.DeviceTokenCreate, db: Session = Depends(get_db)):
    existing = db.query(models.DeviceToken).filter(models.DeviceToken.token == token_data.token).first()
    if not existing:
        db_token = models.DeviceToken(token=token_data.token)
        db.add(db_token)
        db.commit()
    return {"status": "ok"}
