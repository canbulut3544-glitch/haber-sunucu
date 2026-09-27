import logging
import random
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
import models

logger = logging.getLogger(__name__)

# This is a mock service. In reality, it would call NewsAPI or AlphaVantage.
# Using mock data to prevent hardcoding 3rd party keys and for testing purposes.

MOCK_TITLES = [
    ("TCMB faiz kararını açıkladı, piyasalarda hareketlilik bekleniyor", "Turkey"),
    ("FED faizleri sabit bıraktı, Powell'dan şahin açıklamalar", "USA"),
    ("ECB enflasyon endişeleriyle faiz indirimini öteledi", "Europe"),
    ("BİST 100 güne rekor seviyeden başladı", "Turkey"),
    ("S&P 500 teknoloji hisseleri öncülüğünde yükselişte", "USA"),
    ("Çin imalat verileri beklentilerin altında kaldı, emtia talebi düştü", "China"),
    ("Avrupa'da enerji krizi korkusu yeniden alevlendi", "Europe"),
    ("Kızıldeniz'de artan gerilim tedarik zincirini tehdit ediyor", "Logistics"),
    ("Yarı iletken sektöründe dev yatırım planı açıklandı", "Technology")
]

def fetch_and_store_mock_news(db: Session):
    logger.info("Fetching mock news...")
    
    # Ensure categories exist
    categories = ["Turkey", "World", "USA", "Europe", "China", "Russia", "Wars & Geopolitical Risks", "Logistics", "Technology"]
    cat_map = {}
    for c in categories:
        db_cat = db.query(models.Category).filter(models.Category.name == c).first()
        if not db_cat:
            db_cat = models.Category(name=c, display_name=c)
            db.add(db_cat)
            db.commit()
            db.refresh(db_cat)
        cat_map[c] = db_cat.id
        
    # Generate some mock articles
    for title, cat_name in MOCK_TITLES:
        existing = db.query(models.Article).filter(models.Article.title == title).first()
        if not existing:
            article = models.Article(
                title=title,
                description=f"Detailed analysis and reporting on: {title}",
                url=f"https://example.com/news/{random.randint(1000, 9999)}",
                source="MockNews API",
                published_at=datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 120)),
                category_id=cat_map.get(cat_name),
                is_breaking=random.choice([True, False, False, False])
            )
            db.add(article)
            db.commit()
            db.refresh(article)
            
            # Send Push Notification via FCM for Breaking News
            if article.is_breaking:
                send_fcm_notification(db, title=f"🚨 BREAKING: {article.title}", body=article.description)

    logger.info("Mock news updated in DB.")

def send_fcm_notification(db: Session, title: str, body: str):
    logger.info(f"FCM Simulated Push: {title}")
    # In a real environment, you would use:
    # import firebase_admin
    # from firebase_admin import messaging
    #
    # tokens = [t.token for t in db.query(models.DeviceToken).filter(models.DeviceToken.is_active == True).all()]
    # if tokens:
    #     message = messaging.MulticastMessage(
    #         notification=messaging.Notification(title=title, body=body),
    #         tokens=tokens,
    #     )
    #     response = messaging.send_multicast(message)
    #     logger.info(f"FCM Push Response: {response.success_count} messages were sent successfully")

