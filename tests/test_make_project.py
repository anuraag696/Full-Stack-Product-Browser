import os
import shutil
from unittest.mock import patch

import pytest


class TestMakeProject:
    def setup_method(self):
        """Clean up any leftover test directories."""
        self.output_dir = "product-browser"
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def teardown_method(self):
        """Clean up created directories after tests."""
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_creates_directory(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        import importlib
        import make_project
        importlib.reload(make_project)

        assert os.path.isdir(tmp_path / "product-browser")

    def test_creates_requirements_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        import importlib
        import make_project
        importlib.reload(make_project)

        req_path = tmp_path / "product-browser" / "requirements.txt"
        assert req_path.exists()
        content = req_path.read_text()
        assert "fastapi" in content
        assert "uvicorn" in content
        assert "psycopg2-binary" in content
        assert "pydantic" in content
        assert "python-dotenv" in content

    def test_creates_env_example_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        import importlib
        import make_project
        importlib.reload(make_project)

        env_path = tmp_path / "product-browser" / ".env.example"
        assert env_path.exists()
        content = env_path.read_text()
        assert "DATABASE_URL" in content

    def test_creates_env_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        import importlib
        import make_project
        importlib.reload(make_project)

        env_path = tmp_path / "product-browser" / ".env"
        assert env_path.exists()
        content = env_path.read_text()
        assert "DATABASE_URL" in content

    def test_idempotent_execution(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        import importlib
        import make_project
        importlib.reload(make_project)
        # Run again - should not raise
        importlib.reload(make_project)
        assert os.path.isdir(tmp_path / "product-browser")
