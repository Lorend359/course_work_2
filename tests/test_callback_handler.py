import pytest

from src.callback_handler import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_callback_with_code(client):
    """
    Проверяет, что при наличии параметра code
    обработчик возвращает статус 200 и соответствующий ответ.
    """
    response = client.get("/callback?code=abc123")
    assert response.status_code == 200
    assert "abc123" in response.get_data(as_text=True)


def test_callback_without_code(client):
    """
    Проверяет, что при отсутствии параметра code
    обработчик возвращает статус 400 и соответствующий ответ.
    """
    response = client.get("/callback")
    assert response.status_code == 400
    assert "not found" in response.get_data(as_text=True).lower()
