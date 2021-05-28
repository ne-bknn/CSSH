# https://github.com/containerssh/agent
FROM containerssh/agent AS agent

# https://github.com/phusion/baseimage-docker/
FROM phusion/baseimage:bionic-1.0.0

RUN install_clean nano vim psutil

RUN set -Eeuo pipefail
CMD ["/sbin/my_init"]

COPY --from=agent /usr/bin/containerssh-agent /usr/bin/containerssh-agent
RUN mkdir /etc/service/agent
COPY cssh_agent.sh /etc/service/agent/run
RUN chmod +x /etc/service/agent/run

# checker_service should start /utils/checker
RUN mkdir /etc/service/checker
COPY checker_service.sh /etc/service/checker/run
RUN chmod +x /etc/service/checker/run

RUN useradd -m student
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /home/student
USER student
