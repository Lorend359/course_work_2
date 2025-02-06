import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, cast

import requests
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIClient(ABC):
    @abstractmethod
    def authenticate(self, auth_code: Optional[str]) -> None:
        """
        Аутентифицируется в API с использованием authorization_code.
        """
        pass

    @abstractmethod
    def get_data(self, query: str, retries: int = 1) -> List[Dict[str, Any]]:
        """
        Получает данные вакансий по заданному запросу.
        """
        pass


class HeadHunterAPI(APIClient):
    BASE_URL: str = "https://api.hh.ru/"
    TOKEN_URL: str = "https://hh.ru/oauth/token"
    AUTH_URL: str = "https://hh.ru/oauth/authorize"
    TOKEN_FILE: str = ".token"

    def __init__(self) -> None:
        self._client_id: Optional[str] = os.getenv("HH_CLIENT_ID")
        self._client_secret: Optional[str] = os.getenv("HH_CLIENT_SECRET")
        self._redirect_uri: Optional[str] = os.getenv("HH_REDIRECT_URI")
        self._access_token, self._refresh_token = self._load_token()

    @property
    def access_token(self) -> Optional[str]:
        return self._access_token

    def authenticate(self, auth_code: Optional[str] = None) -> None:
        """
        Использует сохранённый токен или получает новый через authorization_code.
        """
        if self._access_token:
            logger.info("Используется сохранённый access_token.")
            return

        if self._refresh_token:
            logger.info("Попытка обновления токена через refresh_token...")
            if self._refresh_access_token():
                logger.info("Токен успешно обновлён через refresh_token!")
                return

        if not auth_code:
            logger.error("Требуется authorization_code для получения нового токена.")
            return

        logger.info("Выполняем аутентификацию через authorization_code...")
        data = {
            "grant_type": "authorization_code",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "code": auth_code,
            "redirect_uri": self._redirect_uri,
        }
        try:
            response = requests.post(self.TOKEN_URL, data=data)
        except requests.exceptions.RequestException as e:
            logger.error("Ошибка при выполнении запроса авторизации: %s", e)
            return

        if response.status_code == 200:
            tokens = response.json()
            self._access_token = tokens.get("access_token")
            self._refresh_token = tokens.get("refresh_token")
            self._save_token()
            logger.info("Успешная авторизация! Токен сохранён.")
        else:
            logger.error("Ошибка авторизации: %s", response.text)

    def _refresh_access_token(self) -> bool:
        """
        Обновляет access_token с помощью refresh_token.
        """
        if not self._refresh_token:
            logger.error("Нет refresh_token. Требуется повторная авторизация.")
            return False

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        try:
            response = requests.post(self.TOKEN_URL, data=data)
        except requests.exceptions.RequestException as e:
            logger.error("Ошибка при запросе обновления токена: %s", e)
            return False

        if response.status_code == 200:
            tokens = response.json()
            self._access_token = tokens.get("access_token")
            self._refresh_token = tokens.get("refresh_token")
            self._save_token()
            logger.info("Токен успешно обновлён!")
            return True
        else:
            logger.error("Ошибка обновления токена: %s", response.text)
            return False

    def _save_token(self) -> None:
        """Сохраняет access_token и refresh_token в файл."""
        try:
            with open(self.TOKEN_FILE, "w") as file:
                json.dump({"access_token": self._access_token, "refresh_token": self._refresh_token}, file)
        except Exception as e:
            logger.error("Ошибка при сохранении токена: %s", e)

    def _load_token(self) -> Tuple[Optional[str], Optional[str]]:
        """Загружает access_token и refresh_token из файла, если они есть."""
        if os.path.exists(self.TOKEN_FILE):
            try:
                with open(self.TOKEN_FILE, "r") as file:
                    data = json.load(file)
            except json.JSONDecodeError:
                logger.error("Файл токена повреждён. Требуется повторная авторизация.")
                return None, None

            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")
            if access_token:
                logger.debug("Загружен access_token: %s...", access_token[:10])
            else:
                logger.debug("access_token не найден!")
            if refresh_token:
                logger.debug("Загружен refresh_token: %s...", refresh_token[:10])
            else:
                logger.debug("refresh_token не найден!")
            return access_token, refresh_token

        logger.debug("Файл .token не найден.")
        return None, None

    def get_data(self, query: str, retries: int = 1) -> List[Dict[str, Any]]:
        """
        Запрашивает вакансии с использованием access_token по ключевому слову.
        """
        if not self._access_token:
            logger.error("Нет access_token. Попытка обновления...")
            if not self._refresh_access_token():
                logger.error("Токен не обновлён. Требуется авторизация.")
                return []

        headers = {"Authorization": f"Bearer {self._access_token}"}
        params: Dict[str, str] = {"text": query, "page": str(0), "per_page": str(20)}

        try:
            response = requests.get(self.BASE_URL + "vacancies", headers=headers, params=params)
        except requests.exceptions.RequestException as e:
            logger.error("Ошибка при выполнении запроса: %s", e)
            return []

        if response.status_code == 401 and retries > 0:
            logger.info("Access token истёк. Попытка обновления...")
            if self._refresh_access_token():
                return self.get_data(query, retries=retries - 1)
        elif response.status_code != 200:
            logger.error("Ошибка при получении данных: %s", response.status_code)
            return []

        try:
            data: Dict[str, Any] = cast(Dict[str, Any], response.json())
        except json.JSONDecodeError as e:
            logger.error("Ошибка декодирования ответа: %s", e)
            return []

        vacancies: List[Dict[str, Any]] = cast(List[Dict[str, Any]], data.get("items", []))
        logger.info("Получено %d вакансий по запросу '%s'.", len(vacancies), query)
        return vacancies
