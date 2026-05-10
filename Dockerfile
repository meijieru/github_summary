FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    XDG_STATE_HOME=/data

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY github_summary ./github_summary
COPY docker-entrypoint.sh ./docker-entrypoint.sh

RUN pip install --no-cache-dir . \
    && chmod +x /app/docker-entrypoint.sh \
    && mkdir -p /config /data \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin ghsum \
    && chown -R ghsum:ghsum /app /config /data

USER ghsum

VOLUME ["/config", "/data"]
EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["serve"]
