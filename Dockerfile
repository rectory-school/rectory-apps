FROM python:3.14-bookworm AS python-builder

WORKDIR /app

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt update
RUN apt install -y yarn

RUN pip install pip==25.2
RUN pip install uv==0.8.14

COPY pyproject.toml uv.lock /app/

RUN python -m venv --copies /app/.venv
RUN . /app/.venv/bin/activate && uv sync --locked

FROM node:26-bookworm-slim AS node-builder

WORKDIR /app

# Node images stopped shipping yarn (and corepack) as of Node 26, so install
# it explicitly. The version is pinned so a new Node release can't break the
# build the way the floating "latest" tag did.
RUN npm install -g yarn@1.22.22

COPY package.json yarn.lock /app/
RUN yarn install --frozen-lockfile

FROM python:3.14-slim-bookworm AS prod
RUN apt-get update && apt-get install -y postgresql-client

COPY --from=python-builder /app/.venv /app/.venv/
COPY --from=node-builder /app/node_modules /app/node_modules

ENV PATH=/app/.venv/bin:$PATH

WORKDIR /app
COPY . ./

RUN python manage.py collectstatic --no-input
EXPOSE 8000

CMD ["gunicorn", "--worker-tmp-dir", "/dev/shm", "--bind", ":8000", "core.wsgi:application"]