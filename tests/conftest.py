"""Preparación compartida por las pruebas: cada prueba usa una base nueva y temporal."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from db import get_db  # noqa: E402


@pytest.fixture
def app(tmp_path):
    os.environ["GEMINI_MOCK"] = "true"  # las pruebas nunca llaman a Gemini de verdad
    # CSRF se desactiva en las pruebas para no repetir el código secreto en cada formulario;
    # test_seguridad.py lo prueba activado.
    return create_app({"TESTING": True, "CSRF": False, "DATABASE": str(tmp_path / "prueba.db")})


@pytest.fixture
def cliente(app):
    return app.test_client()


@pytest.fixture
def con(app):
    with app.app_context():
        yield get_db()
