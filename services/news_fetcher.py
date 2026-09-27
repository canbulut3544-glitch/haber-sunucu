import logging
import urllib.request
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import models

logger = logging.getLogger(__name__)

FEEDS = [
    {
        "name": "Bloomberg HT",
        "category": "Turkey",
        "url": "https://www.bloomberght.com/rss",
        "source": "Bloomberg HT"
    },
    {
        "name": "Dünya Gazetesi",
        "category": "Turkey",
        "url": "https://www.dunya.com/rss",
        "source": "Dünya Gazetesi"
    },
    {
        "name": "CNBC Küresel",
        "category": "World",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
        "source": "CNBC"
    }
]

def clean_html(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.replace('&quot;', '"').replace('&amp;', '&').replace('&apos;', "'").replace('&nbsp;', ' ').strip()

def fetch_and_store_mock_news(db: Session):
    logger.info("Fetching real financial news from RSS feeds...")
    
    # Clean up old test mock articles with example.com
    try:
        deleted_count = db.query(models.Article).filter(models.Article.url.like("%example.com%")).delete(synchronize_session=False)
        db.commit()
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old test articles.")
    except Exception as e:
        logger.warning(f"Error cleaning old articles: {e}")
        db.rollback()

    # Ensure categories exist
    categories = ["Turkey", "World", "USA", "Europe", "China", "Logistics", "Technology"]
    cat_map = {}
    for c in categories:
        db_cat = db.query(models.Category).filter(models.Category.name == c).first()
        if not db_cat:
            db_cat = models.Category(name=c, display_name=c)
            db.add(db_cat)
            db.commit()
            db.refresh(db_cat)
        cat_map[c] = db_cat.id

    # Fetch live RSS items
    new_articles_count = 0
    for feed in FEEDS:
        try:
            req = urllib.request.Request(feed["url"], headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=12) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                items = root.findall('.//item')
                
                for idx, item in enumerate(items[:15]): # top 15 from each source
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    desc_elem = item.find('description')
                    
                    if title_elem is None or not title_elem.text or link_elem is None or not link_elem.text:
                        continue
                        
                    title = clean_html(title_elem.text)
                    link = link_elem.text.strip()
                    desc = clean_html(desc_elem.text) if desc_elem is not None and desc_elem.text else f"{feed['source']} son dakika finans ve piyasa gelişmesi."
                    
                    # Avoid duplicates
                    existing = db.query(models.Article).filter((models.Article.url == link) | (models.Article.title == title)).first()
                    if not existing:
                        article = models.Article(
                            title=title,
                            description=desc,
                            url=link,
                            source=feed["source"],
                            published_at=datetime.now(timezone.utc),
                            category_id=cat_map.get(feed["category"], cat_map["Turkey"]),
                            is_breaking=(idx == 0) # mark the latest as breaking for ticker
                        )
                        db.add(article)
                        new_articles_count += 1
                        
                db.commit()
        except Exception as e:
            logger.error(f"Error fetching feed {feed['name']}: {e}")
            db.rollback()

    logger.info(f"Live news update complete. Added {new_articles_count} new articles.")
