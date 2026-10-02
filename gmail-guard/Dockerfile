FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd -u 10001 -M -s /usr/sbin/nologin guard \
 && mkdir -p /shared /data/tokens && chown -R 10001:10001 /shared /data
WORKDIR /srv
COPY gmail-guard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common ./common
COPY gmail-guard/app ./app
USER 10001
EXPOSE 8000
CMD ["python", "-m", "app.server"]
