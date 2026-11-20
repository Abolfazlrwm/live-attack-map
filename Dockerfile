FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a non-root user (uid 1000 so bind-mounted ./logs and ./data
# directories owned by the host's uid 1000 stay writable).
RUN useradd --system --uid 1000 --create-home appuser \
    && mkdir -p /app/logs /app/data \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 2222 8080

# Gunicorn (gthread) instead of the Werkzeug dev server: one worker with a
# thread pool serves the Socket.IO long-polling fallback, background log/geo
# threads keep working unchanged, and --timeout stays above the Socket.IO
# ping window so pending long polls are not killed.
CMD ["gunicorn", "-w", "1", "--threads", "24", "--timeout", "120", \
     "-b", "0.0.0.0:8080", "dashboard.app:app"]
