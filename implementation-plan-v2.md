# E-commerce Operations Agent - Implementation Plan (Windows + Conda) v2

## Philosophy

**"Make it work, make it right, make it fast"** - Kent Beck

Each phase ends with a **working system** you can demo.

---

## Overview: The 7 Phases

```
Phase 0: Environment Setup (Day 1)
    ↓ ✓ Conda, Docker, DB running
Phase 1: Database & Basic API (Days 2-4)  
    ↓ ✓ Alembic migrations, CRUD, tests pass
Phase 2: Basic Agent - Streaming (Days 5-6)
    ↓ ✓ SSE streaming chat works
Phase 3: Agent with Tools (Days 7-9)
    ↓ ✓ Agent calls tools, complete flows work
Phase 4: Frontend Chat UI (Days 10-12)
    ↓ ✓ Full working app locally
Phase 5: Testing & Hardening (Days 13-15)
    ↓ ✓ Tests pass, edge cases handled
Phase 6: Cloud Deployment (Days 16-18)
    ↓ ✓ Running on AWS
Phase 7: Polish & Documentation (Days 19-20)
    ↓ ✓ Portfolio-ready project
```

**Total: ~20 days**

---

## Windows + Conda Prerequisites

### Required Software

| Software | Download Link | Notes |
|----------|---------------|-------|
| **Miniconda** | https://docs.conda.io/en/latest/miniconda.html | Lighter than Anaconda |
| **Docker Desktop** | https://www.docker.com/products/docker-desktop/ | Requires WSL2 |
| **Node.js 20+** | https://nodejs.org/ | LTS version |
| **Git** | https://git-scm.com/download/win | Includes Git Bash |
| **VS Code** | https://code.visualstudio.com/ | Recommended IDE |

---

# PHASE 0: Environment Setup + Database
**Duration:** 1 day  
**Goal:** Conda env, Docker, PostgreSQL running

## Step 0.1: Install/Verify Miniconda

If not installed:
1. Download from https://docs.conda.io/en/latest/miniconda.html
2. Run installer
3. ✅ Check "Add Miniconda to PATH"

Verify (open **new** terminal):
```powershell
conda --version
# Should show: conda 23.x.x or similar
```

## Step 0.2: Install WSL2 + Docker Desktop

### WSL2 First
```powershell
# Run PowerShell as Administrator
wsl --install
# Restart computer
wsl --set-default-version 2
```

### Docker Desktop
1. Download from https://www.docker.com/products/docker-desktop/
2. Install with WSL2 backend
3. Launch and wait for startup

Verify:
```powershell
docker --version
docker run hello-world
```

## Step 0.3: Install Node.js and Git

```powershell
# After installing from websites, verify:
node --version   # v20.x.x
npm --version    # 10.x.x
git --version    # 2.x.x
```

## Step 0.4: Create Project Structure

```powershell
# Create and enter project directory
mkdir ecommerce-agent
cd ecommerce-agent

# Initialize git
git init

# Create directory structure
mkdir backend
mkdir backend\app
mkdir backend\app\api
mkdir backend\app\api\routes
mkdir backend\app\agent
mkdir backend\app\tools
mkdir backend\app\models
mkdir backend\tests
mkdir backend\scripts
mkdir frontend
mkdir docs

# Create initial files
New-Item -ItemType File -Path backend\app\__init__.py -Force
New-Item -ItemType File -Path backend\app\main.py -Force
New-Item -ItemType File -Path docker-compose.yml -Force
New-Item -ItemType File -Path .env.example -Force
New-Item -ItemType File -Path .gitignore -Force
New-Item -ItemType File -Path README.md -Force
```

## Step 0.5: Create Conda Environment

```powershell
# Create environment with Python 3.11
conda create -n ecommerce-agent python=3.11 -y

# Activate
conda activate ecommerce-agent

# Verify (prompt shows (ecommerce-agent))
python --version
```

## Step 0.6: Create environment.yml

Create `backend/environment.yml`:
```yaml
name: ecommerce-agent
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - pip
  - pip:
    # Web framework
    - fastapi==0.109.0
    - uvicorn[standard]==0.27.0
    - sse-starlette==2.0.0
    # Database
    - sqlalchemy==2.0.25
    - asyncpg==0.29.0
    - alembic==1.13.1
    # Config & validation
    - pydantic==2.5.3
    - pydantic-settings==2.1.0
    - python-dotenv==1.0.0
    # Testing
    - pytest==7.4.4
    - pytest-asyncio==0.23.3
    - httpx==0.26.0
```

Install dependencies:
```powershell
cd backend
conda activate ecommerce-agent
pip install fastapi==0.109.0 uvicorn[standard]==0.27.0 sse-starlette==2.0.0
pip install sqlalchemy==2.0.25 asyncpg==0.29.0 alembic==1.13.1
pip install pydantic==2.5.3 pydantic-settings==2.1.0 python-dotenv==1.0.0
pip install pytest==7.4.4 pytest-asyncio==0.23.3 httpx==0.26.0
```

## Step 0.7: Create Docker Compose (DB Early!)

Create `docker-compose.yml` in project root:
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: ecommerce-db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: ecommerce
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

Start the database:
```powershell
# From project root
docker-compose up -d db

# Verify
docker-compose ps
# Should show ecommerce-db running and healthy

docker-compose logs db
# Should see "database system is ready to accept connections"
```

## Step 0.8: Create .env Files

Create `backend/.env`:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ecommerce
SYNC_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ecommerce
DEBUG=true
```

Create `.env.example` in project root:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ecommerce
SYNC_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ecommerce
DEBUG=true
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview
```

## Step 0.9: Create Minimal FastAPI App

Create `backend/app/main.py`:
```python
from fastapi import FastAPI

app = FastAPI(
    title="E-commerce Agent API",
    description="AI-powered e-commerce operations assistant",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {"message": "E-commerce Agent API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

## Step 0.10: Run and Verify

```powershell
cd backend
conda activate ecommerce-agent
uvicorn app.main:app --reload --port 8000
```

Test:
- http://localhost:8000/ → `{"message":"E-commerce Agent API is running"}`
- http://localhost:8000/health → `{"status":"healthy"}`
- http://localhost:8000/docs → Swagger UI

## Step 0.11: Create .gitignore

Create `.gitignore`:
```
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/

# Environment
.env
*.env.local
venv/

# Conda
.conda/

# Node
node_modules/

# IDE
.vscode/
.idea/

# Testing
.coverage
.pytest_cache/
htmlcov/

# OS
.DS_Store
Thumbs.db

# Alembic
*.db
```

## Step 0.12: First Commit

```powershell
git add .
git commit -m "Phase 0: Environment setup with Conda, Docker, PostgreSQL"
```

## ✅ Phase 0 Validation Checklist

- [ ] Conda environment works (`conda activate ecommerce-agent`)
- [ ] Docker Desktop running
- [ ] PostgreSQL container running (`docker-compose ps` shows healthy)
- [ ] FastAPI app runs on http://localhost:8000
- [ ] `/health` returns `{"status": "healthy"}`
- [ ] Git repository initialized with first commit

---

# PHASE 1: Database with Alembic Migrations
**Duration:** 2-3 days  
**Goal:** Proper migrations, full schema with order_items, CRUD APIs, tests

## Step 1.1: Create Configuration

Create `backend/app/config.py`:
```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ecommerce"
    sync_database_url: str = "postgresql://postgres:postgres@localhost:5432/ecommerce"
    
    # App
    app_name: str = "E-commerce Agent"
    debug: bool = True
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

## Step 1.2: Create Database Models (with order_items)

Create `backend/app/models/__init__.py`:
```python
from app.models.database import Base, User, Product, Order, OrderItem
from app.models.connection import get_db, engine, AsyncSessionLocal
```

Create `backend/app/models/database.py`:
```python
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, 
    ForeignKey, Text, Numeric, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    preferred_lang: Mapped[str] = mapped_column(String(5), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    orders: Mapped[List["Order"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"


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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    order_items: Mapped[List["OrderItem"]] = relationship(back_populates="product")
    
    def __repr__(self) -> str:
        return f"<Product {self.sku}>"


class Order(Base):
    __tablename__ = "orders"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Order {self.order_number}>"


class OrderItem(Base):
    __tablename__ = "order_items"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)  # Price at time of purchase
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")
    
    # Composite index for common queries
    __table_args__ = (
        Index('idx_order_items_order_product', 'order_id', 'product_id'),
    )
    
    def __repr__(self) -> str:
        return f"<OrderItem {self.order_id}:{self.product_id}>"
```

Create `backend/app/models/connection.py`:
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

## Step 1.3: Initialize Alembic

```powershell
cd backend
conda activate ecommerce-agent

# Initialize Alembic
alembic init alembic
```

This creates:
- `alembic/` directory
- `alembic.ini` file

## Step 1.4: Configure Alembic

Update `backend/alembic.ini` - find and change this line:
```ini
# Change from:
# sqlalchemy.url = driver://user:pass@localhost/dbname

# To (we'll override in env.py, but set a default):
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/ecommerce
```

Replace `backend/alembic/env.py` entirely:
```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import your models and config
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.models.database import Base

# this is the Alembic Config object
config = context.config

# Set the database URL from our settings
config.set_main_option("sqlalchemy.url", settings.sync_database_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    from sqlalchemy.ext.asyncio import create_async_engine
    
    connectable = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # For async, we need to run in an event loop
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## Step 1.5: Create Initial Migration

```powershell
cd backend
conda activate ecommerce-agent

# Generate migration from models
alembic revision --autogenerate -m "Initial schema with users, products, orders, order_items"

# Apply migration
alembic upgrade head
```

Verify migration:
```powershell
# Check migration status
alembic current

# Connect to database and verify tables
docker-compose exec db psql -U postgres -d ecommerce -c "\dt"
# Should show: users, products, orders, order_items, alembic_version
```

## Step 1.6: Create Pydantic Schemas

Create `backend/app/models/schemas.py`:
```python
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


# ============== User Schemas ==============
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    preferred_lang: str = Field(default="en", pattern="^(en|he)$")


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============== Product Schemas ==============
class ProductBase(BaseModel):
    sku: str
    name_en: str
    name_he: str
    description_en: Optional[str] = None
    description_he: Optional[str] = None
    category: str
    price: Decimal = Field(ge=0)
    stock_quantity: int = Field(ge=0, default=0)


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: str
    active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============== OrderItem Schemas ==============
class OrderItemBase(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: str
    unit_price: Decimal
    subtotal: Decimal
    
    class Config:
        from_attributes = True


class OrderItemWithProduct(OrderItemResponse):
    """OrderItem with nested product info for display."""
    product: ProductResponse


# ============== Order Schemas ==============
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
    """Order with nested items for display."""
    items: List[OrderItemResponse]


class OrderDetail(OrderResponse):
    """Full order detail with items and product info."""
    items: List[OrderItemWithProduct]
```

## Step 1.7: Create API Routes

Create `backend/app/api/__init__.py` (empty file)

Create `backend/app/api/routes/__init__.py`:
```python
from app.api.routes import products, users, orders
```

Create `backend/app/api/routes/users.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from app.models.connection import get_db
from app.models.database import User
from app.models.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """List all users with pagination."""
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user."""
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == user.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    db_user = User(id=str(uuid.uuid4()), **user.model_dump())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
```

Create `backend/app/api/routes/products.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    """List products with optional filters."""
    query = select(Product).where(Product.active == True)
    
    if category:
        query = query.where(Product.category == category)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Product.name_en.ilike(search_term),
                Product.name_he.ilike(search_term),
                Product.sku.ilike(search_term)
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
    """Get a specific product by ID or SKU."""
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
    # Check if SKU exists
    existing = await db.execute(select(Product).where(Product.sku == product.sku.upper()))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product SKU already exists"
        )
    
    db_product = Product(
        id=str(uuid.uuid4()),
        **product.model_dump(),
        sku=product.sku.upper()
    )
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product
```

Create `backend/app/api/routes/orders.py`:
```python
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
    """Generate a human-readable order number."""
    return f"ORD-{datetime.now().strftime('%Y')}-{uuid.uuid4().hex[:5].upper()}"


@router.get("/", response_model=List[OrderResponse])
async def list_orders(
    user_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """List orders with optional filters."""
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
    """Get a specific order by ID or order number with items."""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where((Order.id == order_id) | (Order.order_number == order_id.upper()))
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
    """Create a new order with items."""
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == order_data.user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate products and calculate totals
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
                detail=f"Insufficient stock for {product.name_en}"
            )
        
        item_subtotal = product.price * item_data.quantity
        subtotal += item_subtotal
        
        order_items.append(OrderItem(
            id=str(uuid.uuid4()),
            product_id=product.id,
            quantity=item_data.quantity,
            unit_price=product.price,
            subtotal=item_subtotal
        ))
    
    # Create order
    order = Order(
        id=str(uuid.uuid4()),
        order_number=generate_order_number(),
        user_id=order_data.user_id,
        status="pending",
        subtotal=subtotal,
        discount_amount=Decimal("0"),
        shipping_cost=Decimal("15.00"),  # Fixed shipping for now
        total_amount=subtotal + Decimal("15.00"),
        notes=order_data.notes
    )
    
    # Associate items
    for item in order_items:
        item.order_id = order.id
        db.add(item)
    
    db.add(order)
    await db.commit()
    
    # Reload with items
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
    )
    return result.scalar_one()
```

## Step 1.8: Update Main App

Update `backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import products, users, orders

app = FastAPI(
    title="E-commerce Agent API",
    description="AI-powered e-commerce operations assistant",
    version="0.1.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "E-commerce Agent API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
```

## Step 1.9: Create Seed Script

Create `backend/scripts/__init__.py` (empty file)

Create `backend/scripts/seed_data.py`:
```python
import asyncio
import uuid
import random
import sys
from pathlib import Path
from decimal import Decimal

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.connection import AsyncSessionLocal
from app.models.database import User, Product, Order, OrderItem
from sqlalchemy import select


USERS = [
    {"email": "david.cohen@email.com", "full_name": "David Cohen", "phone": "+972-50-111-1111", "preferred_lang": "he"},
    {"email": "sarah.levi@email.com", "full_name": "Sarah Levi", "phone": "+972-52-222-2222", "preferred_lang": "he"},
    {"email": "john.smith@email.com", "full_name": "John Smith", "phone": "+972-54-333-3333", "preferred_lang": "en"},
    {"email": "emma.wilson@email.com", "full_name": "Emma Wilson", "phone": "+972-50-444-4444", "preferred_lang": "en"},
    {"email": "michael.brown@email.com", "full_name": "Michael Brown", "phone": "+972-52-555-5555", "preferred_lang": "en"},
    {"email": "yael.mizrachi@email.com", "full_name": "Yael Mizrachi", "phone": "+972-54-666-6666", "preferred_lang": "he"},
    {"email": "daniel.gold@email.com", "full_name": "Daniel Gold", "phone": "+972-50-777-7777", "preferred_lang": "en"},
    {"email": "maya.berkowitz@email.com", "full_name": "Maya Berkowitz", "phone": "+972-52-888-8888", "preferred_lang": "he"},
    {"email": "alex.johnson@email.com", "full_name": "Alex Johnson", "phone": "+972-54-999-9999", "preferred_lang": "en"},
    {"email": "noa.shapira@email.com", "full_name": "Noa Shapira", "phone": "+972-50-000-0000", "preferred_lang": "he"},
]

PRODUCTS = [
    {"sku": "ELEC-HP-001", "name_en": "Wireless Headphones Pro", "name_he": "אוזניות אלחוטיות פרו", "category": "Electronics", "price": Decimal("299.99"), "stock_quantity": 45, "description_en": "Premium wireless headphones with ANC", "description_he": "אוזניות אלחוטיות פרימיום עם ביטול רעשים"},
    {"sku": "ELEC-SW-001", "name_en": "Smart Watch Elite", "name_he": "שעון חכם אליט", "category": "Electronics", "price": Decimal("449.99"), "stock_quantity": 30, "description_en": "Advanced smartwatch", "description_he": "שעון חכם מתקדם"},
    {"sku": "ELEC-BS-001", "name_en": "Bluetooth Speaker", "name_he": "רמקול בלוטות'", "category": "Electronics", "price": Decimal("149.99"), "stock_quantity": 60, "description_en": "Portable waterproof speaker", "description_he": "רמקול נייד עמיד במים"},
    {"sku": "ELEC-CH-001", "name_en": "Wireless Charger", "name_he": "מטען אלחוטי", "category": "Electronics", "price": Decimal("49.99"), "stock_quantity": 100, "description_en": "Fast wireless charging pad", "description_he": "משטח טעינה מהירה"},
    {"sku": "ELEC-HB-001", "name_en": "USB-C Hub", "name_he": "מפצל USB-C", "category": "Electronics", "price": Decimal("79.99"), "stock_quantity": 55, "description_en": "7-in-1 USB-C hub", "description_he": "מפצל USB-C עם 7 חיבורים"},
    {"sku": "HOME-CF-001", "name_en": "Coffee Maker Pro", "name_he": "מכונת קפה פרו", "category": "Home & Kitchen", "price": Decimal("199.99"), "stock_quantity": 25, "description_en": "Programmable coffee maker", "description_he": "מכונת קפה עם תכנות"},
    {"sku": "HOME-AF-001", "name_en": "Air Fryer XL", "name_he": "סיר טיגון באוויר", "category": "Home & Kitchen", "price": Decimal("129.99"), "stock_quantity": 35, "description_en": "Large air fryer", "description_he": "סיר טיגון באוויר גדול"},
    {"sku": "HOME-KS-001", "name_en": "Kitchen Scale", "name_he": "משקל מטבח", "category": "Home & Kitchen", "price": Decimal("34.99"), "stock_quantity": 80, "description_en": "Digital kitchen scale", "description_he": "משקל מטבח דיגיטלי"},
    {"sku": "HOME-BL-001", "name_en": "Power Blender", "name_he": "בלנדר חזק", "category": "Home & Kitchen", "price": Decimal("89.99"), "stock_quantity": 40, "description_en": "High-power blender", "description_he": "בלנדר בעל עוצמה גבוהה"},
    {"sku": "ACC-PC-001", "name_en": "Phone Case Premium", "name_he": "כיסוי פרימיום לטלפון", "category": "Accessories", "price": Decimal("29.99"), "stock_quantity": 150, "description_en": "Shockproof phone case", "description_he": "כיסוי עמיד לזעזועים"},
]

ORDER_STATUSES = ["pending", "confirmed", "processing", "shipped", "delivered"]


async def seed_database():
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(select(User).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping...")
            return
        
        print("Seeding database...")
        
        # Create users
        users = []
        for user_data in USERS:
            user = User(id=str(uuid.uuid4()), **user_data)
            db.add(user)
            users.append(user)
        
        # Create products
        products = []
        for product_data in PRODUCTS:
            product = Product(id=str(uuid.uuid4()), **product_data)
            db.add(product)
            products.append(product)
        
        await db.flush()  # Get IDs without committing
        
        # Create orders with items
        for i in range(25):
            user = random.choice(users)
            num_items = random.randint(1, 3)
            order_products = random.sample(products, num_items)
            
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
                    subtotal=item_subtotal
                ))
            
            shipping = Decimal("15.00")
            order = Order(
                id=str(uuid.uuid4()),
                order_number=f"ORD-2024-{str(i+1).zfill(5)}",
                user_id=user.id,
                status=random.choice(ORDER_STATUSES),
                subtotal=subtotal,
                discount_amount=Decimal("0"),
                shipping_cost=shipping,
                total_amount=subtotal + shipping
            )
            db.add(order)
            
            for item in items:
                item.order_id = order.id
                db.add(item)
        
        await db.commit()
        print("✅ Database seeded successfully!")
        print(f"   - {len(USERS)} users")
        print(f"   - {len(PRODUCTS)} products")
        print(f"   - 25 orders with items")


if __name__ == "__main__":
    asyncio.run(seed_database())
```

## Step 1.10: Create Tests

Create `backend/tests/__init__.py` (empty file)

Create `backend/tests/conftest.py`:
```python
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.models.database import Base
from app.models.connection import get_db

# Test database URL (use same DB but could use separate test DB)
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/ecommerce"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    engine = create_async_engine(TEST_DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
        await session.rollback()
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database session override."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()
```

Create `backend/tests/test_api.py`:
```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test the health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient):
    """Test listing users."""
    response = await client.get("/api/v1/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient):
    """Test listing products."""
    response = await client.get("/api/v1/products")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_products_with_filter(client: AsyncClient):
    """Test listing products with category filter."""
    response = await client.get("/api/v1/products?category=Electronics")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_nonexistent_user(client: AsyncClient):
    """Test getting a user that doesn't exist."""
    response = await client.get("/api/v1/users/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_product(client: AsyncClient):
    """Test getting a product that doesn't exist."""
    response = await client.get("/api/v1/products/nonexistent-id")
    assert response.status_code == 404
```

Create `backend/pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v
```

## Step 1.11: Run and Verify

```powershell
# Terminal 1: Ensure DB is running
docker-compose up -d db
docker-compose ps

# Terminal 2: Run app
cd backend
conda activate ecommerce-agent
uvicorn app.main:app --reload --port 8000

# Terminal 3: Seed database
cd backend
conda activate ecommerce-agent
python -m scripts.seed_data

# Terminal 3: Run tests
pytest

# Test APIs manually
Invoke-RestMethod http://localhost:8000/api/v1/users
Invoke-RestMethod http://localhost:8000/api/v1/products
Invoke-RestMethod http://localhost:8000/api/v1/orders
```

## ✅ Phase 1 Validation Checklist

- [ ] Alembic initialized (`alembic/` folder exists)
- [ ] Migration created and applied (`alembic upgrade head` works)
- [ ] Tables created: users, products, orders, order_items, alembic_version
- [ ] Seed script runs successfully
- [ ] All 6 tests pass (`pytest` shows 6 passed)
- [ ] `GET /api/v1/users` returns 10 users
- [ ] `GET /api/v1/products` returns 10 products  
- [ ] `GET /api/v1/products?category=Electronics` filters work
- [ ] `GET /api/v1/orders` returns 25 orders with items
- [ ] `GET /api/v1/orders/{id}` returns order with nested items

```powershell
git add .
git commit -m "Phase 1: Database with Alembic migrations, order_items, CRUD APIs, tests"
```

---

# PHASE 2: Basic Agent with SSE Streaming
**Duration:** 2 days  
**Goal:** Proper SSE streaming chat (no tools yet)

## Step 2.1: Add OpenAI Dependency

```powershell
conda activate ecommerce-agent
pip install openai==1.12.0
```

Update `backend/environment.yml` to include:
```yaml
    - openai==1.12.0
```

## Step 2.2: Update Configuration

Update `backend/app/config.py`:
```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ecommerce"
    sync_database_url: str = "postgresql://postgres:postgres@localhost:5432/ecommerce"
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    
    # App
    app_name: str = "E-commerce Agent"
    debug: bool = True
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

Update `backend/.env`:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ecommerce
SYNC_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ecommerce
DEBUG=true
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview
```

## Step 2.3: Create Agent Module

Create `backend/app/agent/__init__.py` (empty file)

Create `backend/app/agent/orchestrator.py`:
```python
from openai import AsyncOpenAI
from typing import AsyncGenerator, List, Dict
from app.config import settings

# Initialize OpenAI client
client = AsyncOpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """You are a helpful customer service agent for ShopFlow, an e-commerce platform.

You help customers with:
- Order status and tracking
- Product information and availability
- Returns and refunds
- General inquiries

Guidelines:
1. Be friendly, professional, and concise
2. Respond in the same language the customer uses (English or Hebrew)
3. If you don't have specific information, say so honestly
4. Never make up order numbers or product details

Current limitations (demo mode):
- You cannot look up real orders or products yet
- Real database integration coming soon

For now, you can:
- Explain how things work
- Answer general questions
- Provide helpful information about policies
"""


async def stream_chat_completion(
    messages: List[Dict[str, str]]
) -> AsyncGenerator[str, None]:
    """
    Stream chat completion from OpenAI.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        
    Yields:
        Text chunks as they arrive from OpenAI
    """
    full_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *messages
    ]
    
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=full_messages,
        stream=True,
        temperature=0.7,
        max_tokens=1000
    )
    
    async for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def get_chat_completion(messages: List[Dict[str, str]]) -> str:
    """
    Get complete (non-streaming) chat completion.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        
    Returns:
        Complete response text
    """
    full_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *messages
    ]
    
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=full_messages,
        stream=False,
        temperature=0.7,
        max_tokens=1000
    )
    
    return response.choices[0].message.content
```

## Step 2.4: Create Chat Route with EventSourceResponse

Create `backend/app/api/routes/chat.py`:
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json

from sse_starlette.sse import EventSourceResponse
from app.agent.orchestrator import stream_chat_completion, get_chat_completion

router = APIRouter(prefix="/chat", tags=["chat"])


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    stream: bool = True
    user_id: Optional[str] = None  # For future user context


class ChatResponse(BaseModel):
    response: str


@router.post("/")
async def chat(request: ChatRequest):
    """
    Chat with the AI agent.
    
    - If stream=True (default): Returns Server-Sent Events
    - If stream=False: Returns complete JSON response
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages cannot be empty")
    
    # Convert to dict format for OpenAI
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    
    if request.stream:
        return EventSourceResponse(
            stream_generator(messages),
            media_type="text/event-stream"
        )
    else:
        response = await get_chat_completion(messages)
        return ChatResponse(response=response)


async def stream_generator(messages: List[dict]):
    """
    Generator for SSE streaming.
    
    Yields events in the format expected by EventSourceResponse:
    - data: JSON with content chunk
    - event: 'message' (default) or 'done'
    """
    try:
        async for chunk in stream_chat_completion(messages):
            # Yield each chunk as a JSON object
            yield {
                "event": "message",
                "data": json.dumps({"content": chunk})
            }
        
        # Signal completion
        yield {
            "event": "done",
            "data": json.dumps({"status": "complete"})
        }
        
    except Exception as e:
        # Send error event
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)})
        }
```

## Step 2.5: Update Main App

Update `backend/app/api/routes/__init__.py`:
```python
from app.api.routes import products, users, orders, chat
```

Update `backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import products, users, orders, chat

app = FastAPI(
    title="E-commerce Agent API",
    description="AI-powered e-commerce operations assistant",
    version="0.1.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "E-commerce Agent API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
```

## Step 2.6: Add Chat Tests

Add to `backend/tests/test_api.py`:
```python
@pytest.mark.asyncio
async def test_chat_non_streaming(client: AsyncClient):
    """Test non-streaming chat endpoint."""
    # Skip if no API key configured
    from app.config import settings
    if not settings.openai_api_key:
        pytest.skip("OpenAI API key not configured")
    
    response = await client.post(
        "/api/v1/chat",
        json={
            "messages": [{"role": "user", "content": "Hello!"}],
            "stream": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert len(data["response"]) > 0


@pytest.mark.asyncio
async def test_chat_empty_messages(client: AsyncClient):
    """Test chat with empty messages returns error."""
    response = await client.post(
        "/api/v1/chat",
        json={
            "messages": [],
            "stream": False
        }
    )
    assert response.status_code == 400
```

## Step 2.7: Create Test Script for Streaming

Create `backend/scripts/test_streaming.py`:
```python
"""
Manual test script for SSE streaming.
Run with: python -m scripts.test_streaming
"""
import asyncio
import httpx


async def test_streaming():
    print("Testing SSE streaming chat...\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/api/v1/chat",
            json={
                "messages": [{"role": "user", "content": "Tell me a short joke"}],
                "stream": True
            }
        ) as response:
            print("Streaming response:")
            print("-" * 40)
            
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    import json
                    data = json.loads(line[5:].strip())
                    if "content" in data:
                        print(data["content"], end="", flush=True)
                    elif "status" in data:
                        print(f"\n\n[{data['status']}]")
            
            print("-" * 40)


async def test_hebrew():
    print("\nTesting Hebrew response...\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "http://localhost:8000/api/v1/chat",
            json={
                "messages": [{"role": "user", "content": "שלום, מה שלומך?"}],
                "stream": False
            }
        )
        
        data = response.json()
        print("Hebrew response:")
        print("-" * 40)
        print(data["response"])
        print("-" * 40)


if __name__ == "__main__":
    asyncio.run(test_streaming())
    asyncio.run(test_hebrew())
```

## Step 2.8: Run and Test

```powershell
# Make sure app is running
cd backend
conda activate ecommerce-agent
uvicorn app.main:app --reload --port 8000

# In another terminal, test streaming
cd backend
conda activate ecommerce-agent
python -m scripts.test_streaming

# Run tests (some will skip without API key)
pytest -v
```

**Test with curl (if installed):**
```powershell
# Non-streaming
curl -X POST http://localhost:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d '{"messages": [{"role": "user", "content": "Hello!"}], "stream": false}'

# Streaming (you'll see SSE events)
curl -X POST http://localhost:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d '{"messages": [{"role": "user", "content": "Tell me a joke"}], "stream": true}'
```

## ✅ Phase 2 Validation Checklist

- [ ] OpenAI API key configured in `.env`
- [ ] Non-streaming chat works (`stream: false`)
- [ ] Streaming chat shows SSE events (`stream: true`)
- [ ] Agent responds in English to English
- [ ] Agent responds in Hebrew to Hebrew (שלום)
- [ ] Error handling works (empty messages returns 400)
- [ ] Tests pass (8 tests now)

```powershell
git add .
git commit -m "Phase 2: SSE streaming chat with EventSourceResponse"
```

---

# Quick Reference: Conda Commands

```powershell
# Activate environment
conda activate ecommerce-agent

# Deactivate
conda deactivate

# List installed packages
pip list

# Export environment
conda env export > environment.yml

# Run app
uvicorn app.main:app --reload --port 8000

# Run tests
pytest -v

# Run specific test
pytest tests/test_api.py::test_health_endpoint -v

# Alembic commands
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
alembic current
alembic history
```

---

# Continue to Phases 3-7

The remaining phases work similarly:

- **Phase 3**: Add tools (get_product_info, get_order_status, etc.)
- **Phase 4**: React frontend with SSE consumption
- **Phase 5**: More tests, error handling, edge cases
- **Phase 6**: Docker production build, AWS deployment
- **Phase 7**: Documentation, screenshots, polish

Would you like me to continue with **Phases 3-7**?
