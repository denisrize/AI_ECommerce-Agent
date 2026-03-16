from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import (
    String, Integer, Boolean, DateTime,
    ForeignKey, Text, Numeric, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


# ── Base Class ────────────────────────────────────────────────
# Every model inherits from this. It tells SQLAlchemy "these 
# classes are database tables, not regular Python classes."
# Alembic also uses this to discover all your tables when
# generating migrations.

class Base(DeclarativeBase):
    pass


# ── Users ─────────────────────────────────────────────────────
# Represents a customer of the e-commerce platform.
#
# Design decisions:
# - String ID (UUID) instead of auto-increment integer. Why?
#   UUIDs are globally unique — safe for distributed systems and
#   don't reveal how many users you have (security benefit).
# - preferred_lang: The agent needs to know which language to 
#   respond in. Defaults to English, can be set to Hebrew ("he").
# - email is indexed + unique: We'll look up users by email often
#   (e.g., "find my orders"), so an index makes that fast.

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    preferred_lang: Mapped[str] = mapped_column(String(5), default="en")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships — these don't create columns, they define how
    # SQLAlchemy loads related objects. "cascade=all, delete-orphan"
    # means: if you delete a user, automatically delete their orders.
    orders: Mapped[List["Order"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


# ── Products ──────────────────────────────────────────────────
# A product in the store catalog.
#
# Design decisions:
# - SKU (Stock Keeping Unit): A standard e-commerce identifier.
#   Indexed and unique because agents/tools will search by SKU.
# - Bilingual fields (name_en/name_he, description_en/description_he):
#   The system has Hebrew and English support. Storing both
#   translations in the same row is the simplest approach. For a
#   production system with 20+ languages, you'd use a separate
#   translations table instead.
# - Numeric(10,2) for price: Never use float for money! Floats
#   have rounding errors (0.1 + 0.2 = 0.30000000000000004).
#   Decimal/Numeric is exact.
# - stock_quantity: The agent's check_product_availability tool
#   will read this to tell customers if items are in stock.
# - active: Soft-delete flag. Instead of deleting products (which
#   would break existing order references), we mark them inactive.

class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    name_he: Mapped[str] = mapped_column(String(255), nullable=False)
    description_en: Mapped[Optional[str]] = mapped_column(Text)
    description_he: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    order_items: Mapped[List["OrderItem"]] = relationship(back_populates="product")

    def __repr__(self) -> str:
        return f"<Product {self.sku}: {self.name_en}>"


# ── Orders ────────────────────────────────────────────────────
# A customer's purchase order.
#
# Design decisions:
# - order_number: Human-readable identifier (ORD-2024-XXXXX).
#   Customers will quote this in chat. The agent's get_order_status
#   tool searches by this field.
# - status with index: The agent will frequently filter by status
#   (e.g., "show me my pending orders"), so we index it.
# - Separate subtotal/discount/shipping/total: Breaking out the
#   price components lets the agent explain charges clearly:
#   "Your subtotal was ₪200, shipping was ₪15, total ₪215."
# - ForeignKey with CASCADE: If a user is deleted, their orders
#   go too. In production you'd probably soft-delete instead.

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Order {self.order_number}>"


# ── OrderItems ────────────────────────────────────────────────
# A single line item within an order.
#
# This is the JOIN TABLE between Orders and Products, but it's
# more than a simple many-to-many — it carries data of its own:
#
# - unit_price: The price AT TIME OF PURCHASE. If the product
#   price changes tomorrow, this order still reflects what the
#   customer paid. This is called "price snapshotting."
# - quantity: How many of this product were ordered.
# - subtotal: quantity × unit_price (pre-computed for convenience).
#
# The composite index on (order_id, product_id) speeds up the 
# most common query: "get all items for order X."

class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_id: Mapped[str] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")

    __table_args__ = (
        Index("idx_order_items_order_product", "order_id", "product_id"),
    )

    def __repr__(self) -> str:
        return f"<OrderItem order={self.order_id} product={self.product_id} qty={self.quantity}>"
