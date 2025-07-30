## Задание
### HTTP сервер


📄 Описание

Реализация простого многопоточного HTTP/1.1 сервера, способного обрабатывать GET и HEAD запросы. Сервер соответствует требованиям задания и проходит все тесты из http-test-suite.

🚀 Архитектура

Модель: multithreaded (thread-per-request)

Технологии: socket, threading, без использования HTTP-фреймворков

Безопасность: защита от path traversal, чтение только внутри DOCUMENT_ROOT

📆 Поддерживаемые возможности

GET, HEAD

200, 403, 404, 405, 500 коды ответа

Content-Type по расширению

index.html для директорий

URL-декодирование (%20, пробелы, Unicode)

Заголовки: Date, Server, Content-Length, Content-Type, Connection

🔄 Запуск

python httpd.py -r ./httptest -p 80 -w 100 -l info

🏋️ Тестирование

✅ Функциональные тесты

python httptest.py
# → Все 23 теста пройдены

⚖️ Нагрузочное тестирование

Проведено с помощью ab.exe из Apache Lounge на Windows:

ab -n 10000 -c 50 -r http://localhost:80/httptest/wikipedia_russia.html

⚡ Результаты:

Concurrency Level: 50

Requests per second: 378.41 [#/sec]

Time per request: 132.1 ms (mean)

Failed requests: 0

Longest request: 415 ms

Transfer rate: ~353 MB/sec

✅ Вывод

Сервер стабильно обрабатывает нагрузку в 10 000 запросов при 50 одновременных соединениях и обрабатывает все случаи, указанные в тестах.

⚖️ Проверено на:

Python 3.10 (Windows)

Git Bash + ApacheBench (ab.exe)