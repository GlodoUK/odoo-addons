FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim

SHELL ["/bin/bash", "-xo", "pipefail", "-c"]

ARG GITHUB_TOKEN
ARG ODOO_VERSION

ENV \
    UV_NO_CACHE=true \
    UV_PYTHON_DOWNLOADS=never \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    UV_INDEX_URL=https://wheelhouse.odoo-community.org/oca-simple-and-pypi \
    ODOO_RC=/opt/odoo/odoo.conf

RUN apt-get -yq update && \
  apt-get install -yqq --no-install-recommends \
    build-essential \
    curl \
    debianutils \
    expect \
    git

WORKDIR /opt/odoo

ADD . src/private/

ENV PATH="/opt/odoo/.venv/bin:$PATH"

RUN run-parts src/private/.ci/build.d

ENTRYPOINT [ "run-parts", "src/private/.ci/entrypoint.d" ]
