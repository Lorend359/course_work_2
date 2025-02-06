import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from src.vacancy import Vacancy


class VacancySaver(ABC):
    """
    Абстрактный класс для работы с файлами вакансий.
    """

    @abstractmethod
    def add_vacancy(self, vacancy: Vacancy) -> None:
        """
        Добавить вакансию в файл.
        """
        pass

    @abstractmethod
    def load_data(self) -> List[Dict[str, Any]]:
        """
        Загрузить данные вакансий из файла.
        """
        pass

    @abstractmethod
    def delete_vacancy(self, title: str) -> None:
        """
        Удалить вакансию по названию.
        """
        pass


class JSONSaver(VacancySaver):
    """
    Класс для сохранения и загрузки данных вакансий в формате JSON.
    """

    def __init__(self, file_path: str = "data/vacancies.json") -> None:
        self._file_path: str = file_path

    def add_vacancy(self, vacancy: Vacancy) -> None:
        """
        Добавляет вакансию в JSON-файл, если её там ещё нет.
        """
        try:
            data = self.load_data()
            # Формируем словарь вручную, так как __dict__ недоступен для классов с __slots__
            vacancy_dict = {
                "title": vacancy.title,
                "url": vacancy.url,
                "salary": vacancy.salary,
                "description": vacancy.description,
            }
            if vacancy_dict not in data:
                data.append(vacancy_dict)
                with open(self._file_path, "w", encoding="utf-8") as file:
                    json.dump(data, file, ensure_ascii=False, indent=4)
                print(f"Вакансия '{vacancy.title}' добавлена.")
        except Exception as e:
            print(f"Ошибка при добавлении вакансии: {e}")

    def load_data(self) -> List[dict]:
        """
        Загружает данные из JSON-файла и возвращает их в виде списка словарей.
        """
        try:
            with open(self._file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, list):
                    return data
                else:
                    return []
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            return []

    def delete_vacancy(self, title: str) -> None:
        """
        Удаляет вакансию с указанным названием из JSON-файла.
        """
        try:
            data = self.load_data()
            updated_data = [vac for vac in data if vac.get("title") != title]
            with open(self._file_path, "w", encoding="utf-8") as file:
                json.dump(updated_data, file, ensure_ascii=False, indent=4)
            print(f"Вакансия '{title}' удалена.")
        except Exception as e:
            print(f"Ошибка при удалении вакансии: {e}")
