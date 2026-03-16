"""
Database seed script.

Run from the backend/ directory:
    python -m scripts.seed_data

Creates:
  - 10 users (mix of Hebrew and English speakers)
  - 10 products (3 categories, 2 deliberately out of stock)
  - 25 orders with random items

The data is designed to support realistic agent conversations:
  - "Do you have headphones in stock?" → Yes (45 in stock)
  - "Is the Smart Watch available?" → No (0 stock — out of stock!)
  - "What are my orders?" (david.cohen@email.com) → Returns orders
  - "מה המחיר של מכונת קפה?" → Agent responds in Hebrew with price
"""
import asyncio
import uuid
import random
import sys
from pathlib import Path
from decimal import Decimal

# Add parent to path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.connection import AsyncSessionLocal
from app.models.database import User, Product, Order, OrderItem
from sqlalchemy import select


# ── Users ─────────────────────────────────────────────────────
# 5 Hebrew-preferring + 5 English-preferring users.
# Mix of Israeli and international names for realistic testing.
USERS = [
    {"email": "david.cohen@email.com", "full_name": "David Cohen",
     "phone": "+972-50-111-1111", "preferred_lang": "he"},
    {"email": "sarah.levi@email.com", "full_name": "Sarah Levi",
     "phone": "+972-52-222-2222", "preferred_lang": "he"},
    {"email": "john.smith@email.com", "full_name": "John Smith",
     "phone": "+972-54-333-3333", "preferred_lang": "en"},
    {"email": "emma.wilson@email.com", "full_name": "Emma Wilson",
     "phone": "+972-50-444-4444", "preferred_lang": "en"},
    {"email": "michael.brown@email.com", "full_name": "Michael Brown",
     "phone": "+972-52-555-5555", "preferred_lang": "en"},
    {"email": "yael.mizrachi@email.com", "full_name": "Yael Mizrachi",
     "phone": "+972-54-666-6666", "preferred_lang": "he"},
    {"email": "daniel.gold@email.com", "full_name": "Daniel Gold",
     "phone": "+972-50-777-7777", "preferred_lang": "en"},
    {"email": "maya.berkowitz@email.com", "full_name": "Maya Berkowitz",
     "phone": "+972-52-888-8888", "preferred_lang": "he"},
    {"email": "alex.johnson@email.com", "full_name": "Alex Johnson",
     "phone": "+972-54-999-9999", "preferred_lang": "en"},
    {"email": "noa.shapira@email.com", "full_name": "Noa Shapira",
     "phone": "+972-50-000-0000", "preferred_lang": "he"},
]

# ── Products ──────────────────────────────────────────────────
# 3 categories: Electronics (5), Home & Kitchen (4), Accessories (1)
# Note: Smart Watch Elite and Air Fryer XL have stock=0 (out of stock)
# to test the agent's "not available" responses.
PRODUCTS = [
    {
        "sku": "ELEC-HP-001", "category": "Electronics",
        "name_en": "Wireless Headphones Pro",
        "name_he": "אוזניות אלחוטיות פרו",
        "description_en": "Premium wireless headphones with active noise cancellation, 30-hour battery life",
        "description_he": "אוזניות אלחוטיות פרימיום עם ביטול רעשים אקטיבי, סוללה ל-30 שעות",
        "price": Decimal("299.99"), "stock_quantity": 45,
    },
    {
        "sku": "ELEC-SW-001", "category": "Electronics",
        "name_en": "Smart Watch Elite",
        "name_he": "שעון חכם אליט",
        "description_en": "Advanced smartwatch with health monitoring, GPS, and 5-day battery",
        "description_he": "שעון חכם מתקדם עם ניטור בריאות, GPS וסוללה ל-5 ימים",
        "price": Decimal("449.99"), "stock_quantity": 0,  # OUT OF STOCK
    },
    {
        "sku": "ELEC-BS-001", "category": "Electronics",
        "name_en": "Bluetooth Speaker",
        "name_he": "רמקול בלוטות'",
        "description_en": "Portable waterproof Bluetooth speaker with 360° sound",
        "description_he": "רמקול בלוטות' נייד עמיד במים עם צליל 360°",
        "price": Decimal("149.99"), "stock_quantity": 60,
    },
    {
        "sku": "ELEC-CH-001", "category": "Electronics",
        "name_en": "Wireless Charger",
        "name_he": "מטען אלחוטי",
        "description_en": "Fast wireless charging pad compatible with all Qi-enabled devices",
        "description_he": "משטח טעינה אלחוטית מהירה תואם לכל מכשירי Qi",
        "price": Decimal("49.99"), "stock_quantity": 100,
    },
    {
        "sku": "ELEC-HB-001", "category": "Electronics",
        "name_en": "USB-C Hub",
        "name_he": "מפצל USB-C",
        "description_en": "7-in-1 USB-C hub with HDMI, SD card, USB 3.0 ports",
        "description_he": "מפצל USB-C עם 7 חיבורים כולל HDMI, כרטיס SD ו-USB 3.0",
        "price": Decimal("79.99"), "stock_quantity": 55,
    },
    {
        "sku": "HOME-CF-001", "category": "Home & Kitchen",
        "name_en": "Coffee Maker Pro",
        "name_he": "מכונת קפה פרו",
        "description_en": "Programmable 12-cup coffee maker with built-in grinder",
        "description_he": "מכונת קפה 12 כוסות עם מטחנה מובנית",
        "price": Decimal("199.99"), "stock_quantity": 25,
    },
    {
        "sku": "HOME-AF-001", "category": "Home & Kitchen",
        "name_en": "Air Fryer XL",
        "name_he": "סיר טיגון באוויר XL",
        "description_en": "Extra large 5.8QT air fryer with digital touchscreen",
        "description_he": "סיר טיגון באוויר גדול 5.8 ליטר עם מסך מגע",
        "price": Decimal("129.99"), "stock_quantity": 0,  # OUT OF STOCK
    },
    {
        "sku": "HOME-KS-001", "category": "Home & Kitchen",
        "name_en": "Kitchen Scale",
        "name_he": "משקל מטבח",
        "description_en": "Precision digital kitchen scale, measures grams and ounces",
        "description_he": "משקל מטבח דיגיטלי מדויק, מודד גרמים ואונקיות",
        "price": Decimal("34.99"), "stock_quantity": 80,
    },
    {
        "sku": "HOME-BL-001", "category": "Home & Kitchen",
        "name_en": "Power Blender",
        "name_he": "בלנדר חזק",
        "description_en": "1200W high-power blender with 6 stainless steel blades",
        "description_he": "בלנדר 1200 וואט עם 6 להבי נירוסטה",
        "price": Decimal("89.99"), "stock_quantity": 40,
    },
    {
        "sku": "ACC-PC-001", "category": "Accessories",
        "name_en": "Phone Case Premium",
        "name_he": "כיסוי פרימיום לטלפון",
        "description_en": "Shockproof premium phone case with MagSafe compatibility",
        "description_he": "כיסוי פרימיום עמיד לזעזועים עם תאימות MagSafe",
        "price": Decimal("29.99"), "stock_quantity": 150,
    },
]

ORDER_STATUSES = ["pending", "confirmed", "processing", "shipped", "delivered"]


async def seed_database():
    async with AsyncSessionLocal() as db:
        # Guard: Don't double-seed
        result = await db.execute(select(User).limit(1))
        if result.scalar_one_or_none():
            print("⚠️  Database already seeded. Skipping.")
            print("   To re-seed: drop the tables and run migrations again.")
            return

        print("🌱 Seeding database...\n")

        # ── Create users ──
        users = []
        for user_data in USERS:
            user = User(id=str(uuid.uuid4()), **user_data)
            db.add(user)
            users.append(user)
        print(f"   👤 Created {len(users)} users")

        # ── Create products ──
        products = []
        for product_data in PRODUCTS:
            product = Product(id=str(uuid.uuid4()), **product_data)
            db.add(product)
            products.append(product)
        print(f"   📦 Created {len(products)} products")

        # Flush to get IDs assigned (but don't commit yet —
        # we want everything in one transaction)
        await db.flush()

        # ── Create orders ──
        # Only use products that are in stock for orders
        in_stock_products = [p for p in products if p.stock_quantity > 0]
        orders_created = 0

        for i in range(25):
            user = random.choice(users)
            num_items = random.randint(1, 3)
            order_products = random.sample(
                in_stock_products, min(num_items, len(in_stock_products))
            )

            subtotal = Decimal("0")
            items = []

            for product in order_products:
                qty = random.randint(1, 2)
                item_subtotal = product.price * qty
                subtotal += item_subtotal

                items.append(OrderItem(
                    id=str(uuid.uuid4()),
                    product_id=product.id,
                    quantity=qty,
                    unit_price=product.price,
                    subtotal=item_subtotal,
                ))

            shipping = Decimal("15.00")
            order = Order(
                id=str(uuid.uuid4()),
                order_number=f"ORD-2024-{str(i + 1).zfill(5)}",
                user_id=user.id,
                status=random.choice(ORDER_STATUSES),
                subtotal=subtotal,
                discount_amount=Decimal("0"),
                shipping_cost=shipping,
                total_amount=subtotal + shipping,
            )
            db.add(order)

            for item in items:
                item.order_id = order.id
                db.add(item)

            orders_created += 1

        # ── Commit everything in one transaction ──
        await db.commit()

        print(f"   🛒 Created {orders_created} orders with items")
        print(f"\n✅ Database seeded successfully!")
        print(f"\n📋 Quick reference:")
        print(f"   Test user (Hebrew):  david.cohen@email.com")
        print(f"   Test user (English): john.smith@email.com")
        print(f"   Out-of-stock items:  Smart Watch Elite, Air Fryer XL")
        print(f"   Sample order:        ORD-2024-00001")


if __name__ == "__main__":
    asyncio.run(seed_database())
