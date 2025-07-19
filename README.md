
<div align="center">

# Телеграм-бот Донорского центра НИЯУ МИФИ

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Koalal143/donorbot/main.yml?style=for-the-badge)

![Python](https://img.shields.io/badge/python-3.12-logo?style=for-the-badge&logo=python&color=%233776AB) ![PostgreSQL](https://img.shields.io/badge/postgresql-15-logo?style=for-the-badge&logo=postgresql&color=%234169E1) ![Redis](https://img.shields.io/badge/redis-logo?style=for-the-badge&logo=redis&logoColor=%23FFFFFF&color=%23FF4438)
![Aiogram](https://img.shields.io/badge/aiogram-logo?style=for-the-badge&logo=telegram&logoColor=%23FFFFFF&color=%2326A5E4) ![SQLAlchemy](https://img.shields.io/badge/sqlalchemy-logo?style=for-the-badge&logo=sqlalchemy&color=%23D71F00) ![GitHub Actions](https://img.shields.io/badge/github-actions-logo?style=for-the-badge&logo=githubactions&color=%232088FF)
![Ansible](https://img.shields.io/badge/ansible-logo?style=for-the-badge&logo=ansible&color=%23EE0000) ![Caddy](https://img.shields.io/badge/caddy-logo?style=for-the-badge&logo=caddy&color=%23FDDD35) ![Ruff](https://img.shields.io/badge/ruff-logo?style=for-the-badge&logo=ruff&logoColor=%23FFFFFF&color=%23D7FF64)

**🔗 Ссылка на бота:** [t.me/mifi_donot_center_bot](https://t.me/mifi_donot_center_bot)

</div>

## 📋 Описание

Телеграм-бот для автоматизации работы Донорского центра НИЯУ МИФИ. Бот предоставляет удобный интерфейс для доноров и организаторов для управления донациями, регистрации на дни донора и ведения статистики.

### 🎯 Основные возможности

#### Для доноров:
- 📝 **Регистрация** - простая регистрация по номеру телефона
- 👤 **Профиль донора** - просмотр личной информации и истории донаций
- 📅 **Запись на День донора** - регистрация на предстоящие мероприятия
- 📊 **История донаций** - отслеживание количества и дат донаций
- 🦴 **Регистр костного мозга** - информация о вступлении в регистр
- ℹ️ **Информационные материалы** - доступ к полезной информации о донорстве

#### Для организаторов:
- 🗂️ **Управление донорами** - добавление, редактирование и поиск доноров
- 📅 **Управление Днями донора** - создание и отмена мероприятий
- 📊 **Статистика** - генерация отчетов и экспорт данных в Excel
- 📢 **Массовые рассылки** - уведомления для различных категорий доноров
- ✅ **Подтверждение донаций** - управление статусом регистраций

## 📁 Структура проекта

```
DonorBotExample/
├── bot/                          # Основной код бота
│   ├── src/                      # Исходный код
│   │   ├── core/                 # Основные настройки и конфигурация
│   │   ├── db/                   # Настройки базы данных
│   │   ├── di/                   # Dependency Injection контейнеры
│   │   ├── dialogs/              # Диалоги пользовательского интерфейса
│   │   ├── enums/                # Перечисления
│   │   ├── handlers/             # Обработчики команд и сообщений
│   │   ├── models/               # Модели данных (SQLAlchemy)
│   │   ├── repositories/         # Репозитории для работы с БД
│   │   ├── scheduling/           # Планировщик задач
│   │   ├── services/             # Бизнес-логика и сервисы
│   │   ├── lifespan.py          # Управление жизненным циклом приложения
│   │   └── main.py              # Точка входа в приложение
│   ├── alembic/                  # Миграции базы данных
│   ├── .example.env             # Пример файла переменных окружения
│   ├── Dockerfile               # Docker-образ для бота
│   └── pyproject.toml           # Зависимости Python
├── deploy/                       # Конфигурация развертывания
│   └── ansible/                  # Ansible плейбуки для деплоя
│       ├── group_vars/          # Переменные групп
│       ├── inventory/           # Инвентарь серверов
│       ├── roles/               # Роли Ansible
│       ├── playbook.yml         # Основной плейбук
│       ├── requirements.yml     # Зависимости Ansible
│       └── secrets.example.yml  # Пример секретов
├── docker-compose.yml           # Продакшн конфигурация Docker
├── docker-compose.dev.yml       # Разработческая конфигурация Docker
└── docker-compose.base.yml      # Базовая конфигурация Docker
```

## 🚀 Запуск проекта

### 📋 Предварительные требования

- Docker и Docker Compose
- Python 3.12+ (для разработки)
- PostgreSQL 15+
- Redis

### ⚙️ Настройка переменных окружения

1. Скопируйте файл с примером переменных окружения:
```bash
cp bot/.example.env bot/.env
```

2. Отредактируйте файл `bot/.env`, указав ваши значения

### 🐳 Запуск через Docker Compose (рекомендуется)

#### Для разработки:
```bash
docker compose -f docker-compose.dev.yml up --build
```

#### Для продакшена:
```bash
docker compose up --build -d
```

### 🎭 Запуск через Ansible

1. Настройте инвентарь в `deploy/ansible/inventory/`
2. Скопируйте и заполните секреты:
```bash
cp deploy/ansible/secrets.example.yml deploy/ansible/secrets.yml
```
3. Запустите деплой:
```bash
ansible-galaxy install -r deploy/ansible/requirements.yml
cd deploy/ansible
ansible-playbook -i inventory/production playbook.yml
```

### 🛠️ Разработка

## 🔧 Дополнительные команды

### Создание миграций базы данных:
```bash
cd bot
alembic revision --autogenerate -m "Description of changes"
```

### Применение миграций:
```bash
cd bot
alembic upgrade head
```

### Откат миграций:
```bash
cd bot
alembic downgrade -1
```

## 📝 Особенности реализации

- **Архитектура**: Чистая архитектура с разделением на слои (handlers, services, repositories)
- **Dependency Injection**: Использование Dishka для управления зависимостями
- **Диалоги**: aiogram-dialog для создания интерактивных пользовательских интерфейсов
- **Миграции**: Alembic для управления схемой базы данных
- **Webhook/Polling**: Поддержка как webhook, так и polling режимов

## 📞 Контакты

- **Донорский центр YADONOR**: [официальный сайт](https://yadonor.ru/)
- **Telegram бот**: [@mifi_donot_center_bot](https://t.me/mifi_donot_center_bot)

---

<div align="center">
Сделано с ❤️ для Донорского центра НИЯУ МИФИ
</div>
