FROM python:3.12-bookworm AS python-builder

WORKDIR /app

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt update
RUN apt install -y yarn

RUN pip install pip==24.0
RUN pip install pdm==2.14.0

COPY pyproject.toml pdm.lock /app/

RUN python -m venv --copies /app/.venv
RUN . /app/.venv/bin/activate && pdm install

FROM node:latest AS node-builder

WORKDIR /app

COPY package.json yarn.lock /app/
RUN yarn install

FROM python:3.12-slim-bookworm AS prod
RUN apt-get update && apt-get install -y postgresql-client

COPY --from=python-builder /app/.venv /app/.venv/
COPY --from=node-builder /app/node_modules /app/node_modules

ENV PATH=/app/.venv/bin:$PATH

WORKDIR /app
COPY . ./

RUN python manage.py collectstatic --no-input
EXPOSE 8000

CMD ["gunicorn", "--worker-tmp-dir", "/dev/shm", "--bind", ":8000", "core.wsgi:application"]