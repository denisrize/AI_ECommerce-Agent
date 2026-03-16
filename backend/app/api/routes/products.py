from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Optional
import uuid

from app.models.connection import get_db
from app.models.database import Product
from app.models.schemas import ProductCreate, ProductResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 10,
    category: Optional[str] = None,
    search: Optional[str] = None,
    in_stock: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List products with optional filters.
    
    This endpoint demonstrates query composition — we start with
    a base query and conditionally add WHERE clauses. SQLAlchemy
    builds the final SQL from whatever filters are provided.
    
    Examples:
      GET /products                     → all active products
      GET /products?category=Electronics → only electronics
      GET /products?search=headphones    → name/SKU contains "headphones"
      GET /products?in_stock=true        → only items with stock > 0
      GET /products?category=Electronics&in_stock=true → combined filters
    
    The agent's search_products tool will use very similar logic.
    """
    query = select(Product).where(Product.active == True)

    if category:
        query = query.where(Product.category == category)

    if search:
        # ilike = case-insensitive LIKE. The % wildcards mean
        # "anything before or after the search term."
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Product.name_en.ilike(search_term),
                Product.name_he.ilike(search_term),
                Product.sku.ilike(search_term),
            )
        )

    if in_stock is not None:
        if in_stock:
            query = query.where(Product.stock_quantity > 0)
        else:
            query = query.where(Product.stock_quantity == 0)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get a specific product by ID or SKU.
    
    Why check both ID and SKU? Because customers might say
    "tell me about ELEC-HP-001" (the SKU) or the agent might
    have an internal ID. Supporting both makes the API flexible.
    """
    result = await db.execute(
        select(Product).where(
            or_(Product.id == product_id, Product.sku == product_id.upper())
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    """Create a new product."""
    existing = await db.execute(
        select(Product).where(Product.sku == product.sku.upper())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product SKU already exists"
        )

    db_product = Product(
        id=str(uuid.uuid4()),
        **product.model_dump(),
        sku=product.sku.upper(),
    )
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product
