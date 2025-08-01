# FastAPI PNG API

Минималистичный FastAPI-сервис, генерирующий PNG-картинку по параметру `seed`.

## 🛠 Сборка и запуск

```bash
docker build -t fastapi-png .
docker run -p 8090:8090 fastapi-png
```

## 📌 API

- `GET /` — приветствие
- `GET /generate?seed=42` — PNG-изображение (image/png)
- `GET /secure` — защищённый маршрут (Basic Auth: `demo_user` / `demo_pass`)
