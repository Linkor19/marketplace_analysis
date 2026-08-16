import pandas as pd
import numpy as np
import random
import datetime

random.seed(42)
np.random.seed(42)

print("⏳ Generating data for the Online Marketplace...")

# 1. Cities
cities_df = pd.DataFrame([
    {"city_id": 1, "city_name": "Kyiv", "country": "UA"},
    {"city_id": 2, "city_name": "Lviv", "country": "UA"},
    {"city_id": 3, "city_name": "Warsaw", "country": "PL"},
    {"city_id": 4, "city_name": "Krakow", "country": "PL"}
])

# 2. Categories
categories_df = pd.DataFrame([
    {"category_id": 1, "category_name": "Pet Supplies", "parent_id": None},
    {"category_id": 2, "category_name": "Pets & Animals", "parent_id": None},
    {"category_id": 3, "category_name": "Pet Services", "parent_id": None}
])

# 3. Users
NUM_USERS = 1500
start_date = datetime.datetime(2026, 1, 1)

users_list = []
for u_id in range(1, NUM_USERS + 1):
    country = "UA" if random.random() < 0.65 else "PL"
    city_id = random.choice([1, 2]) if country == "UA" else random.choice([3, 4])
    users_list.append({
        "user_id": u_id,
        "registered_at": start_date + datetime.timedelta(days=random.randint(0, 60), minutes=random.randint(0, 1440)),
        "country": country,
        "city_id": city_id,
        "email": f"user_{u_id}@example.com"
    })
users = pd.DataFrame(users_list)

# 4. User Profiles & Pet Profiles
user_profiles_list = []
for u in users_list:
    has_pet_profile = random.random() < 0.55
    user_profiles_list.append({
        "profile_id": u["user_id"],
        "user_id": u["user_id"],
        "has_pet_profile": has_pet_profile,
        "pet_type": random.choice(["Dog", "Cat", "Bird", "Other"]) if has_pet_profile else None,
        "pet_name": f"Pet_{u['user_id']}" if has_pet_profile else None,
        "updated_at": u["registered_at"] + datetime.timedelta(minutes=random.randint(5, 120))
    })
user_profiles = pd.DataFrame(user_profiles_list)

# 5. Listings
NUM_LISTINGS = 3000
listings_list = []
for l_id in range(1, NUM_LISTINGS + 1):
    seller_id = random.randint(1, NUM_USERS)
    seller_country = users.loc[users['user_id'] == seller_id, 'country'].values[0]
    seller_city = users.loc[users['user_id'] == seller_id, 'city_id'].values[0]
    created_at = start_date + datetime.timedelta(days=random.randint(0, 50), hours=random.randint(0, 23))

    # Generating duplicates for the scoring
    if l_id % 20 == 0:
        title = "Собака породы Лабрадор щенки"
        desc = "Продам щенка лабрадора с документами отличное здоровье"
    else:
        title = f"Товар или животное #{l_id}"
        desc = f"Описание объявления номер {l_id} с хорошими характеристиками."

    is_active = random.random() > 0.25  # 25% "dead" or inactive
    listings_list.append({
        "listing_id": l_id,
        "seller_id": seller_id,
        "category_id": random.choice([1, 2, 3]),
        "city_id": seller_city,
        "title": title,
        "description": desc,
        "price": round(random.uniform(10.0, 500.0), 2),
        "created_at": created_at,
        "status": "active" if is_active else "inactive",
        "view_count": random.randint(0, 150) if is_active else random.randint(0, 5)
    })
listings = pd.DataFrame(listings_list)

# 6. Listing Promotions
promotions_list = []
for l in listings_list[:400]:
    promotions_list.append({
        "promo_id": len(promotions_list) + 1,
        "listing_id": l["listing_id"],
        "promo_type": random.choice(["TOP_3_DAYS", "HIGHLIGHT", "VIP"]),
        "amount_paid": random.choice([5.00, 10.00, 25.00]),
        "purchased_at": l["created_at"] + datetime.timedelta(hours=2)
    })
listing_promotions = pd.DataFrame(promotions_list)

# 7. View Bookings (Views and bookings funnel)
bookings_list = []
b_id = 1
for l in listings_list:
    if l["status"] == "active" and random.random() < 0.30:  # 30% view and book
        buyer_id = random.randint(1, NUM_USERS)
        bookings_list.append({
            "booking_id": b_id,
            "listing_id": l["listing_id"],
            "buyer_id": buyer_id,
            "booking_fee": 2.50,
            "booked_at": l["created_at"] + datetime.timedelta(days=random.randint(1, 5)),
            "status": random.choice(["confirmed", "cancelled"])
        })
        b_id += 1
view_bookings = pd.DataFrame(bookings_list)

# 8. Deals
deals_list = []
d_id = 1
for b in bookings_list:
    if b["status"] == "confirmed" and random.random() < 0.65:  # 65% from booking to deal
        deals_list.append({
            "deal_id": d_id,
            "booking_id": b["booking_id"],
            "deal_amount": round(random.uniform(20.0, 400.0), 2),
            "closed_at": b["booked_at"] + datetime.timedelta(days=random.randint(1, 3))
        })
        d_id += 1
deals = pd.DataFrame(deals_list)

# 9. Partner Discounts
discounts_list = []
p_id = 1
for up in user_profiles_list:
    if up["has_pet_profile"]:
        # 40% of those who have a pet profile use the discount
        if random.random() < 0.40:
            discounts_list.append({
                "discount_id": p_id,
                "user_id": up["user_id"],
                "partner_name": random.choice(["PetShop_UA", "VetClinic_PL", "ZooKorm"]),
                "discount_code": "PET_LOVER_2026",
                "used_at": up["updated_at"] + datetime.timedelta(days=random.randint(1, 10))
            })
            p_id += 1
partner_discounts = pd.DataFrame(discounts_list)

# 10. Clickstream Events
events_list = []
ev_id = 1
for u in users_list:
    reg_t = u["registered_at"]
    # Registration events
    events_list.append(
        {"event_id": ev_id, "user_id": u["user_id"], "event_type": "user_registered", "timestamp": reg_t})
    ev_id += 1

    # Profile creation events
    up_row = user_profiles[user_profiles['user_id'] == u["user_id"]].iloc[0]
    if up_row["has_pet_profile"]:
        events_list.append({"event_id": ev_id, "user_id": u["user_id"], "event_type": "pet_profile_created",
                            "timestamp": up_row["updated_at"]})
        ev_id += 1

    # Discount events
    has_disc = partner_discounts[partner_discounts['user_id'] == u["user_id"]]
    if len(has_disc) > 0:
        events_list.append({"event_id": ev_id, "user_id": u["user_id"], "event_type": "partner_discount_used",
                            "timestamp": has_disc.iloc[0]["used_at"]})
        ev_id += 1

clickstream_events = pd.DataFrame(events_list)

# 11. Listing Moderation Logs
mod_logs_list = []
m_id = 1
for l in listings_list:
    if random.random() < 0.10:  # 10% of listings have complaints or moderation checks
        mod_logs_list.append({
            "log_id": m_id,
            "listing_id": l["listing_id"],
            "flag_reason": random.choice(["DUPLICATE", "IRRELEVANT", "FRAUD_SUSPECT", "WRONG_CATEGORY"]),
            "flagged_at": l["created_at"] + datetime.timedelta(hours=random.randint(1, 24)),
            "resolved": random.choice([True, False])
        })
        m_id += 1
listing_moderation_logs = pd.DataFrame(mod_logs_list)

print("✅ Marketplace data generation fully completed!")