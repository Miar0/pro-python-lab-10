# Hotel Booking System (Production-Oriented Edition)

Лабораторна робота №10 з дисципліни «Професійний Python»  
**Варіант 8: Система бронювання готелю (Hotel Reservation System)**  
**Тема:** Production Python: Docker, CI/CD та захист проєкту

---

## 1. Description (Опис проєкту)

**Hotel Booking System** — це фінальна production-ready реалізація сервісу бронювання номерів готелю, що завершує наскрізний цикл розробки проєкту (ЛР №1 – №10). Проєкт спроєктовано та підготовлено за сучасними інженерними стандартами індустрії:
- **Packaging & Distribution:** Повноцінний Python-пакет (`hotel-booking` / `hotel_booking`), що відповідає стандарту PEP 517 / PEP 621, із автоматичним складанням бінарного дистрибутива **wheel** (`.whl`) та вихідного архіву **sdist** (`.tar.gz`).
- **12-Factor App Configuration:** Повна ізоляція конфігурації та чутливих даних (**secrets**) від вихідного коду через змінні середовища (**environment variables**) та безпечний шаблон `.env.example`.
- **Багатошарова архітектура (Layered Architecture):**
  - **API Layer (FastAPI):** Асинхронний REST API із валідацією запитів, пагінацією, фільтрацією та обробкою винятків.
  - **Service Layer (`HotelService`):** Бізнес-логіка, захист від подвійного бронювання (**double booking prevention**), перевірка конфліктів періодів дат, розрахунок виручки.
  - **Repository Layer (`RoomRepository`, `GuestRepository`, `ReservationRepository`):** Ізольовані операції доступу до даних.
  - **Database Layer (SQLAlchemy ORM + SQLite):** Персистентність даних із підтримкою транзакцій та змонтованого дискового розділу (**persistent volume**).
  - **Analytics Layer (`NumPy` + `@lru_cache`):** Векторизовані статистичні підрахунки та багаторівневе кешування із інвалідацією.
- **Containerization (Docker & Docker Compose):** Багатоетапний Dockerfile (**multi-stage build**), запуск від непривілейованого користувача (**non-root user**), перевірка працездатності контейнера (**HEALTHCHECK**) та збереження БД на томі (**volume**).
- **CI/CD Pipeline (GitHub Actions):** Автоматизований пайплайн перевірки коду (**lint**, **format check**, **type check**, **tests with coverage threshold**, **build**, **docker build**).

---

## 2. Features (Функціональність)

### Предметна логіка Варіанта 8
1. **Облік номерного фонду (`Room`):**
   - Збереження номера (`room_number`), типу (`room_type`: single, double, suite, deluxe), ціни (`price`) та статусу (`status`: available, occupied, maintenance);
   - Створення, редагування, пагінований перегляд та видалення номерів;
   - Пошук найдешевшого номера (`find_cheapest_room`) із можливістю фільтрації за категорією.
2. **Облік гостей (`Guest`):**
   - Збереження контактних даних (`first_name`, `last_name`, `email`, `phone`);
   - Пошук гостей за ім'ям, прізвищем або поштою із захистом від дублювання email.
3. **Керування бронюваннями (`Reservation`):**
   - Створення бронювання з автоматичним підрахунком тривалості ночей (`nights`) та фінальної вартості (`total_price`);
   - **Запобігання подвійному бронюванню (Double-booking prevention):** алгоритмічна перевірка перетину інтервалів $[check\_in, check\_out)$ із підтвердженими бронюваннями того самого номера;
   - Заборона бронювання кімнат у статусі `maintenance`;
   - Скасування бронювань із збереженням історії аудиту.
4. **Пошук вільних номерів (`get_available_rooms`):**
   - Фільтрація доступних номерів на будь-який діапазон дат без колізій, із опціональними обмеженнями за типом та максимальною вартістю проживання.
5. **Фінансова та статистична аналітика (`calculate_potential_revenue`):**
   - Підрахунок зафіксованої виручки підтверджених заїздів;
   - Розрахунок потенційного щомісячного доходу всього доступного номерного фонду;
   - Векторизовані розрахунки середнього чека, мінімуму, максимуму та стандартного відхилення цін номерів через **NumPy**.
6. **Health Monitoring:**
   - Системний ендпоінт `GET /health` для моніторингу статусу працездатності, версії сервісу та активного середовища виконання.

---

## 3. Requirements (Системні вимоги)

- **Python:** версія `>= 3.11`
- **Пакетний менеджер:** [uv](https://docs.astral.sh/uv/) (рекомендовано) або стандартний `pip`
- **Docker:** Docker Engine `>= 20.10` / Docker Desktop (для запуску контейнерів)
- **Docker Compose:** версія `>= 2.0` (опціонально)

---

## 4. Installation (Встановлення за допомогою `uv`)

Проєкт налаштовано для миттєвої синхронізації та ізоляції через `uv`:

### 1. Клонування репозиторію та перехід до каталогу
```bash
cd Lab_10
```

### 2. Створення віртуального оточення та встановлення залежностей
```bash
# Синхронізація базових та dev-залежностей через uv
uv sync --extra dev
```

---

## 5. Configuration (Конфігурація та змінні оточення)

Усі параметри роботи сервісу виносяться у змінні середовища відповідно до стандартів безпеки production-розробки. Паролі, секретні ключі та облікові дані **категорично заборонено комітити в Git**.

### Шаблон конфігурації `.env.example`
Для локального запуску скопіюйте файл-зразок:
```bash
cp .env.example .env
```

| Змінна оточення | Значення за замовчуванням | Опис |
|---|---|---|
| `APP_NAME` | `Hotel Booking System` | Назва сервісу у заголовках та документації |
| `ENVIRONMENT` | `development` | Оточення розгортання (`development`, `test`, `production`) |
| `DATABASE_URL` | `sqlite:///hotel.db` | URL підключення до БД (SQLite, PostgreSQL тощо) |
| `LOG_LEVEL` | `INFO` | Рівень логування (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `API_HOST` | `0.0.0.0` | IP-інтерфейс для прив'язки сервера |
| `API_PORT` | `8000` | Порт API-сервера |
| `SECRET_KEY` | *(dummy-default)* | Секретний ключ застосунку (перевизначається на production) |

### Перевірка безпеки (Security Audit Checklist)
- [x] Відсутні збережені реальні паролі та ключі у вихідному коді.
- [x] Файл `.env` внесено до `.gitignore` та відсутній у Git.
- [x] У Dockerfile не зашито жодних секретних значень.
- [x] Налаштування зчитуються через типобезпечний `pydantic-settings.BaseSettings`.

---

## 6. Running locally (Локальний запуск)

### Варіант А. Запуск через зареєстрований CLI-скрипт (з наповненням даними)
```bash
# Наповнити базу демонстраційними номерами, гостями і запустити сервер
uv run hotel-booking --seed --reload
```

### Варіант Б. Прямий запуск сервера Uvicorn
```bash
uv run uvicorn hotel_booking.api:app --reload --host 0.0.0.0 --port 8000
```

### Варіант В. Швидке наповнення БД без запуску сервера
```bash
uv run hotel-booking --seed-only
```

Після запуску сервіс доступний за адресою:  
`http://localhost:8000`

---

## 7. Running with Docker (Контейнеризація)

### Архітектура Dockerfile
У проєкті реалізовано **завдання підвищеної складності (Section 84-86)**:
1. **Multi-stage build:**
   - *Stage 1 (builder):* складання wheel-пакета у чистому середовищі.
   - *Stage 2 (runner):* фінальний мінімальний образ на базі `python:3.12-slim` без зайвих інструментів компіляції.
2. **Non-root user (`appuser`):** Запуск процесу від безпечного системного користувача з обмеженими правами.
3. **Docker HEALTHCHECK:** Інструкція самодіагностики контейнера через стандартну бібліотеку Python `urllib` кожні 30 секунд.
4. **Persistent Data Volume:** Збереження SQLite бази даних у змонтованому томі `/app/data`.

### 1. Збирання Docker образу
```bash
docker build -t hotel-booking:1.0.0 .
```

### 2. Запуск контейнера з передачею змінних оточення та Persistent Volume
```bash
docker run --rm -d \
  -p 8000:8000 \
  --name hotel_booking_service \
  -e ENVIRONMENT=production \
  -e LOG_LEVEL=INFO \
  -v hotel_data:/app/data \
  hotel-booking:1.0.0
```

### 3. Перевірка працездатності та стану контейнера
```bash
# Перевірка статусу Healthcheck
docker inspect --format='{{json .State.Health.Status}}' hotel_booking_service

# Тестовий запит до Health endpoint
curl http://localhost:8000/health
```

### 4. Запуск через Docker Compose
```bash
docker compose up -d --build
```
Для зупинки:
```bash
docker compose down
```

---

## 8. REST API (Документація ендпоінтів)

Інтерактивна документація генерується автоматично на основі специфікації **OpenAPI 3.1**:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Таблиця ендпоінтів

| Метод | URL-маршрут | Опис призначення | Очікуваний статус-код |
|---|---|---|---|
| `GET` | `/health` | Моніторинг стану сервісу, середовища та версії | `200 OK` |
| `GET` | `/` | Інформаційний корінь з посиланнями на документацію | `200 OK` |
| `GET` | `/rooms` | Список номерів із пагінацією (`page`, `page_size`), фільтрами за типом, ціною, статусом | `200 OK` |
| `POST` | `/rooms` | Створення нового номера в готелі | `201 Created` / `409 Conflict` |
| `GET` | `/rooms/{room_id}` | Отримання інформації про номер за ID | `200 OK` / `404 Not Found` |
| `PATCH`| `/rooms/{room_id}` | Часткове оновлення ціни, типу або статусу номера | `200 OK` / `404 Not Found` |
| `DELETE`| `/rooms/{room_id}`| Видалення номера | `204 No Content` / `404` |
| `GET` | `/rooms/available` | Пошук вільних номерів на вказані дати (`check_in`, `check_out`) | `200 OK` / `400 Bad Request` |
| `GET` | `/rooms/cheapest` | Отримання найдешевшого діючого номера (з фільтром за типом) | `200 OK` / `404 Not Found` |
| `GET` | `/rooms/revenue` | Розрахунок підтвердженої виручки та NumPy аналітики цін | `200 OK` |
| `POST` | `/guests` | Реєстрація гостя з валідацією пошти | `201 Created` / `409 Conflict` |
| `GET` | `/guests` | Список зареєстрованих гостей із пошуком за ім'ям або email | `200 OK` |
| `GET` | `/guests/{guest_id}`| Отримання профілю гостя за ID | `200 OK` / `404 Not Found` |
| `PATCH`| `/guests/{guest_id}`| Оновлення контактної інформації гостя | `200 OK` / `404` / `409` |
| `DELETE`| `/guests/{guest_id}`| Видалення запису гостя | `204 No Content` / `404` |
| `POST` | `/reservations` | Створення бронювання із захистом від колізій (double-booking) | `201 Created` / `409 Conflict` |
| `GET` | `/reservations` | Список бронювань із фільтрацією за номером кімнати та статусом | `200 OK` |
| `GET` | `/reservations/{id}`| Деталі бронювання | `200 OK` / `404 Not Found` |
| `DELETE`| `/reservations/{id}`| Скасування бронювання | `204 No Content` / `404` |

---

## 9. Testing & Quality Control (Тестування та якість коду)

### 1. Запуск тестового набору з аналізом покриття
```bash
uv run pytest -v --cov=hotel_booking --cov-report=term-missing
```
> **Результат:** 36 тестів успішно пройдено, сумарне покриття коду складає **97%** (що суттєво перевищує обов'язковий поріг у 80%).

### 2. Перевірка статичного лінтера (Ruff Linter)
```bash
uv run ruff check .
```

### 3. Перевірка форматування коду (Ruff Formatter)
```bash
uv run ruff format --check .
```

### 4. Статична перевірка типів (Mypy Type Checking)
```bash
uv run mypy src
```

### 5. Запуск оптимізаційних бенчмарків (NumPy vs Python)
```bash
uv run python benchmarks/benchmark.py
```

---

## 10. Packaging (Складання та перевірка пакетів)

Складання пакетів виконується відповідно до сучасних стандартів PEP 517:
```bash
# Складання wheel та sdist через uv
uv build
```
Або через стандартну утиліту `build`:
```bash
uv run python -m build
```

У результаті в директорії `dist/` утворюються артефакти:
```text
dist/
├── hotel_booking-1.0.0-py3-none-any.whl   # Бінарний wheel пакет
└── hotel_booking-1.0.0.tar.gz            # Вихідний source distribution (sdist)
```

### Перевірка встановлення wheel у чистому ізольованому середовищі:
```bash
# Створення чистих тестових оточень
uv venv test_env
# Встановлення wheel
uv pip install --python test_env dist/hotel_booking-1.0.0-py3-none-any.whl
# Перевірка виконання команди точки входу
./test_env/Scripts/hotel-booking --version
```

---

## 11. CI/CD (GitHub Actions Pipeline)

Конфігурація розміщена у `.github/workflows/ci.yml`.  
Пайплайн спрацьовує автоматично при кожному `push` та `pull_request` у гілки `main` і `develop`.

### Етапи пайплайну:
1. **Matrix Strategy:** Тестування одночасно на Python `3.11` та `3.12`.
2. **Checkout & Environment Setup:** Клонування коду та налаштування середовища.
3. **Dependency Installation:** Встановлення залежностей пакету у режимі розробника (`pip install -e ".[dev]"`).
4. **Code Quality Gates:**
   - `ruff check .` — перевірка якості та відсутності синтаксичних/стильових помилок;
   - `ruff format --check .` — перевірка відповідності код-стайлу;
   - `mypy src` — сувора статична типізація вихідного коду.
5. **Automated Testing:** Запуск `pytest` із фіксацією покриття та автоматичним відхиленням білду при зниженні покриття нижче 80% (`--cov-fail-under=80`).
6. **Package Build:** Збирання дистрибутивів `wheel` і `sdist` та завантаження артефактів (**Artifact Upload**).
7. **Docker Container Build:** Складання тестового образу `hotel-booking:ci` для гарантії працездатності Dockerfile.

---

## 12. Project Structure (src-layout)

```text
Lab_10/
├── .github/
│   └── workflows/
│       └── ci.yml             # Конфігурація GitHub Actions CI/CD пайплайну
│
├── src/
│   └── hotel_booking/         # Основний пакет варіанта 8
│       ├── __init__.py        # Експорт моделей, сервісів та __version__
│       ├── api.py             # FastAPI застосунок, lifespan, обробка помилок
│       ├── config.py          # Pydantic Settings, змінні оточення, логування
│       ├── database.py        # SQLAlchemy Base, engine, SessionLocal, init_db
│       ├── models.py          # ORM сутності: Room, Guest, Reservation
│       ├── schemas.py         # Pydantic v2 схеми валідації запитів/відповідей
│       ├── exceptions.py      # Доменні винятки (Conflict, NotFound, Validation)
│       ├── repositories.py    # Repository layer: Room, Guest, Reservation
│       ├── services.py        # Service layer: доступність, double booking, revenue
│       ├── analytics.py       # NumPy векторизація та LRU кешування з інвалідацією
│       └── main.py            # CLI інтерфейс (hotel-booking) та сідування даних
│
├── tests/                     # Повний тестовий набір (36 тестів, 97% покриття)
│   ├── __init__.py
│   ├── conftest.py            # Ізольована in-memory SQLite фікстура та TestClient
│   ├── test_config.py         # Тестування конфігурації та env-змінних
│   ├── test_health.py         # Тестування /health та кореневого ендпоінта
│   ├── test_models.py         # Тестування ORM моделей, розрахунку ночей
│   ├── test_repositories.py   # Тестування CRUD та пошуку колізій у БД
│   ├── test_services.py       # Тестування бізнес-правил, захисту подвійного бронювання
│   ├── test_api.py            # Інтеграційні тести REST API endpoints
│   ├── test_analytics.py      # Тестування NumPy обчислень та кешування
│   └── test_main.py           # Тестування CLI прапорців та сідування
│
├── benchmarks/
│   ├── __init__.py
│   └── benchmark.py           # Порівняльний бенчмарк Python vs NumPy
│
├── migrations/
│   ├── __init__.py
│   └── README.md              # Документація структури міграцій БД
│
├── Dockerfile                 # Multi-stage, non-root, HEALTHCHECK образ
├── docker-compose.yml         # Специфікація Docker Compose з томом даних
├── .dockerignore              # Файли, що виключаються з образу Docker
├── .gitignore                 # Виключення тимчасових файлів, .env, *.db, dist
├── .env.example               # Безпечний шаблон змінних середовища
├── pyproject.toml             # Декларація пакета, метаданих та інструментів
├── README.md                  # Головна документація проєкту
├── LICENSE                    # Ліцензія MIT
└── alembic.ini                # Конфігурація Alembic міграцій
```

---

## 13. Сценарій демонстрації на захисті проєкту (Defense Walkthrough)

Під час фінального захисту лабораторної роботи демонструється повний життєвий цикл сервісу:

- **Крок 1. Структура проєкту:** Показати `src-layout`, наявність `.github/workflows`, `tests/`, `benchmarks/`, `Dockerfile`.
- **Крок 2. Конфігурація та безпека:** Продемонструвати `src/hotel_booking/config.py`, файл `.env.example`, відсутність `.env` у репозиторії та гарантію неналежності секретів до коду.
- **Крок 3. Метадані пакета:** Відкрити `pyproject.toml`, показати секції `[project]`, `[build-system]`, залежності, точки входу `[project.scripts]`.
- **Крок 4. Автоматичне тестування:**  
  Виконати: `uv run pytest -v` — переконатися у проходженні 36 тестів із покриттям 97%.
- **Крок 5. Контроль якості (Linting & Formatting):**  
  Виконати: `uv run ruff check .` та `uv run ruff format --check .` (0 помилок).
- **Крок 6. Контроль типізації:**  
  Виконати: `uv run mypy src` (0 помилок).
- **Крок 7. Складання дистрибутиву:**  
  Виконати: `uv build` — показати появу артефактів `.whl` та `.tar.gz` у директорії `dist/`.
- **Крок 8. Складання Docker образу:**  
  Виконати: `docker build -t hotel-booking:1.0.0 .` — звернути увагу на multi-stage build та non-root user.
- **Крок 9. Запуск контейнера:**  
  Виконати: `docker run --rm -d -p 8000:8000 -v hotel_data:/app/data hotel-booking:1.0.0`.
- **Крок 10. Демонстрація API:**  
  Відкрити у браузері:
  - `http://localhost:8000/health` (відповідь `{"status":"ok", "environment":"production"}`);
  - `http://localhost:8000/docs` (Swagger UI документація з усіма методами варіанта 8).
- **Крок 11. Демонстрація CI пайплайну:**  
  Показати зелені чек-марки GitHub Actions CI: lint, format, type check, tests, package build, docker build.

---

## 14. Автор

- **Студент:** Івасів Данило  
- **Група:** ФеП-32  
- **Варіант:** 8 (Система бронювання готелю)
