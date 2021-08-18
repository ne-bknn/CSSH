# https://github.com/containerssh/agent
FROM containerssh/agent AS agent

# https://github.com/phusion/baseimage-docker/
FROM phusion/baseimage:bionic-1.0.0

USER root

RUN install_clean nano vim python3-psutil

RUN set -eu pipefail

COPY --from=agent /usr/bin/containerssh-agent /usr/bin/containerssh-agent

# checker_service should start /utils/checker
RUN mkdir /etc/service/checker
COPY checker_service.py /etc/service/checker/run
RUN chmod +x /etc/service/checker/run

RUN useradd -m student
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /home/student
# USER student

ENTRYPOINT ["containerssh-agent", "console", "--env", "TERM=xterm-256color", "--", "/sbin/my_init", "--", "bash", "-l"]
