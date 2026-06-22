"""
День 2: массовый парсинг вакансий по нефтянке и финансам, сохранение в SQLite.
Источник: открытый API trudvsem.ru (госпортал "Работа России")
"""

import requests
import sqlite3
import json
import time

API_URL = "http://opendata.trudvsem.ru/api/v1/vacancies"
DB_PATH = "data/vacancies.db"

SEARCH_QUERIES = [
    "оператор добычи нефти и газа",
    "инженер нефтегазового оборудования",
    "буровой мастер",
    "геолог нефтегазовой",
    "технолог нефтепереработки",
    "инженер по бурению",
    "финансовый аналитик",
    "бухгалтер",
    "экономист",
    "кредитный специалист банка",
]

LIMIT_PER_PAGE = 100
TARGET_TOTAL = 500


def create_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vacancies (
            id TEXT PRIMARY KEY,
            job_name TEXT,
            company TEXT,
            region TEXT,
            salary_min INTEGER,
            salary_max INTEGER,
            experience INTEGER,
            education TEXT,
            specialisation TEXT,
            employment TEXT,
            schedule TEXT,
            skills TEXT,
            creation_date TEXT,
            vac_url TEXT,
            search_query TEXT
        )
    """)
    conn.commit()
    conn.close()
    print(f"✓ База данных готова: {DB_PATH}")


def fetch_vacancies(query, limit=100, offset=0):
    params = {
        "text": query,
        "limit": limit,
        "offset": offset,
    }
    try:
        response = requests.get(API_URL, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get("results", {}).get("vacancies", [])
        else:
            print(f"  ⚠ Ошибка {response.status_code} для запроса '{query}'")
            return []
    except requests.exceptions.RequestException as e:
        print(f"  ⚠ Сетевая ошибка: {e}")
        return []


def parse_vacancy(item, search_query):
    v = item.get("vacancy", {})

    skills_list = v.get("skills", [])
    skills_text = ", ".join(set(skills_list)) if skills_list else ""

    return {
        "id": v.get("id"),
        "job_name": v.get("job-name", ""),
        "company": v.get("company", {}).get("name", ""),
        "region": v.get("region", {}).get("name", ""),
        "salary_min": v.get("salary_min"),
        "salary_max": v.get("salary_max"),
        "experience": v.get("requirement", {}).get("experience"),
        "education": v.get("requirement", {}).get("education", ""),
        "specialisation": v.get("category", {}).get("specialisation", ""),
        "employment": v.get("employment", ""),
        "schedule": v.get("schedule", ""),
        "skills": skills_text,
        "creation_date": v.get("creation-date", ""),
        "vac_url": v.get("vac_url", ""),
        "search_query": search_query,
    }


def save_vacancy(conn, vacancy):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO vacancies
        (id, job_name, company, region, salary_min, salary_max,
         experience, education, specialisation, employment, schedule,
         skills, creation_date, vac_url, search_query)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        vacancy["id"], vacancy["job_name"], vacancy["company"], vacancy["region"],
        vacancy["salary_min"], vacancy["salary_max"], vacancy["experience"],
        vacancy["education"], vacancy["specialisation"], vacancy["employment"],
        vacancy["schedule"], vacancy["skills"], vacancy["creation_date"],
        vacancy["vac_url"], vacancy["search_query"]
    ))
    conn.commit()


def main():
    create_database()
    conn = sqlite3.connect(DB_PATH)

    total_saved = 0

    for query in SEARCH_QUERIES:
        if total_saved >= TARGET_TOTAL:
            break

        print(f"\n→ Поиск: '{query}'")
        offset = 0
        query_saved = 0

        for page in range(2):
            vacancies = fetch_vacancies(query, limit=LIMIT_PER_PAGE, offset=offset)

            if not vacancies:
                break

            for item in vacancies:
                parsed = parse_vacancy(item, query)
                if parsed["id"]:
                    save_vacancy(conn, parsed)
                    query_saved += 1
                    total_saved += 1

            offset += LIMIT_PER_PAGE
            time.sleep(0.5)

        print(f"  Сохранено по запросу: {query_saved}")

    conn.close()
    print(f"\n✓ Готово. Всего сохранено вакансий в базе: {total_saved}")


if __name__ == "__main__":
    main()
