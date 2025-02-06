import re


class Vacancy:
    """
    Класс для представления вакансии.
    """

    __slots__ = ("title", "url", "salary", "description")

    def __init__(self, title: str, url: str, salary: str, description: str) -> None:
        """
        Инициализация экземпляра вакансии.
        """
        self.title: str = title
        self.url: str = url
        self.salary: str = self._validate_salary(salary)
        self.description: str = description

    @staticmethod
    def _validate_salary(salary: str) -> str:
        """
        Приватный метод валидации зарплаты.
        Возвращает исходную зарплату или 'Зарплата не указана', если значение пустое.
        """
        return salary if salary else "Зарплата не указана"

    def __str__(self) -> str:
        return f"{self.title} ({self.salary})\n{self.url}\nОписание: {self.description}"

    def __lt__(self, other: "Vacancy") -> bool:
        return self._parse_salary(self.salary) < self._parse_salary(other.salary)

    def __gt__(self, other: "Vacancy") -> bool:
        return self._parse_salary(self.salary) > self._parse_salary(other.salary)

    @staticmethod
    def _parse_salary(salary: str) -> int:
        """
        Приватный метод для извлечения числового значения зарплаты.
        Если цифры не найдены, возвращает 0.
        """
        match = re.search(r"\d+", salary)
        return int(match.group()) if match else 0
