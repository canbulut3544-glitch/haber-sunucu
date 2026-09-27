from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CategoryBase(BaseModel):
    name: str
    display_name: str

class CategoryOut(CategoryBase):
    id: int
    class Config:
        from_attributes = True

class ArticleBase(BaseModel):
    title: str
    description: Optional[str] = None
    url: str
    source: str
    published_at: datetime
    is_breaking: bool

class ArticleOut(ArticleBase):
    id: int
    category_id: int
    class Config:
        from_attributes = True

class DeviceTokenCreate(BaseModel):
    token: str
