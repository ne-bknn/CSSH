FROM debian:buster

RUN apt-get update && \
    apt-get install -y python apt-transport-https ca-certificates curl gnupg-agent software-properties-common && \
    curl -fsSL https://packages.containerssh.io/debian/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://packages.containerssh.io/debian ./" && \
    apt-get update && apt-get -y install containerssh-agent && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN useradd -m student

WORKDIR /home/student
USER student
