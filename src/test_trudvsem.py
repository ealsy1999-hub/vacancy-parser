import requests
import json

URL = "http://opendata.trudvsem.ru/api/v1/vacancies"

params = {
    "text": "python",
    "limit": 5,
    "offset": 0,
}

response = requests.get(URL, params=params, timeout=15)
print(f"Статус ответа: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    with open("data/sample_response.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Сохранено в data/sample_response.json")
else:
    print(f"Ошибка: {response.text[:300]}")
