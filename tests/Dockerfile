FROM python:buster

RUN apt-get update && apt-get install -y --no-install-recommends redis-server netcat curl && rm -rf /var/lib/apt/lists/*

RUN mkdir /app && mkdir /app/bot && mkdir /app/tests

WORKDIR /app/

COPY bot/requirements.txt /app/bot
COPY tests/requirements.txt /app/tests

RUN pip3 install --no-cache-dir -r bot/requirements.txt
RUN pip3 install --no-cache-dir -r tests/requirements.txt

COPY tests/*.sh /app/
COPY bot/ /app/bot
COPY tests/ /app/tests

RUN chmod +x ./*.sh
ENTRYPOINT ["./entrypoint.sh"]
