"""
День 3: анализ навыков и зарплат по городам через pandas.
"""

import sqlite3
import pandas as pd

DB_PATH = "data/vacancies.db"

# Загружаем данные из SQLite в DataFrame
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM vacancies", conn)
conn.close()

print(f"Загружено вакансий: {len(df)}")
print(f"Колонки: {list(df.columns)}\n")

# === 1. Топ регионов по количеству вакансий ===
print("=== ТОП-10 РЕГИОНОВ ПО КОЛИЧЕСТВУ ВАКАНСИЙ ===")
top_regions = df["region"].value_counts().head(10)
print(top_regions.to_string())

# === 2. Средняя зарплата по регионам (только где указана) ===
print("\n=== СРЕДНЯЯ ЗАРПЛАТА ПО РЕГИОНАМ (ТОП-10) ===")
df_salary = df[df["salary_min"] > 0].copy()
salary_by_region = (
    df_salary.groupby("region")["salary_min"]
    .mean()
    .sort_values(ascending=False)
    .head(10)
    .astype(int)
)
print(salary_by_region.to_string())

# === 3. Топ навыков по всем вакансиям ===
print("\n=== ТОП-20 НАВЫКОВ ===")
all_skills = []
for skills_str in df["skills"].dropna():
    if skills_str.strip():
        for skill in skills_str.split(","):
            skill = skill.strip()
            if skill:
                all_skills.append(skill)

skills_series = pd.Series(all_skills)
top_skills = skills_series.value_counts().head(20)
print(top_skills.to_string())

# === 4. Средняя зарплата по типу вакансии (нефтянка vs финансы) ===
print("\n=== СРЕДНЯЯ ЗАРПЛАТА: НЕФТЯНКА VS ФИНАНСЫ ===")
oil_queries = ["оператор добычи нефти и газа", "инженер нефтегазового оборудования",
               "буровой мастер", "геолог нефтегазовой", "технолог нефтепереработки",
               "инженер по бурению"]
fin_queries = ["финансовый аналитик", "бухгалтер", "экономист", "кредитный специалист банка"]

df_oil = df[df["search_query"].isin(oil_queries) & (df["salary_min"] > 0)]
df_fin = df[df["search_query"].isin(fin_queries) & (df["salary_min"] > 0)]

print(f"Нефтянка — средняя зарплата (min): {int(df_oil['salary_min'].mean()):,} руб. | вакансий с зарплатой: {len(df_oil)}")
print(f"Финансы  — средняя зарплата (min): {int(df_fin['salary_min'].mean()):,} руб. | вакансий с зарплатой: {len(df_fin)}")

# === 5. Требования по опыту ===
print("\n=== РАСПРЕДЕЛЕНИЕ ПО ОПЫТУ (лет) ===")
exp = pd.to_numeric(df["experience"], errors="coerce").dropna().astype(int).value_counts().sort_index()
for years, count in exp.items():
    label = f"{years} лет" if years > 0 else "Без опыта"
    print(f"  {label}: {count} вакансий")

# === 6. Сохраняем сводку в CSV для дашборда (День 4) ===
df_salary_csv = df_salary.groupby("region")["salary_min"].mean().astype(int).reset_index()
df_salary_csv.columns = ["region", "avg_salary"]
df_salary_csv = df_salary_csv.sort_values("avg_salary", ascending=False)
df_salary_csv.to_csv("data/salary_by_region.csv", index=False, encoding="utf-8")

skills_df = top_skills.reset_index()
skills_df.columns = ["skill", "count"]
skills_df.to_csv("data/top_skills.csv", index=False, encoding="utf-8")

print("\n✓ Сохранено: data/salary_by_region.csv")
print("✓ Сохранено: data/top_skills.csv")
print("\nЭти файлы используем в День 4 для дашборда.")
