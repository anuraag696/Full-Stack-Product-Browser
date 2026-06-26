from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest

from seed import generate_mock_products, CATEGORIES, PRODUCT_NAMES


class TestGenerateMockProducts:
    def test_generates_correct_count(self):
        products = generate_mock_products(100)
        assert len(products) == 100

    def test_generates_default_count(self):
        products = generate_mock_products()
        assert len(products) == 200000

    def test_product_tuple_structure(self):
        products = generate_mock_products(1)
        product = products[0]
        assert len(product) == 5
        name, category, price, created_at, updated_at = product
        assert isinstance(name, str)
        assert isinstance(category, str)
        assert isinstance(price, float)
        assert isinstance(created_at, datetime)
        assert isinstance(updated_at, datetime)

    def test_categories_are_valid(self):
        products = generate_mock_products(500)
        for product in products:
            assert product[1] in CATEGORIES

    def test_product_names_contain_base_names(self):
        products = generate_mock_products(100)
        for product in products:
            name = product[0]
            base_name = name.rsplit(" ", 1)[0]
            assert base_name in PRODUCT_NAMES

    def test_product_names_have_numeric_suffix(self):
        products = generate_mock_products(50)
        for product in products:
            name = product[0]
            suffix = name.rsplit(" ", 1)[1]
            num = int(suffix)
            assert 100 <= num <= 999

    def test_prices_in_valid_range(self):
        products = generate_mock_products(500)
        for product in products:
            price = product[2]
            assert 9.99 <= price <= 1499.99
            # Check price has at most 2 decimal places
            assert round(price, 2) == price

    def test_timestamps_are_decreasing(self):
        products = generate_mock_products(10)
        for i in range(1, len(products)):
            assert products[i][3] < products[i - 1][3]

    def test_created_at_equals_updated_at(self):
        products = generate_mock_products(20)
        for product in products:
            assert product[3] == product[4]

    def test_timestamps_spaced_5_seconds_apart(self):
        products = generate_mock_products(5)
        for i in range(1, len(products)):
            diff = products[i - 1][3] - products[i][3]
            assert diff == timedelta(seconds=5)

    def test_zero_count(self):
        products = generate_mock_products(0)
        assert products == []


class TestSeedDatabase:
    @patch("seed.psycopg2.connect")
    def test_seed_database_calls_connect(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        from seed import seed_database
        seed_database()

        mock_connect.assert_called_once()
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    @patch("seed.psycopg2.connect")
    def test_seed_database_handles_error(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("DB error")

        from seed import seed_database
        seed_database()

        mock_conn.rollback.assert_called_once()

    @patch("seed.psycopg2.connect")
    def test_seed_database_closes_resources(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        from seed import seed_database
        seed_database()

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
