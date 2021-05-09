# https://github.com/phusion/baseimage-docker/
FROM phusion/baseimage:bionic-1.0.0
CMD ["/sbin/my_init"]

RUN set -Eeuo pipefail

RUN apt-get update && \
    apt-get install -y python apt-transport-https ca-certificates curl gnupg-agent software-properties-common && \
    curl -fsSL https://packages.containerssh.io/debian/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://packages.containerssh.io/debian ./" && \
    apt-get update && apt-get -y install containerssh-agent

RUN mkdir /utils
COPY artifacts/checker.py /utils/checker.py

RUN mkdir /etc/service/checker
COPY artifacts/checker_service.sh /etc/service/checker/run
RUN chmod +x /etc/service/checker/run

RUN useradd -m student
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /home/student
USER student
