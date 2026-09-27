import logging
import urllib.request
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import models

logger = logging.getLogger(__name__)

# Complete list of reputable, open, free financial and economic news feeds
FEEDS = [
    {
        "name": "Bloomberg HT",
        "category": "Turkey",
        "url": "https://www.bloomberght.com/rss",
        "source": "Bloomberg HT"
    },
    {
        "name": "Investing.com TR",
        "category": "Turkey",
        "url": "https://tr.investing.com/rss/news_25.rss",
        "source": "Investing.com"
    },
    {
        "name": "Investing.com Küresel",
        "category": "World",
        "url": "https://tr.investing.com/rss/news.rss",
        "source": "Investing.com"
    },
    {
        "name": "Euronews Türkçe",
        "category": "World",
        "url": "https://tr.euronews.com/rss?level=theme&name=business",
        "source": "Euronews"
    },
    {
        "name": "BBC Türkçe Ekonomi",
        "category": "World",
        "url": "https://feeds.bbci.co.uk/turkce/rss.xml",
        "source": "BBC Türkçe"
    },
    {
        "name": "AA Finans",
        "category": "Turkey",
        "url": "https://www.aa.com.tr/tr/rss/default?cat=ekonomi",
        "source": "AA Finans"
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
    },
    {
        "name": "Yahoo Finance",
        "category": "World",
        "url": "https://finance.yahoo.com/news/rssindex",
        "source": "Yahoo Finance"
    },
    {
        "name": "TRT Ekonomi",
        "category": "Turkey",
        "url": "https://www.trthaber.com/ekonomi_articles.rss",
        "source": "TRT Ekonomi"
    }
]

def clean_html(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.replace('&quot;', '"').replace('&amp;', '&').replace('&apos;', "'").replace('&nbsp;', ' ').replace('&#x27;', "'").strip()

def clean_paraanaliz_text(raw_text: str):
    categories = [
        "Şirket Haberleri", "Ekonomi", "Altın, Petrol ve Emtia", "Dünya Ekonomisi",
        "Politika", "Para Politikası", "Kripto", "Borsa", "Gündem", "Yazarlar",
        "Sektörler", "Bankacılık"
    ]
    detected_cat = "Piyasa"
    cleaned = raw_text.strip()
    
    for c in categories:
        if cleaned.startswith(c):
            detected_cat = c
            cleaned = cleaned[len(c):].strip()
            break
            
    # Remove trailing date if present
    cleaned = re.sub(r'\s*\d{1,2}\s+(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4}$', '', cleaned, flags=re.I).strip()
    return detected_cat, cleaned

def fetch_paraanaliz_news():
    """Fetch live news from Paraanaliz.com"""
    items = []
    try:
        url = "https://www.paraanaliz.com/"
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
        )
        with urllib.request.urlopen(req, timeout=12) as res:
            html = res.read().decode('utf-8', errors='ignore')
            
        pattern = r'<a[^>]+href="(/haberler/(?!kategori/)[^"]+)"[^>]*>(.*?)</a>'
        matches = re.findall(pattern, html, re.DOTALL)
        seen = set()
        
        for href, inner in matches:
            clean_text = re.sub(r'<[^>]+>', ' ', inner).strip()
            clean_text = re.sub(r'\s+', ' ', clean_text)
            clean_text = clean_html(clean_text)
            
            if len(clean_text) > 15 and href not in seen:
                seen.add(href)
                cat, title = clean_paraanaliz_text(clean_text)
                full_url = f"https://www.paraanaliz.com{href}"
                items.append({
                    "title": title,
                    "url": full_url,
                    "source": "Paraanaliz",
                    "category": cat,
                    "description": f"Paraanaliz {cat} analizi ve piyasa gelişmesi: {title}"
                })
    except Exception as e:
        logger.warning(f"Error fetching Paraanaliz: {e}")
    return items

def fetch_and_store_mock_news(db: Session):
    logger.info("Fetching real financial news from all feeds including Paraanaliz...")
    
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

    new_articles_count = 0

    # 1. Fetch RSS feeds (Bloomberg, Investing, Euronews, BBC, AA, Dünya, CNBC, Yahoo, TRT)
    for feed in FEEDS:
        try:
            req = urllib.request.Request(
                feed["url"],
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
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
                    desc = clean_html(desc_elem.text) if desc_elem is not None and desc_elem.text else f"{feed['source']} son dakika finans ve ekonomi haberi."
                    
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
                            is_breaking=(idx == 0) # mark top article as breaking for ticker
                        )
                        db.add(article)
                        new_articles_count += 1
                        
                db.commit()
                logger.info(f"[{feed['source']}] successfully imported.")
        except Exception as e:
            logger.warning(f"Error fetching feed {feed['name']}: {e}")
            db.rollback()

    # 2. Fetch Paraanaliz.com
    try:
        pa_items = fetch_paraanaliz_news()
        for idx, item in enumerate(pa_items[:20]):
            existing = db.query(models.Article).filter((models.Article.url == item["url"]) | (models.Article.title == item["title"])).first()
            if not existing:
                article = models.Article(
                    title=item["title"],
                    description=item["description"],
                    url=item["url"],
                    source="Paraanaliz",
                    published_at=datetime.now(timezone.utc),
                    category_id=cat_map["Turkey"],
                    is_breaking=(idx == 0)
                )
                db.add(article)
                new_articles_count += 1
        db.commit()
        logger.info("[Paraanaliz] successfully imported.")
    except Exception as e:
        logger.warning(f"Error saving Paraanaliz news: {e}")
        db.rollback()

    logger.info(f"All feeds update complete. Total new articles: {new_articles_count}")
