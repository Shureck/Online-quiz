FROM python:3.8-buster

# рабочая директория внутри проекта
WORKDIR /usr/src/app

# переменные окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем зависимости для Postgre
#RUN apk update \
#    && apk add postgresql-dev gcc python3-dev musl-dev
#RUN apk --update --upgrade add gcc musl-dev jpeg-dev zlib-dev libffi-dev cairo-dev pango-dev gdk-pixbuf-dev
#RUN apt install openslide-to
# устанавливаем зависимости
RUN pip install --upgrade pip
COPY req.txt .
RUN pip install -r req.txt
# copy project
COPY . .