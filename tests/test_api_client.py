import json
import os
from pathlib import Path
from typing import Any, Dict

import requests

from src.api_client import HeadHunterAPI


class FakeResponse:
    """Фейковый ответ для имитации HTTP-ответа."""

    def __init__(self, status_code: int, json_data: Any) -> None:
        self.status_code = status_code
        self._json_data = json_data
        self.text = json.dumps(json_data)

    def json(self) -> Any:
        """Возвращает JSON-данные."""
        return self._json_data


def fake_post_success_auth(url: str, data: Dict[str, Any], **kwargs: Any) -> FakeResponse:
    """Возвращает успешный ответ для аутентификации."""
    if data.get("grant_type") == "authorization_code":
        return FakeResponse(200, {"access_token": "test_access", "refresh_token": "test_refresh"})
    elif data.get("grant_type") == "refresh_token":
        return FakeResponse(200, {"access_token": "refreshed_access", "refresh_token": "refreshed_refresh"})
    return FakeResponse(400, {"error": "invalid_grant"})


def fake_post_error(url: str, data: Dict[str, Any], **kwargs: Any) -> FakeResponse:
    """Возвращает ошибочный ответ для POST-запроса."""
    return FakeResponse(400, {"error": "invalid_grant"})


def fake_post_exception(url: str, data: Dict[str, Any], **kwargs: Any) -> None:
    """Выбрасывает исключение при POST-запросе."""
    raise requests.exceptions.RequestException("Test exception")


def fake_get_success(url: str, headers: Dict[str, str], params: Dict[str, str], **kwargs: Any) -> FakeResponse:
    """Возвращает успешный ответ для GET-запроса."""
    fake_items = [
        {"name": "Vacancy A", "snippet": {"responsibility": "Test description"}, "alternate_url": "http://example.com"}
    ]
    return FakeResponse(200, {"items": fake_items, "found": len(fake_items)})


def fake_get_invalid_json(url: str, headers: Dict[str, str], params: Dict[str, str], **kwargs: Any) -> Any:
    """Имитация ответа с некорректным JSON."""

    class FakeResponseInvalid:
        status_code = 200
        text = "Not JSON"

        def json(self) -> Any:
            raise json.JSONDecodeError("msg", "doc", 0)

    return FakeResponseInvalid()


def fake_get_error(url: str, headers: Dict[str, str], params: Dict[str, str], **kwargs: Any) -> FakeResponse:
    """Возвращает ответ с ошибочным статусом."""
    return FakeResponse(500, {})


def fake_get_401(url: str, headers: Dict[str, str], params: Dict[str, str], **kwargs: Any) -> FakeResponse:
    """Возвращает ответ с кодом 401."""
    return FakeResponse(401, {})


def fake_get_401_then_success(
    url: str, headers: Dict[str, str], params: Dict[str, str], **kwargs: Any
) -> FakeResponse:
    """Первый вызов возвращает 401, затем успешный ответ."""
    if not hasattr(fake_get_401_then_success, "called"):
        fake_get_401_then_success.called = True
        return FakeResponse(401, {})
    else:
        return fake_get_success(url, headers, params, **kwargs)


def test_authenticate_existing_token(monkeypatch):
    """Проверяет, что если токен уже установлен, он не изменяется."""
    api = HeadHunterAPI()
    api._access_token = "existing_token"
    monkeypatch.setattr(requests, "post", fake_post_success_auth)
    api.authenticate("any_code")
    assert api.access_token == "existing_token"


def test_authenticate_with_refresh(monkeypatch):
    """Проверяет использование refresh-токена при отсутствии access_token."""
    api = HeadHunterAPI()
    api._access_token = None
    api._refresh_token = "existing_refresh"
    monkeypatch.setattr(requests, "post", fake_post_success_auth)
    api.authenticate("ignored_code")
    assert api.access_token == "refreshed_access"


def test_authenticate_missing_auth_code(monkeypatch):
    """Проверяет, что при отсутствии auth_code токен не устанавливается."""
    api = HeadHunterAPI()
    api._access_token = None
    api._refresh_token = None
    api.authenticate(None)
    assert api.access_token is None


def test_authenticate_success(monkeypatch, tmp_path: Path):
    """Проверяет успешную аутентификацию и сохранение токена в файл."""
    token_file = tmp_path / "token.json"
    monkeypatch.setattr(HeadHunterAPI, "_load_token", lambda self: (None, None))

    def fake_save_token(self) -> None:
        with open(str(token_file), "w") as f:
            json.dump({"access_token": self._access_token, "refresh_token": self._refresh_token}, f)

    monkeypatch.setattr(HeadHunterAPI, "_save_token", fake_save_token)
    monkeypatch.setattr(requests, "post", fake_post_success_auth)
    api = HeadHunterAPI()
    api.TOKEN_FILE = str(token_file)
    api.authenticate("valid_code")
    assert api.access_token == "test_access"
    with open(str(token_file), "r") as f:
        data = json.load(f)
    assert data["access_token"] == "test_access"
    assert data["refresh_token"] == "test_refresh"


def test_authenticate_post_exception(monkeypatch):
    """Проверяет, что при исключении в POST-запросе токен не устанавливается."""
    monkeypatch.setattr(HeadHunterAPI, "_load_token", lambda self: (None, None))
    monkeypatch.setattr(requests, "post", fake_post_exception)
    api = HeadHunterAPI()
    api.authenticate("valid_code")
    assert api.access_token is None


def test_authenticate_error_response(monkeypatch):
    """Проверяет, что при ошибочном ответе токен не устанавливается."""
    monkeypatch.setattr(HeadHunterAPI, "_load_token", lambda self: (None, None))
    monkeypatch.setattr(requests, "post", fake_post_error)
    api = HeadHunterAPI()
    api.authenticate("valid_code")
    assert api.access_token is None


def test_get_data_success(monkeypatch):
    """Проверяет, что get_data возвращает список вакансий при успешном ответе."""
    api = HeadHunterAPI()
    api._access_token = "dummy_token"
    monkeypatch.setattr(requests, "get", fake_get_success)
    vacancies = api.get_data("test query")
    assert isinstance(vacancies, list)
    assert len(vacancies) == 1
    assert vacancies[0]["name"] == "Vacancy A"


def test_get_data_exception(monkeypatch):
    """Проверяет, что get_data возвращает пустой список при исключении."""
    api = HeadHunterAPI()
    api._access_token = "dummy_token"

    def fake_get_exception(url, headers, params, **kwargs):
        raise requests.exceptions.RequestException("Test exception")

    monkeypatch.setattr(requests, "get", fake_get_exception)
    vacancies = api.get_data("test query")
    assert vacancies == []


def test_get_data_invalid_json(monkeypatch):
    """Проверяет, что get_data возвращает пустой список при ошибке декодирования JSON."""
    api = HeadHunterAPI()
    api._access_token = "dummy_token"
    monkeypatch.setattr(requests, "get", fake_get_invalid_json)
    vacancies = api.get_data("test query")
    assert vacancies == []


def test_get_data_status_error(monkeypatch):
    """Проверяет, что get_data возвращает пустой список при ошибочном статусе ответа."""
    api = HeadHunterAPI()
    api._access_token = "dummy_token"
    monkeypatch.setattr(requests, "get", fake_get_error)
    vacancies = api.get_data("test query")
    assert vacancies == []


def test_get_data_401_then_success(monkeypatch):
    """Проверяет сценарий: 401 → обновление токена → успешный ответ."""
    api = HeadHunterAPI()
    api._access_token = "dummy_token"
    if hasattr(fake_get_401_then_success, "called"):
        del fake_get_401_then_success.called
    monkeypatch.setattr(requests, "get", fake_get_401_then_success)

    def fake_refresh(self) -> bool:
        self._access_token = "refreshed_token"
        return True

    monkeypatch.setattr(HeadHunterAPI, "_refresh_access_token", fake_refresh)
    vacancies = api.get_data("test query")
    assert vacancies != []
    assert api.access_token == "refreshed_token"


def test_load_token_valid(tmp_path: Path, monkeypatch) -> None:
    """Проверяет, что _load_token возвращает корректные токены из файла."""
    token_file = tmp_path / "valid_token.json"
    token_data = {"access_token": "valid_access", "refresh_token": "valid_refresh"}
    token_file.write_text(json.dumps(token_data))
    original_exists = os.path.exists
    monkeypatch.setattr(os.path, "exists", lambda path: path == str(token_file) or original_exists(path))
    api = HeadHunterAPI()
    api.TOKEN_FILE = str(token_file)
    tokens = api._load_token()
    assert tokens == ("valid_access", "valid_refresh")


def test_load_token_invalid(tmp_path: Path, monkeypatch) -> None:
    """Проверяет, что _load_token возвращает (None, None) при некорректном файле."""
    token_file = tmp_path / "invalid_token.json"
    token_file.write_text("invalid json")
    original_exists = os.path.exists
    monkeypatch.setattr(os.path, "exists", lambda path: path == str(token_file) or original_exists(path))
    api = HeadHunterAPI()
    api.TOKEN_FILE = str(token_file)
    tokens = api._load_token()
    assert tokens == (None, None)


def test_load_token_not_exist(monkeypatch) -> None:
    """Проверяет, что _load_token возвращает (None, None), если файл не существует."""
    monkeypatch.setattr(os.path, "exists", lambda path: False)
    api = HeadHunterAPI()
    api.TOKEN_FILE = "nonexistent.json"
    tokens = api._load_token()
    assert tokens == (None, None)


def test_save_token(tmp_path: Path):
    """Проверяет, что _save_token корректно записывает токены в файл."""
    token_file = tmp_path / "save_token.json"
    api = HeadHunterAPI()
    api.TOKEN_FILE = str(token_file)
    api._access_token = "save_access"
    api._refresh_token = "save_refresh"
    api._save_token()
    with open(str(token_file), "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["access_token"] == "save_access"
    assert data["refresh_token"] == "save_refresh"
