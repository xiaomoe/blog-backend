# syntax=docker/dockerfile:1
FROM python:3.11.2-slim-bullseye as builder

# install pdm
# hadolint ignore=DL3042
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install pdm==2.4.5

# install dependencies
COPY pyproject.toml pdm.lock /
RUN mkdir __pypackages__
RUN --mount=type=cache,target=/root/.cache/pdm \
    pdm install --prod --no-lock --no-editable

FROM python:3.11.2-slim-bullseye

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/pkgs/lib
ENV PATH="/pkgs/bin:${PATH}"
COPY --from=builder /__pypackages__/3.11 /pkgs

COPY ./compose/dev/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /app

ENTRYPOINT [ "/entrypoint.sh" ]
