FROM python:3.11-slim

# Копируем файлы приложения в контейнер
WORKDIR /app
COPY ./docker_compose_viewer.py /app
COPY ./requirements.txt /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Открываем порт для Flask-сервера
EXPOSE 8888

# Указываем команду запуска
CMD ["python3 /app/docker_compose_viewer.py"]
