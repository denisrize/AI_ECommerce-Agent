from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


# ══════════════════════════════════════════════════════════════
# User Schemas
# ══════════════════════════════════════════════════════════════
# Pattern: Base → Create (for input) → Response (for output)
#
# UserBase has the shared fields. UserCreate inherits it (adds
# nothing here, but could add password etc. in a real app).
# UserResponse adds server-generated fields like id and created_at.

class UserBase(BaseModel):
    email: EmailStr  # Pydantic validates email format automatically
    full_name: str
    phone: Optional[str] = None
    preferred_lang: str = Field(default="en", pattern="^(en|he)$")


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True  # Allows creating from SQLAlchemy model instances


# ══════════════════════════════════════════════════════════════
# Product Schemas
# ══════════════════════════════════════════════════════════════

class ProductBase(BaseModel):
    sku: str
    name_en: str
    name_he: str
    description_en: Optional[str] = None
    description_he: Optional[str] = None
    category: str
    price: Decimal = Field(ge=0)  # ge=0 means "greater or equal to 0"
    stock_quantity: int = Field(ge=0, default=0)


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: str
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ══════════════════════════════════════════════════════════════
# OrderItem Schemas
# ══════════════════════════════════════════════════════════════

class OrderItemBase(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)  # gt=0 means "must be at least 1"


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: str
    unit_price: Decimal
    subtotal: Decimal

    class Config:
        from_attributes = True


class OrderItemWithProduct(OrderItemResponse):
    """OrderItem with nested product info — used when the agent
    needs to tell a customer what's in their order."""
    product: ProductResponse


# ══════════════════════════════════════════════════════════════
# Order Schemas
# ══════════════════════════════════════════════════════════════
# Three levels of detail:
# - OrderResponse: Just the order metadata (for list views)
# - OrderWithItems: Includes line items (for order detail)
# - OrderDetail: Includes items WITH full product info (for agent)

class OrderBase(BaseModel):
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    user_id: str
    items: List[OrderItemCreate]


class OrderResponse(OrderBase):
    id: str
    order_number: str
    user_id: str
    status: str
    subtotal: Decimal
    discount_amount: Decimal
    shipping_cost: Decimal
    total_amount: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class OrderWithItems(OrderResponse):
    """Order with nested items — what the get_order_status tool returns."""
    items: List[OrderItemResponse]


class OrderDetail(OrderResponse):
    """Full detail with product info inside each item."""
    items: List[OrderItemWithProduct]


# ══════════════════════════════════════════════════════════════
# Chat Schemas
# ══════════════════════════════════════════════════════════════
# These define the HTTP interface for the chat endpoint.
# Unlike the schemas above, they don't map to database tables —
# they define the conversation protocol between client and agent.
#
# Kept here (not in chat.py) for consistency: all data contracts
# live in one place. The orchestrator, routes, and tests can all
# import from here.

class Message(BaseModel):
    """
    A single message in the conversation.

    The conversation is STATELESS on the server — the client sends
    the FULL history every time. This means:
      - No session storage needed on the backend
      - The client controls the context window
      - Easy to scale horizontally (any server can handle any request)
    """
    role: str   # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    stream: bool = True               # SSE streaming by default
    user_id: Optional[str] = None     # For future: personalized responses


class ChatResponse(BaseModel):
    """Used only for non-streaming responses (stream=false)."""
    response: str