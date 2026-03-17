"""
API endpoint tests.

These tests assume the database has been seeded (scripts/seed_data.py).
Run: cd backend && pytest -v

Test naming convention: test_<what>_<expected_outcome>
  - test_health_endpoint         → verifies the app is alive
  - test_list_users_returns_data → verifies seeded users are returned
  - test_get_user_not_found      → verifies 404 for bad IDs
"""
import pytest
from httpx import AsyncClient


# ══════════════════════════════════════════════════════════════
# Health & Root
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """The root endpoint should return a welcome message."""
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "E-commerce Agent API is running"


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """The health endpoint should confirm the app is healthy."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


# ══════════════════════════════════════════════════════════════
# Users
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_list_users_returns_data(client: AsyncClient):
    """After seeding, we should have users in the database."""
    response = await client.get("/api/v1/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Seeded data should have 10 users
    assert len(data) == 10


@pytest.mark.asyncio
async def test_list_users_pagination(client: AsyncClient):
    """Pagination should limit results correctly."""
    response = await client.get("/api/v1/users?limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 3


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient):
    """Requesting a non-existent user should return 404."""
    response = await client.get("/api/v1/users/nonexistent-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ══════════════════════════════════════════════════════════════
# Products
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_list_products_returns_data(client: AsyncClient):
    """After seeding, we should have products in the database."""
    response = await client.get("/api/v1/products")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 10


@pytest.mark.asyncio
async def test_list_products_filter_by_category(client: AsyncClient):
    """Filtering by category should return only matching products."""
    response = await client.get("/api/v1/products?category=Electronics")
    assert response.status_code == 200
    data = response.json()
    # We seeded 5 electronics products
    assert len(data) == 5
    for product in data:
        assert product["category"] == "Electronics"


@pytest.mark.asyncio
async def test_list_products_search(client: AsyncClient):
    """Search should find products by name (case-insensitive)."""
    response = await client.get("/api/v1/products?search=headphones")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "headphones" in data[0]["name_en"].lower()


@pytest.mark.asyncio
async def test_list_products_in_stock_filter(client: AsyncClient):
    """in_stock=true should exclude out-of-stock products."""
    response = await client.get("/api/v1/products?in_stock=true")
    assert response.status_code == 200
    data = response.json()
    # We seeded 2 out-of-stock products, so 8 should be in stock
    assert len(data) == 8
    for product in data:
        assert product["stock_quantity"] > 0


@pytest.mark.asyncio
async def test_list_products_out_of_stock(client: AsyncClient):
    """in_stock=false should return only out-of-stock products."""
    response = await client.get("/api/v1/products?in_stock=false")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for product in data:
        assert product["stock_quantity"] == 0


@pytest.mark.asyncio
async def test_get_product_not_found(client: AsyncClient):
    """Requesting a non-existent product should return 404."""
    response = await client.get("/api/v1/products/nonexistent-id")
    assert response.status_code == 404


# ══════════════════════════════════════════════════════════════
# Orders
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_list_orders_returns_data(client: AsyncClient):
    """After seeding, we should have orders in the database."""
    response = await client.get("/api/v1/orders")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 10  # Default limit is 10


@pytest.mark.asyncio
async def test_list_orders_by_status(client: AsyncClient):
    """Filtering by status should return only matching orders."""
    response = await client.get("/api/v1/orders?status_filter=delivered")
    assert response.status_code == 200
    data = response.json()
    for order in data:
        assert order["status"] == "delivered"


@pytest.mark.asyncio
async def test_get_order_by_number(client: AsyncClient):
    """Should be able to look up an order by its human-readable number."""
    response = await client.get("/api/v1/orders/ORD-2024-00001")
    assert response.status_code == 200
    data = response.json()
    assert data["order_number"] == "ORD-2024-00001"
    # OrderWithItems should include the items list
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_get_order_not_found(client: AsyncClient):
    """Requesting a non-existent order should return 404."""
    response = await client.get("/api/v1/orders/ORD-9999-XXXXX")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_order_has_correct_totals(client: AsyncClient):
    """Order totals should be consistent: total = subtotal + shipping - discount."""
    response = await client.get("/api/v1/orders/ORD-2024-00001")
    assert response.status_code == 200
    data = response.json()

    subtotal = float(data["subtotal"])
    discount = float(data["discount_amount"])
    shipping = float(data["shipping_cost"])
    total = float(data["total_amount"])

    expected_total = subtotal + shipping - discount
    assert abs(total - expected_total) < 0.01, (
        f"Total mismatch: {total} != {subtotal} + {shipping} - {discount}"
    )


# ══════════════════════════════════════════════════════════════
# Trailing Slash Handling
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_trailing_slash_get(client: AsyncClient):
    """Both /users and /users/ should return the same 200 response."""
    without_slash = await client.get("/api/v1/users")
    with_slash = await client.get("/api/v1/users/")

    assert without_slash.status_code == 200
    assert with_slash.status_code == 200
    assert without_slash.json() == with_slash.json()


@pytest.mark.asyncio
async def test_trailing_slash_post(client: AsyncClient):
    """POST to /chat/ should work the same as /chat (no redirect)."""
    response = await client.post(
        "/api/v1/chat/",
        json={"messages": [], "stream": False},
    )
    # Should get 400 (empty messages), NOT 307 redirect
    assert response.status_code == 400