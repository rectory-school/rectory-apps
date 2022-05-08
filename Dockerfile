FROM python:3.10-alpine

RUN mkdir /app/
RUN mkdir /app/code/
WORKDIR /app/code/

RUN apk add --no-cache build-base libffi-dev bzip2-dev zlib-dev sqlite-dev jpeg-dev postgresql-dev

RUN pip install pip==22.0.4
RUN pip install poetry==1.1.13

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

# Start gunicorn
CMD ["gunicorn", "--worker-tmp-dir", "/dev/shm", "--bind", ":8000", "core.asgi:application", "-k", "uvicorn.workers.UvicornWorker"]