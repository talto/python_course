# FastAPI PNG API

Минималистичный FastAPI-сервис, генерирующий PNG-картинку по параметру `seed`.

## 🛠 Сборка и запуск

```bash
docker build -t fastapi-png .
docker run -p 8090:8090 fastapi-png
```

## 📌 API

- `GET /` — приветствие
- `GET /generate?seed=42` — PNG-изображение (image/png) (нужен токен)
- `GET /secure` — защищённый маршрут (Basic Auth: `demo_user` / `demo_pass`)(нужен токен)
- `POST /login` — получение JWT токена (demo_user / demo_pass)

# Получить токен
TOKEN=$(curl -s -X POST http://localhost:8090/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo_user&password=demo_pass" | jq -r .access_token)

# Получить картинку
curl -H "Authorization: Bearer $TOKEN" \
  -o out.png "http://localhost:8090/generate?seed=42"

# Проверить защищённый маршрут
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8090/secure