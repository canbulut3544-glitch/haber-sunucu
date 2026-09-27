from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from database import Base

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # e.g., Turkey, USA, Europe, Technology
    display_name = Column(String)

class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    url = Column(String, unique=True, index=True)
    source = Column(String) # e.g., Bloomberg, Reuters
    published_at = Column(DateTime(timezone=True), default=func.now())
    category_id = Column(Integer, ForeignKey("categories.id"))
    is_breaking = Column(Boolean, default=False)
    
class DeviceToken(Base):
    __tablename__ = "device_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
