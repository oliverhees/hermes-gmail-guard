FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd -u 10001 -M -s /usr/sbin/nologin bot \
 && mkdir -p /shared /data/tokens && chown 10001:10001 /shared
WORKDIR /srv
COPY freigabe-bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common ./common
COPY freigabe-bot/bot.py .
USER 10001
CMD ["python", "bot.py"]
