import re
from typing import Any

from src.api_client import HeadHunterAPI
from src.file_manager import JSONSaver
from src.vacancy import Vacancy


def format_salary(salary: Any) -> str:
    """
    Форматирует зарплату из JSON HH.ru.

    """
    if isinstance(salary, dict):
        salary_from = salary.get("from") or "Не указано"
        salary_to = salary.get("to") or "Не указано"
        currency = salary.get("currency", "")
        return f"{salary_from} - {salary_to} {currency}".strip()
    return "Зарплата не указана"


def clean_description(description: Any) -> str:
    """
    Удаляет HTML-теги и возвращает понятное сообщение, если описание отсутствует.

    """
    if not description:
        return "Описание отсутствует"
    return re.sub(r"<.*?>", "", description)


def main() -> None:
    """
    Основная функция для взаимодействия с пользователем.
    """
    print("Добро пожаловать в поиск вакансий на HH.ru!")

    hh_api = HeadHunterAPI()
    json_saver = JSONSaver()

    if not hh_api.access_token:
        auth_code = input("Введите authorization_code: ")
        hh_api.authenticate(auth_code)
    else:
        print("[LOG]: Используется сохранённый access_token, ввод authorization_code не требуется.")

    while True:
        print("\nВыберите действие:")
        print("1. Поиск вакансий")
        print("2. Сохранить вакансию")
        print("3. Удалить вакансию")
        print("4. Показать сохраненные вакансии")
        print("5. Выход")

        choice = input("Введите номер действия: ")

        if choice == "1":
            query = input("Введите поисковый запрос: ")
            vacancies = hh_api.get_data(query)

            if vacancies:
                print("\nНайденные вакансии:")
                for v in vacancies[:5]:
                    salary = format_salary(v.get("salary"))
                    description = clean_description(v["snippet"].get("responsibility", ""))
                    vac = Vacancy(
                        title=v["name"],
                        url=v["alternate_url"],
                        salary=salary,
                        description=description,
                    )
                    print(vac)

        elif choice == "2":
            title = input("Введите название вакансии: ")
            url = input("Введите ссылку на вакансию: ")
            salary = input("Введите зарплату: ")
            description = input("Введите описание вакансии: ")
            vacancy = Vacancy(title, url, salary, description)
            json_saver.add_vacancy(vacancy)

        elif choice == "3":
            title = input("Введите название вакансии для удаления: ")
            json_saver.delete_vacancy(title)

        elif choice == "4":
            data = json_saver.load_data()
            print("\nСохраненные вакансии:")
            for item in data:
                print(item)

        elif choice == "5":
            print("Выход из программы.")
            break

        else:
            print("Неверный ввод. Попробуйте снова.")


if __name__ == "__main__":
    main()
