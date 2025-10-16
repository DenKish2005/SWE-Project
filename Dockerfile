# Используем официальный Python-образ
FROM python:3.11

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Создаём рабочую директорию
WORKDIR /code

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt /code/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копируем весь проект внутрь контейнера
COPY . /code/
