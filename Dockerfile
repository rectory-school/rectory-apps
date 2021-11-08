FROM python:3.10-alpine

RUN mkdir /app/
RUN mkdir /app/code/
WORKDIR /app/code/

RUN apk add --no-cache build-base libffi-dev bzip2-dev zlib-dev sqlite-dev jpeg-dev postgresql-dev

RUN pip install pip==21.3.1
RUN pip install poetry==1.1.11

COPY poetry.lock pyproject.toml /code/

# Copy only requirements to cache them in docker layer
WORKDIR /code
COPY poetry.lock pyproject.toml /code/

RUN poetry config virtualenvs.create false
RUN poetry install --no-dev --no-interaction --no-ansi


# Creating folders, and files for a project:
COPY . /code

# Temporary secret key for collecting static
ARG SECRET_KEY=-

RUN python manage.py collectstatic --no-input
EXPOSE 8000

# Tell uWSGI where to find your wsgi file (change this):
ENV UWSGI_WSGI_FILE=core/wsgi.py

# Base uWSGI configuration (you shouldn't need to change these):
ENV UWSGI_HTTP=:8000 UWSGI_MASTER=1 UWSGI_HTTP_AUTO_CHUNKED=1 UWSGI_HTTP_KEEPALIVE=1 UWSGI_LAZY_APPS=1 UWSGI_WSGI_ENV_BEHAVIOR=holy UWSGI_UID=nobody UWSGI_GID=nobody

# Number of uWSGI workers and threads per worker (customize as needed):
# ENV UWSGI_WORKERS=2 UWSGI_THREADS=4

# Start uWSGI
CMD ["uwsgi"]