# Minecraft 1.8.9 local smart control (Python)

Локальная панель управления для Minecraft 1.8.9:
- Auto Build (правый клик),
- Auto Click (левый клик),
- Double Click Assist (дублирует твой ручной клик: например 1 CPS -> ~2 CPS, работает только когда окно Minecraft активно),
- CPS настройка,
- бинды с сайта,
- умный автопоиск процесса Minecraft.

Когда `main.py` находит процесс Minecraft, статус становится **CONNECTED** (зеленым), а локальный сайт автоматически открывается в браузере.

## Быстрый запуск (Windows)

Запусти `start_client.bat` — он:
1. создаст `.venv` (если нет),
2. установит зависимости,
3. запустит `main.py`.

## Ручной запуск

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Сайт: `http://127.0.0.1:5000`

## Управление

- Включение/выключение функций: по назначенным биндам.
- Настройки (`CPS`, бинды Auto Build/Auto Click/Double Click Assist) меняются прямо с локального сайта.
- Если Minecraft не найден или окно Minecraft неактивно, функции автоматически отключаются/не срабатывают.

## Примечания

- На некоторых системах для глобальных биндов и кликов требуются права администратора.
- Поддержка рассчитана на Minecraft 1.8.9 (через признаки процесса Java/LaunchWrapper).
