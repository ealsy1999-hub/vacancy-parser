"""
День 4: генерация HTML-дашборда из данных SQLite.
"""

import sqlite3
import json
import pandas as pd

DB_PATH = "data/vacancies.db"
OUTPUT = "data/dashboard.html"

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM vacancies", conn)
conn.close()

# === Подготовка данных ===

# Топ-10 регионов по вакансиям
top_regions = df["region"].value_counts().head(10)
regions_labels = top_regions.index.tolist()
regions_values = top_regions.values.tolist()

# Топ-10 регионов по средней зарплате
df_salary = df[df["salary_min"] > 0]
salary_by_region = (
    df_salary.groupby("region")["salary_min"]
    .mean().astype(int)
    .sort_values(ascending=False)
    .head(10)
)
salary_labels = salary_by_region.index.tolist()
salary_values = salary_by_region.values.tolist()

# Топ-15 навыков
all_skills = []
for s in df["skills"].dropna():
    if s.strip():
        for skill in s.split(","):
            skill = skill.strip()
            if skill and len(skill) > 3:
                all_skills.append(skill)
skills_series = pd.Series(all_skills).value_counts().head(15)
skills_labels = skills_series.index.tolist()
skills_values = skills_series.values.tolist()

# Нефтянка vs Финансы
oil_queries = ["оператор добычи нефти и газа", "инженер нефтегазового оборудования",
               "буровой мастер", "геолог нефтегазовой", "технолог нефтепереработки",
               "инженер по бурению"]
fin_queries = ["финансовый аналитик", "бухгалтер", "экономист", "кредитный специалист банка"]
oil_avg = int(df[df["search_query"].isin(oil_queries) & (df["salary_min"] > 0)]["salary_min"].mean())
fin_avg = int(df[df["search_query"].isin(fin_queries) & (df["salary_min"] > 0)]["salary_min"].mean())

# Опыт
exp_series = pd.to_numeric(df["experience"], errors="coerce").dropna().astype(int).value_counts().sort_index()
exp_labels = [f"{x} лет" if x > 0 else "Без опыта" for x in exp_series.index.tolist()]
exp_values = exp_series.values.tolist()

# Топ-10 компаний
top_companies = df["company"].value_counts().head(10)
companies_labels = top_companies.index.tolist()
companies_values = top_companies.values.tolist()

total = len(df)
oil_count = len(df[df["search_query"].isin(oil_queries)])
fin_count = len(df[df["search_query"].isin(fin_queries)])

# === HTML ===
html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Анализ рынка труда — Нефтянка & Финансы</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f1117; color: #e0e0e0; }}
  .header {{ background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 40px; text-align: center; border-bottom: 1px solid #2a2a4a; }}
  .header h1 {{ font-size: 28px; color: #fff; margin-bottom: 8px; }}
  .header p {{ color: #888; font-size: 14px; }}
  .stats {{ display: flex; gap: 20px; padding: 30px 40px; justify-content: center; flex-wrap: wrap; }}
  .stat-card {{ background: #1e1e2e; border: 1px solid #2a2a4a; border-radius: 12px; padding: 24px 32px; text-align: center; min-width: 160px; }}
  .stat-card .num {{ font-size: 32px; font-weight: 700; color: #7c7cff; }}
  .stat-card .label {{ font-size: 13px; color: #888; margin-top: 4px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; padding: 0 40px 40px; max-width: 1400px; margin: 0 auto; }}
  .card {{ background: #1e1e2e; border: 1px solid #2a2a4a; border-radius: 12px; padding: 24px; }}
  .card h2 {{ font-size: 15px; color: #aaa; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1px; }}
  .full-width {{ grid-column: 1 / -1; }}
  canvas {{ max-height: 320px; }}
  @media (max-width: 768px) {{ .grid {{ grid-template-columns: 1fr; padding: 0 16px 24px; }} .stats {{ padding: 20px 16px; }} }}
</style>
</head>
<body>

<div class="header">
  <h1>📊 Рынок труда: Нефтянка & Финансы</h1>
  <p>Данные: trudvsem.ru (Работа России) · {total} вакансий · Июнь 2026</p>
</div>

<div class="stats">
  <div class="stat-card"><div class="num">{total}</div><div class="label">Вакансий собрано</div></div>
  <div class="stat-card"><div class="num">{oil_count}</div><div class="label">Нефтегаз</div></div>
  <div class="stat-card"><div class="num">{fin_count}</div><div class="label">Финансы</div></div>
  <div class="stat-card"><div class="num">{oil_avg:,}</div><div class="label">Ср. зарплата нефтянка (руб.)</div></div>
  <div class="stat-card"><div class="num">{fin_avg:,}</div><div class="label">Ср. зарплата финансы (руб.)</div></div>
</div>

<div class="grid">

  <div class="card">
    <h2>Топ регионов по вакансиям</h2>
    <canvas id="regionsChart"></canvas>
  </div>

  <div class="card">
    <h2>Средняя зарплата по регионам</h2>
    <canvas id="salaryChart"></canvas>
  </div>

  <div class="card full-width">
    <h2>Топ навыков</h2>
    <canvas id="skillsChart"></canvas>
  </div>

  <div class="card">
    <h2>Нефтянка vs Финансы</h2>
    <canvas id="compareChart"></canvas>
  </div>

  <div class="card">
    <h2>Распределение по опыту</h2>
    <canvas id="expChart"></canvas>
  </div>

  <div class="card full-width">
    <h2>Топ компаний по количеству вакансий</h2>
    <canvas id="companiesChart"></canvas>
  </div>

</div>

<script>
const COLORS = ['#7c7cff','#5c9eff','#4ecdc4','#45b7d1','#96ceb4','#ffeaa7','#dda0dd','#98d8c8','#f7dc6f','#82e0aa'];

Chart.defaults.color = '#888';
Chart.defaults.borderColor = '#2a2a4a';

new Chart(document.getElementById('regionsChart'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(regions_labels, ensure_ascii=False)},
    datasets: [{{ data: {json.dumps(regions_values)}, backgroundColor: COLORS, borderRadius: 6 }}]
  }},
  options: {{ indexAxis: 'y', plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ grid: {{ color: '#2a2a4a' }} }}, y: {{ grid: {{ display: false }} }} }} }}
}});

new Chart(document.getElementById('salaryChart'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(salary_labels, ensure_ascii=False)},
    datasets: [{{ data: {json.dumps(salary_values)}, backgroundColor: '#5c9eff', borderRadius: 6 }}]
  }},
  options: {{ indexAxis: 'y', plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ grid: {{ color: '#2a2a4a' }} }}, y: {{ grid: {{ display: false }} }} }} }}
}});

new Chart(document.getElementById('skillsChart'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(skills_labels, ensure_ascii=False)},
    datasets: [{{ data: {json.dumps(skills_values)}, backgroundColor: '#4ecdc4', borderRadius: 6 }}]
  }},
  options: {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ grid: {{ color: '#2a2a4a' }} }}, x: {{ grid: {{ display: false }} }} }} }}
}});

new Chart(document.getElementById('compareChart'), {{
  type: 'bar',
  data: {{
    labels: ['Нефтянка', 'Финансы'],
    datasets: [{{ data: [{oil_avg}, {fin_avg}], backgroundColor: ['#7c7cff', '#5c9eff'], borderRadius: 8 }}]
  }},
  options: {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ grid: {{ color: '#2a2a4a' }} }}, x: {{ grid: {{ display: false }} }} }} }}
}});

new Chart(document.getElementById('expChart'), {{
  type: 'doughnut',
  data: {{
    labels: {json.dumps(exp_labels, ensure_ascii=False)},
    datasets: [{{ data: {json.dumps(exp_values)}, backgroundColor: COLORS, borderWidth: 0 }}]
  }},
  options: {{ plugins: {{ legend: {{ position: 'right' }} }} }}
}});

new Chart(document.getElementById('companiesChart'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(companies_labels, ensure_ascii=False)},
    datasets: [{{ data: {json.dumps(companies_values)}, backgroundColor: COLORS, borderRadius: 6 }}]
  }},
  options: {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ grid: {{ color: '#2a2a4a' }} }}, x: {{ grid: {{ display: false }} }} }} }}
}});
</script>
</body>
</html>"""

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✓ Дашборд сохранён: {OUTPUT}")
print(f"  Открой в браузере: open {OUTPUT}")
