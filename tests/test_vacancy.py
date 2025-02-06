from src.vacancy import Vacancy


def test_validate_salary_non_empty():
    """
    Если зарплата не пустая, метод _validate_salary должен возвращать её без изменений.
    """
    result = Vacancy._validate_salary("50000 - 60000 RUR")
    assert result == "50000 - 60000 RUR"


def test_validate_salary_empty():
    """
    Если передана пустая строка, метод _validate_salary должен вернуть 'Зарплата не указана'.
    """
    result = Vacancy._validate_salary("")
    assert result == "Зарплата не указана"


def test_parse_salary_with_digits():
    """
    Метод _parse_salary должен корректно извлекать число из строки.
    """
    result = Vacancy._parse_salary("40000 - 60000 RUR")
    assert result == 40000

    result = Vacancy._parse_salary("75000")
    assert result == 75000


def test_parse_salary_no_digits():
    """
    Если в строке нет цифр, _parse_salary должен вернуть 0.
    """
    result = Vacancy._parse_salary("Не указана")
    assert result == 0


def test_str_method():
    """
    Метод __str__ должен возвращать строку, содержащую название, зарплату, URL и описание вакансии.
    """
    vac = Vacancy("Developer", "http://example.com", "50000 RUR", "Develop awesome apps")
    output = str(vac)
    assert "Developer" in output
    assert "50000 RUR" in output
    assert "http://example.com" in output
    assert "Develop awesome apps" in output


def test_vacancy_comparison():
    """
    Сравнение вакансий должно основываться на числовом значении зарплаты.
    """
    vac_low = Vacancy("Junior Dev", "http://example.com/junior", "30000 RUR", "Entry level")
    vac_high = Vacancy("Senior Dev", "http://example.com/senior", "80000 RUR", "Experienced")

    assert vac_low < vac_high
    assert vac_high > vac_low


def test_vacancy_comparison_with_non_numeric():
    """
    Если зарплата не содержит цифр, считается, что её числовое значение равно 0.
    """
    vac1 = Vacancy("Vacancy 1", "http://example.com/1", "Не указана", "Desc 1")
    vac2 = Vacancy("Vacancy 2", "http://example.com/2", "50000 RUR", "Desc 2")
    assert vac1 < vac2
