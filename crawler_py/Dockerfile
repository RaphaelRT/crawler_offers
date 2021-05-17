FROM python:3.8-slim AS builder
WORKDIR /app
RUN apt-get update \
&& apt-get install gcc -y \
&& apt-get clean
RUN python3 -m venv .venv && .venv/bin/pip install --no-cache-dir -U pip setuptools
COPY ./crawler_py/requirements.txt .
RUN .venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.8-slim
WORKDIR /app
COPY --from=builder /app /app
COPY ./crawler_py/app.py .
COPY .env .
#RUN IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' selenium-hub); echo SELENIUM_HUB_IP=$IP >> .env
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 9500
CMD ["flask", "run", "--host=0.0.0.0", "--port=9500"]
