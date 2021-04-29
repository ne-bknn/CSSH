FROM python:3.7.10-slim-stretch AS build

RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes python3-venv gcc libpython3-dev && \
    python3 -m venv /venv && \
    /venv/bin/pip install --upgrade pip

COPY requirements.txt /requirements.txt
RUN /venv/bin/pip install --disable-pip-version-check -r /requirements.txt
RUN ln -s -f /usr/bin/python3 /venv/bin/python3
RUN ln -s -f /usr/bin/python  /venv/bin/python


FROM gcr.io/distroless/python3-debian10 

COPY --from=build /venv /venv
COPY bot.py config.py ui.py db.py /bot/

WORKDIR /app

ENTRYPOINT ["/venv/bin/python3", "/bot/bot.py"]
