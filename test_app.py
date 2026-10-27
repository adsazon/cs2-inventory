from fastapi.testclient import TestClient
from app_final import app, INVENTORY
import pytest

client = TestClient(app)

def setup_function():
    INVENTORY.clear()

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_version():
    r = client.get("/version")
    assert r.status_code == 200
    assert r.json()["app"]

def test_root_no_404():
    r = client.get("/")
    assert r.status_code == 200
    assert "docs" in r.json()

def test_favicon_no_404():
    r = client.get("/favicon.ico")
    assert r.status_code == 204

def test_add_and_get():
    r = client.post("/inventory/ak47", json={"price": 35.0, "qty": 2})
    assert r.status_code == 201
    assert client.get("/inventory").json()["ak47"]["qty"] == 2

def test_add_twice_updates_qty():
    client.post("/inventory/ak47", json={"price": 35.0, "qty": 2})
    client.post("/inventory/ak47", json={"price": 40.0, "qty": 1})
    data = client.get("/inventory").json()["ak47"]
    assert data["qty"] == 3
    assert data["price"] == 40.0

def test_delete_full_404():
    assert client.delete("/inventory/unknown").status_code == 404

def test_total_default_commission():
    client.post("/inventory/ak47", json={"price": 100.0, "qty": 1})
    r = client.get("/inventory/total")
    assert r.status_code == 200
    assert r.json()["total"] == 115.0

def test_total_custom_commission():
    client.post("/inventory/awp", json={"price": 200.0, "qty": 1})
    r = client.get("/inventory/total", params={"commission": 10})
    assert r.json()["total"] == 220.0

def test_total_empty_inventory():
    r = client.get("/inventory/total")
    assert r.status_code == 200
    data = r.json()
    assert data["unique_items"] == 0
    assert data["total_items"] == 0
    assert data["total"] == 0.0

def test_add_invalid_price():
    r = client.post("/inventory/x", json={"price": -5, "qty": 1})
    assert r.status_code == 422

def test_add_invalid_qty():
    r = client.post("/inventory/x", json={"price": 10, "qty": 0})
    assert r.status_code == 422

def test_add_missing_qty_defaults_to_1():
    r = client.post("/inventory/x", json={"price": 10})
    assert r.status_code == 201
    assert r.json()["qty"] == 1

def test_add_bad_item_name():
    r = client.post("/inventory/../evil", json={"price": 10, "qty": 1})
    assert r.status_code in (404, 422)

def test_total_commission_out_of_range():
    r = client.get("/inventory/total", params={"commission": 150})
    assert r.status_code == 422

def test_max_items_limit(monkeypatch):
    import app_final
    monkeypatch.setattr(app_final, "MAX_ITEMS", 1)
    client.post("/inventory/first", json={"price": 10, "qty": 1})
    r = client.post("/inventory/second", json={"price": 10, "qty": 1})
    assert r.status_code == 400
    assert "limit" in r.json()["detail"].lower()

def test_partial_delete_decreases_qty():
    client.post("/inventory/ak47", json={"price": 35.0, "qty": 5})
    r = client.delete("/inventory/ak47/2")
    assert r.status_code == 200
    assert r.json() == {"item": "ak47", "qty_left": 3}
    assert client.get("/inventory").json()["ak47"]["qty"] == 3

def test_partial_delete_exact_qty_removes_item():
    client.post("/inventory/ak47", json={"price": 35.0, "qty": 2})
    r = client.delete("/inventory/ak47/2")
    assert r.status_code == 200
    assert r.json() == {"item": "ak47", "qty_left": 0}
    assert "ak47" not in client.get("/inventory").json()

def test_partial_delete_more_than_available_400():
    client.post("/inventory/ak47", json={"price": 35.0, "qty": 2})
    r = client.delete("/inventory/ak47/5")
    assert r.status_code == 400
    assert "only 2" in r.json()["detail"]
    assert client.get("/inventory").json()["ak47"]["qty"] == 2

def test_partial_delete_unknown_404():
    r = client.delete("/inventory/unknown/1")
    assert r.status_code == 404

def test_partial_delete_qty_zero_422():
    client.post("/inventory/ak47", json={"price": 35.0, "qty": 2})
    r = client.delete("/inventory/ak47/0")
    assert r.status_code == 422

def test_partial_delete_bad_name_422():
    r = client.delete("/inventory/../evil/1")
    assert r.status_code in (404, 422)

def test_partial_delete_updates_total():
    client.post("/inventory/ak47", json={"price": 100.0, "qty": 5})
    client.delete("/inventory/ak47/3")
    r = client.get("/inventory/total")
    data = r.json()
    assert data["unique_items"] == 1
    assert data["total_items"] == 2
    assert data["subtotal"] == 200.0
    assert data["total"] == 230.0

def test_total_counts_unique_and_total():
    client.post("/inventory/ak47", json={"price": 10.0, "qty": 3})
    client.post("/inventory/awp", json={"price": 20.0, "qty": 2})
    r = client.get("/inventory/total")
    data = r.json()
    assert data["unique_items"] == 2
    assert data["total_items"] == 5
    assert data["subtotal"] == 10.0 * 3 + 20.0 * 2

def test_get_single_item():
    client.post("/inventory/ak47", json={"price": 35.0, "qty": 2})
    r = client.get("/inventory/ak47")
    assert r.status_code == 200
    assert r.json()["qty"] == 2

def test_get_single_item_404():
    r = client.get("/inventory/unknown")
    assert r.status_code == 404