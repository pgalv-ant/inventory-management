"""
Tests for restocking API endpoints.
"""
import pytest


class TestRestockingRecommendations:
    """Test suite for GET /api/restocking/recommendations."""

    def test_recommendations_basic(self, client):
        """Test getting recommendations with a mid-range budget."""
        response = client.get("/api/restocking/recommendations?budget=15000")
        assert response.status_code == 200

        data = response.json()
        assert "budget" in data
        assert "recommendations" in data
        assert "total_cost" in data
        assert "remaining_budget" in data
        assert data["budget"] == 15000
        assert isinstance(data["recommendations"], list)

    def test_recommendations_structure(self, client):
        """Test that each recommendation has the required fields."""
        response = client.get("/api/restocking/recommendations?budget=50000")
        data = response.json()

        assert len(data["recommendations"]) > 0
        for rec in data["recommendations"]:
            assert "sku" in rec
            assert "name" in rec
            assert "category" in rec
            assert "shortfall" in rec
            assert "recommended_quantity" in rec
            assert "unit_cost" in rec
            assert "line_total" in rec
            assert "lead_time_days" in rec
            assert isinstance(rec["shortfall"], int)
            assert isinstance(rec["recommended_quantity"], int)
            assert isinstance(rec["unit_cost"], (int, float))
            assert isinstance(rec["lead_time_days"], int)
            assert rec["recommended_quantity"] > 0
            assert rec["lead_time_days"] > 0

    def test_recommendations_within_budget(self, client):
        """Test that total_cost never exceeds the given budget."""
        for budget in [1000, 5000, 15000, 50000]:
            response = client.get(f"/api/restocking/recommendations?budget={budget}")
            data = response.json()
            assert data["total_cost"] <= budget
            assert abs(data["remaining_budget"] - (budget - data["total_cost"])) < 0.01

    def test_recommendations_line_total_calculation(self, client):
        """Test that line_total equals quantity times unit_cost."""
        response = client.get("/api/restocking/recommendations?budget=50000")
        data = response.json()

        for rec in data["recommendations"]:
            expected = rec["recommended_quantity"] * rec["unit_cost"]
            assert abs(rec["line_total"] - expected) < 0.01

    def test_recommendations_sorted_by_shortfall(self, client):
        """Test that recommendations are sorted by shortfall descending (largest-first priority)."""
        response = client.get("/api/restocking/recommendations?budget=50000")
        data = response.json()

        shortfalls = [r["shortfall"] for r in data["recommendations"]]
        assert shortfalls == sorted(shortfalls, reverse=True)

    def test_recommendations_tiny_budget(self, client):
        """Test that a budget too small for any single unit returns empty recommendations."""
        response = client.get("/api/restocking/recommendations?budget=1")
        assert response.status_code == 200
        data = response.json()
        assert data["recommendations"] == []
        assert data["total_cost"] == 0

    def test_recommendations_missing_budget(self, client):
        """Test that missing budget param returns a validation error."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 422


class TestPlaceRestockingOrder:
    """Test suite for POST /api/restocking/order."""

    def test_place_order_success(self, client):
        """Test that placing an order creates a Restocking-status order."""
        payload = {
            "items": [
                {"sku": "WDG-001", "name": "Industrial Widget Type A", "quantity": 150,
                 "unit_price": 42.50, "category": "Actuators", "lead_time_days": 10}
            ]
        }
        response = client.post("/api/restocking/order", json=payload)
        assert response.status_code == 200

        order = response.json()
        assert order["status"] == "Restocking"
        assert order["customer"] == "Internal Restock"
        assert order["order_number"].startswith("ORD-2025-R")
        assert len(order["items"]) == 1
        assert order["items"][0]["sku"] == "WDG-001"
        assert abs(order["total_value"] - 150 * 42.50) < 0.01

    def test_place_order_expected_delivery_uses_max_lead_time(self, client):
        """Test that expected_delivery is order_date plus the longest lead time among items."""
        from datetime import datetime
        payload = {
            "items": [
                {"sku": "SNR-420", "name": "Sensor", "quantity": 10,
                 "unit_price": 34.20, "category": "Sensors", "lead_time_days": 5},
                {"sku": "CTL-330", "name": "Controller", "quantity": 5,
                 "unit_price": 120.00, "category": "Controllers", "lead_time_days": 12},
            ]
        }
        response = client.post("/api/restocking/order", json=payload)
        order = response.json()

        ordered = datetime.fromisoformat(order["order_date"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        delta_days = (expected - ordered).days
        assert delta_days == 12

    def test_place_order_appears_in_orders_list(self, client):
        """Test that a placed restocking order is visible via GET /api/orders."""
        payload = {
            "items": [
                {"sku": "GSK-203", "name": "Gasket", "quantity": 100,
                 "unit_price": 12.30, "category": "Sensors", "lead_time_days": 5}
            ]
        }
        post_response = client.post("/api/restocking/order", json=payload)
        created = post_response.json()

        get_response = client.get("/api/orders")
        all_orders = get_response.json()
        matching = [o for o in all_orders if o["id"] == created["id"]]
        assert len(matching) == 1
        assert matching[0]["status"] == "Restocking"

    def test_place_order_empty_items_rejected(self, client):
        """Test that an empty items list returns a 400 error."""
        response = client.post("/api/restocking/order", json={"items": []})
        assert response.status_code == 400
        assert "detail" in response.json()
