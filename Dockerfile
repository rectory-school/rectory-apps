FROM python:3.10-buster as builder

WORKDIR /app

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt update
RUN apt install -y yarn

RUN pip install pip==22.2.2
RUN pip install poetry==1.2.1

COPY poetry.lock pyproject.toml /app/

RUN python -m venv --copies /app/.venv
RUN . /app/.venv/bin/activate && poetry install

COPY package.json yarn.lock /app/
RUN yarn install

FROM python:3.10-slim-buster as prod
RUN apt-get update && apt-get install -y postgresql-client

COPY --from=builder /app/.venv /app/.venv/
COPY --from=builder /app/node_modules /app/node_modules

ENV PATH /app/.venv/bin:$PATH

WORKDIR /app
COPY . ./

RUN python manage.py collectstatic --no-input
EXPOSE 8000

CMD ["gunicorn", "--worker-tmp-dir", "/dev/shm", "--bind", ":8000", "core.asgi:application", "-k", "uvicorn.workers.UvicornWorker"]