import json
from pathlib import Path

import pytest

from src.file_manager import JSONSaver
from src.vacancy import Vacancy


@pytest.fixture
def temp_json_file(tmp_path: Path) -> str:
    """
    Фикстура, создающая временный JSON-файл для вакансий,
    инициализированный пустым списком.
    """
    file_path = tmp_path / "vacancies.json"
    file_path.write_text("[]")
    return str(file_path)


def test_add_vacancy(temp_json_file: str) -> None:
    """
    Проверяет, что после добавления вакансии она появляется в файле.
    """
    saver = JSONSaver(file_path=temp_json_file)
    vac = Vacancy("Test Vacancy", "http://example.com", "50000 RUR", "Test description")
    saver.add_vacancy(vac)
    with open(temp_json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert any(item.get("title") == "Test Vacancy" for item in data)


def test_no_duplicate_vacancy(temp_json_file: str) -> None:
    """
    Проверяет, что повторное добавление одной и той же вакансии не приводит к дублированию.
    """
    saver = JSONSaver(file_path=temp_json_file)
    vac = Vacancy("Unique Vacancy", "http://example.com", "60000 RUR", "Unique description")
    saver.add_vacancy(vac)
    saver.add_vacancy(vac)
    with open(temp_json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    count = sum(1 for item in data if item.get("title") == "Unique Vacancy")
    assert count == 1


def test_delete_vacancy(temp_json_file: str) -> None:
    """
    Проверяет, что после удаления вакансии по названию
    эта вакансия исчезает из файла, а остальные остаются.
    """
    saver = JSONSaver(file_path=temp_json_file)
    vac1 = Vacancy("Vacancy 1", "http://example.com/1", "70000 RUR", "Desc 1")
    vac2 = Vacancy("Vacancy 2", "http://example.com/2", "80000 RUR", "Desc 2")
    saver.add_vacancy(vac1)
    saver.add_vacancy(vac2)
    saver.delete_vacancy("Vacancy 1")
    with open(temp_json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert not any(item.get("title") == "Vacancy 1" for item in data)
    assert any(item.get("title") == "Vacancy 2" for item in data)


def test_load_data_nonexistent(tmp_path: Path) -> None:
    """
    Проверяет, что если файла с вакансиями не существует,
    метод load_data возвращает пустой список.
    """
    fake_file = tmp_path / "nonexistent.json"
    saver = JSONSaver(file_path=str(fake_file))
    data = saver.load_data()
    assert data == []
