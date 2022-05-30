FROM python:3.10-buster as builder

WORKDIR /app

RUN pip install pip==22.1.1
RUN pip install poetry==1.1.13

COPY poetry.lock pyproject.toml /app/

RUN python -m venv --copies /app/.venv
RUN . /app/.venv/bin/activate && poetry install

FROM python:3.10-slim-buster as prod
COPY --from=builder /app/.venv /app/.venv/
ENV PATH /app/.venv/bin:$PATH

WORKDIR /app
COPY . ./

RUN python manage.py collectstatic --no-input
EXPOSE 8000

CMD ["gunicorn", "--worker-tmp-dir", "/dev/shm", "--bind", ":8000", "core.asgi:application", "-k", "uvicorn.workers.UvicornWorker"]