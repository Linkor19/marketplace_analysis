import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base

from data_gen import (
    cities_df, categories_df, users, user_profiles, listings,
    listing_promotions, view_bookings, deals, partner_discounts,
    clickstream_events, listing_moderation_logs
)

load_dotenv()

DBCON = os.getenv('DBCON') # Формат: password@localhost:5432
engine = create_engine(f"postgresql://postgres:{DBCON}/marketplace_db")

Base = declarative_base()

# --- СХЕМА БД ---

class Cities(Base):
    __tablename__ = 'cities'
    city_id = Column(Integer, primary_key=True)
    city_name = Column(String(50), nullable=False)
    country = Column(String(10), nullable=False)

class Categories(Base):
    __tablename__ = 'categories'
    category_id = Column(Integer, primary_key=True)
    category_name = Column(String(100), nullable=False)
    parent_id = Column(Integer, nullable=True)

class Users(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    registered_at = Column(DateTime, nullable=False)
    country = Column(String(10), nullable=False)
    city_id = Column(Integer, ForeignKey('cities.city_id'), nullable=False)
    email = Column(String(100))

class UserProfiles(Base):
    __tablename__ = 'user_profiles'
    profile_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    has_pet_profile = Column(Boolean, default=False)
    pet_type = Column(String(50))
    pet_name = Column(String(50))
    updated_at = Column(DateTime)

class Listings(Base):
    __tablename__ = 'listings'
    listing_id = Column(Integer, primary_key=True)
    seller_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.category_id'), nullable=False)
    city_id = Column(Integer, ForeignKey('cities.city_id'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(1000))
    price = Column(Numeric(10, 2))
    created_at = Column(DateTime, nullable=False)
    status = Column(String(20))
    view_count = Column(Integer, default=0)

class ListingPromotions(Base):
    __tablename__ = 'listing_promotions'
    promo_id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey('listings.listing_id'), nullable=False)
    promo_type = Column(String(50))
    amount_paid = Column(Numeric(10, 2))
    purchased_at = Column(DateTime)

class ViewBookings(Base):
    __tablename__ = 'view_bookings'
    booking_id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey('listings.listing_id'), nullable=False)
    buyer_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    booking_fee = Column(Numeric(10, 2))
    booked_at = Column(DateTime)
    status = Column(String(20))

class Deals(Base):
    __tablename__ = 'deals'
    deal_id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey('view_bookings.booking_id'), nullable=False)
    deal_amount = Column(Numeric(10, 2))
    closed_at = Column(DateTime)

class PartnerDiscounts(Base):
    __tablename__ = 'partner_discounts'
    discount_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    partner_name = Column(String(100))
    discount_code = Column(String(50))
    used_at = Column(DateTime)

class ClickstreamEvents(Base):
    __tablename__ = 'clickstream_events'
    event_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    event_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False)

class ListingModerationLogs(Base):
    __tablename__ = 'listing_moderation_logs'
    log_id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey('listings.listing_id'), nullable=False)
    flag_reason = Column(String(50))
    flagged_at = Column(DateTime)
    resolved = Column(Boolean, default=False)

print("⚙️ Создание таблиц и ключей PostgreSQL...")
Base.metadata.create_all(engine)

print("🚀 Пакетная загрузка данных...")
tables_map = [
    ("cities", cities_df),
    ("categories", categories_df),
    ("users", users),
    ("user_profiles", user_profiles),
    ("listings", listings),
    ("listing_promotions", listing_promotions),
    ("view_bookings", view_bookings),
    ("deals", deals),
    ("partner_discounts", partner_discounts),
    ("clickstream_events", clickstream_events),
    ("listing_moderation_logs", listing_moderation_logs)
]

for table_name, df in tables_map:
    df.to_sql(
        name=table_name,
        con=engine,
        if_exists='append',
        index=False,
        chunksize=5000,
        method='multi'
    )
    print(f"  └─ Таблица '{table_name}': успешно занесена.")

print("\n🎉 Все таблицы онлайн-маркетплейса успешно занесены в базу данных!")