# ------------------------------------------------------------
# Get uv binary
# ------------------------------------------------------------

FROM ghcr.io/astral-sh/uv:latest AS uv


# ------------------------------------------------------------
# Apache Airflow + MDM Platform
# ------------------------------------------------------------

# FROM apache/airflow:3.1.0-python3.12
FROM apache/airflow:3.2.2-python3.13

# ------------------------------------------------------------
# Install uv
# ------------------------------------------------------------

USER root

COPY --from=uv /uv /usr/local/bin/uv


# ------------------------------------------------------------
# MDM Platform
# ------------------------------------------------------------

WORKDIR /opt/mdm-platform

COPY --chown=airflow:root pyproject.toml ./pyproject.toml


# ------------------------------------------------------------
# Install MDM dependencies into Airflow's Python environment
# ------------------------------------------------------------

USER airflow

RUN uv pip install \
    --python /home/airflow/.local/bin/python \
    --no-cache \
    -r pyproject.toml


# ------------------------------------------------------------
# Copy complete MDM Platform application
# ------------------------------------------------------------

USER root

COPY --chown=airflow:root . /opt/mdm-platform/


# ------------------------------------------------------------
# Django configuration
# ------------------------------------------------------------

ENV PYTHONPATH="/opt/mdm-platform"
ENV DJANGO_SETTINGS_MODULE="config.settings"


# ------------------------------------------------------------
# Airflow runtime
# ------------------------------------------------------------

USER airflow

WORKDIR /opt/airflow