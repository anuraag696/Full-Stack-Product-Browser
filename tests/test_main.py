import base64
import json
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException

from main import app, encode_cursor, decode_cursor


client = TestClient(app)


# --- Tests for encode_cursor ---

class TestEncodeCursor:
    def test_encode_cursor_basic(self):
        created_at = "2024-01-15T10:30:00"
        item_id = 42
        result = encode_cursor(created_at, item_id)
        decoded = json.loads(base64.b64decode(result))
        assert decoded == {"c": created_at, "i": item_id}

    def test_encode_cursor_large_id(self):
        created_at = "2024-06-01T00:00:00"
        item_id = 999999
        result = encode_cursor(created_at, item_id)
        decoded = json.loads(base64.b64decode(result))
        assert decoded["i"] == 999999

    def test_encode_cursor_returns_string(self):
        result = encode_cursor("2024-01-01T00:00:00", 1)
        assert isinstance(result, str)

    def test_encode_cursor_is_base64(self):
        result = encode_cursor("2024-01-01T00:00:00", 1)
        # Should not raise
        base64.b64decode(result)


# --- Tests for decode_cursor ---

class TestDecodeCursor:
    def test_decode_cursor_roundtrip(self):
        created_at = "2024-03-20T14:25:00"
        item_id = 100
        encoded = encode_cursor(created_at, item_id)
        decoded_created_at, decoded_id = decode_cursor(encoded)
        assert decoded_created_at == created_at
        assert decoded_id == item_id

    def test_decode_cursor_invalid_base64(self):
        with pytest.raises(HTTPException) as exc_info:
            decode_cursor("not-valid-base64!!!")
        assert exc_info.value.status_code == 400
        assert "Invalid cursor format" in exc_info.value.detail

    def test_decode_cursor_invalid_json(self):
        invalid = base64.b64encode(b"not json").decode()
        with pytest.raises(HTTPException) as exc_info:
            decode_cursor(invalid)
        assert exc_info.value.status_code == 400

    def test_decode_cursor_missing_keys(self):
        missing_keys = base64.b64encode(json.dumps({"x": 1}).encode()).decode()
        with pytest.raises(HTTPException) as exc_info:
            decode_cursor(missing_keys)
        assert exc_info.value.status_code == 400

    def test_decode_cursor_empty_string(self):
        with pytest.raises(HTTPException) as exc_info:
            decode_cursor("")
        assert exc_info.value.status_code == 400


# --- Tests for GET /api/products endpoint ---

def _make_mock_product(id, name="Test Product", category="Electronics",
                       price=29.99, created_at=None, updated_at=None):
    now = created_at or datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    return {
        "id": id,
        "name": name,
        "category": category,
        "price": price,
        "created_at": now,
        "updated_at": updated_at or now,
    }


class TestGetProductsEndpoint:
    @patch("main.get_db_connection")
    def test_get_products_success(self, mock_get_conn):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        products = [_make_mock_product(i) for i in range(5)]
        mock_cursor.fetchall.return_value = products

        response = client.get("/api/products?limit=20")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5
        assert data["has_more"] is False
        assert data["next_cursor"] is None

    @patch("main.get_db_connection")
    def test_get_products_with_pagination(self, mock_get_conn):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Return limit+1 items to indicate more data
        products = [_make_mock_product(i) for i in range(21)]
        mock_cursor.fetchall.return_value = products

        response = client.get("/api/products?limit=20")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 20
        assert data["has_more"] is True
        assert data["next_cursor"] is not None

    @patch("main.get_db_connection")
    def test_get_products_with_category_filter(self, mock_get_conn):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        products = [_make_mock_product(1, category="Books")]
        mock_cursor.fetchall.return_value = products

        response = client.get("/api/products?category=Books")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["category"] == "Books"

        # Verify the SQL query included category filter
        executed_query = mock_cursor.execute.call_args[0][0]
        assert "category = %s" in executed_query

    @patch("main.get_db_connection")
    def test_get_products_with_cursor(self, mock_get_conn):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        cursor_val = encode_cursor("2024-01-01T00:00:00", 50)
        response = client.get(f"/api/products?cursor={cursor_val}")
        assert response.status_code == 200

        # Verify cursor pagination was applied in the query
        executed_query = mock_cursor.execute.call_args[0][0]
        assert "created_at < %s" in executed_query

    @patch("main.get_db_connection")
    def test_get_products_invalid_cursor(self, mock_get_conn):
        response = client.get("/api/products?cursor=invalid!!!")
        assert response.status_code == 400

    @patch("main.get_db_connection")
    def test_get_products_db_connection_error(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("Connection refused")

        response = client.get("/api/products")
        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]

    @patch("main.get_db_connection")
    def test_get_products_query_error(self, mock_get_conn):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Query timeout")

        response = client.get("/api/products")
        assert response.status_code == 500
        assert "Query failed" in response.json()["detail"]

    @patch("main.get_db_connection")
    def test_get_products_limit_max(self, mock_get_conn):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        response = client.get("/api/products?limit=100")
        assert response.status_code == 200

    def test_get_products_limit_exceeds_max(self):
        response = client.get("/api/products?limit=101")
        assert response.status_code == 422  # Validation error

    @patch("main.get_db_connection")
    def test_get_products_empty_result(self, mock_get_conn):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        response = client.get("/api/products")
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["has_more"] is False
        assert data["next_cursor"] is None

    @patch("main.get_db_connection")
    def test_get_products_category_and_cursor_combined(self, mock_get_conn):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        cursor_val = encode_cursor("2024-01-01T00:00:00", 10)
        response = client.get(f"/api/products?category=Sports&cursor={cursor_val}")
        assert response.status_code == 200

        executed_query = mock_cursor.execute.call_args[0][0]
        assert "category = %s" in executed_query
        assert "created_at < %s" in executed_query

    @patch("main.get_db_connection")
    def test_get_products_connection_closed_after_success(self, mock_get_conn):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        client.get("/api/products")
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("main.get_db_connection")
    def test_get_products_connection_closed_after_error(self, mock_get_conn):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("fail")

        client.get("/api/products")
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
