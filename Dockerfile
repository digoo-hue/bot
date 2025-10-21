# ✅ Базовый образ с Python 3.11
FROM python:3.11-slim

# Устанавливаем зависимости
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

# Устанавливаем часовой пояс (по желанию)
ENV TZ=Europe/Moscow

# Запускаем бота
CMD ["python", "main.py"]
