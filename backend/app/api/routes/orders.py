from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from decimal import Decimal
import uuid
from datetime import datetime

from app.models.connection import get_db
from app.models.database import Order, OrderItem, User, Product
from app.models.schemas import OrderCreate, OrderResponse, OrderWithItems

router = APIRouter(prefix="/orders", tags=["orders"])


def generate_order_number() -> str:
    """
    Generate a human-readable order number.
    
    Format: ORD-2024-A1B2C (year + 5 random hex chars).
    Customers will quote these in chat, so they need to be
    short enough to read aloud and unique enough to not collide.
    """
    return f"ORD-{datetime.now().strftime('%Y')}-{uuid.uuid4().hex[:5].upper()}"


@router.get("/", response_model=List[OrderResponse])
async def list_orders(
    user_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    List orders with optional filters.
    
    The agent's get_order_status tool will call similar logic
    when a customer asks "what are my orders?" with their email.
    """
    query = select(Order)

    if user_id:
        query = query.where(Order.user_id == user_id)

    if status_filter:
        query = query.where(Order.status == status_filter)

    query = query.order_by(Order.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderWithItems)
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get a specific order by ID or order number, with items.
    
    selectinload(Order.items) tells SQLAlchemy: "When you fetch
    the order, also fetch all its items in one efficient query."
    Without this, accessing order.items would trigger a separate
    query for each order — the dreaded N+1 problem.
    """
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(
            (Order.id == order_id) | (Order.order_number == order_id.upper())
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


@router.post("/", response_model=OrderWithItems, status_code=status.HTTP_201_CREATED)
async def create_order(order_data: OrderCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new order with items.
    
    This is a TRANSACTION — if any step fails (user not found,
    product out of stock, etc.), nothing gets saved to the database.
    This prevents partial orders (e.g., order created but items missing).
    
    Steps:
    1. Verify user exists
    2. For each item: verify product exists, check stock, compute subtotal
    3. Calculate order totals
    4. Save order + items together
    5. Return the complete order with items
    """
    # Step 1: Verify user
    user_result = await db.execute(
        select(User).where(User.id == order_data.user_id)
    )
    if not user_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Step 2: Validate products and build items
    subtotal = Decimal("0")
    order_items = []

    for item_data in order_data.items:
        product_result = await db.execute(
            select(Product).where(Product.id == item_data.product_id)
        )
        product = product_result.scalar_one_or_none()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item_data.product_id} not found"
            )

        if product.stock_quantity < item_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for {product.name_en}. "
                       f"Available: {product.stock_quantity}, "
                       f"requested: {item_data.quantity}"
            )

        item_subtotal = product.price * item_data.quantity
        subtotal += item_subtotal

        order_items.append(OrderItem(
            id=str(uuid.uuid4()),
            product_id=product.id,
            quantity=item_data.quantity,
            unit_price=product.price,  # Snapshot the current price
            subtotal=item_subtotal,
        ))

    # Step 3: Create order
    shipping = Decimal("15.00")
    order = Order(
        id=str(uuid.uuid4()),
        order_number=generate_order_number(),
        user_id=order_data.user_id,
        status="pending",
        subtotal=subtotal,
        discount_amount=Decimal("0"),
        shipping_cost=shipping,
        total_amount=subtotal + shipping,
        notes=order_data.notes,
    )

    # Step 4: Associate items and save everything
    for item in order_items:
        item.order_id = order.id
        db.add(item)

    db.add(order)
    await db.commit()

    # Step 5: Reload with items for the response
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order.id)
    )
    return result.scalar_one()
