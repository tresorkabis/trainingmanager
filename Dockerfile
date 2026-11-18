FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=settings.prod

WORKDIR /app

RUN addgroup --system django && adduser --system --ingroup django django

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=django:django . .

RUN mkdir -p /app/staticfiles /app/mediafiles \
    && chown -R django:django /app

USER django

EXPOSE 8000

CMD ["/app/docker-entrypoint.sh"]
