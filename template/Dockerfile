# Use phusion/baseimage as base image. To make your builds reproducible, make
# sure you lock down to a specific version, not to `latest`!
# See https://github.com/phusion/baseimage-docker/blob/master/Changelog.md for
# a list of version numbers.
FROM phusion/baseimage:bionic-1.0.0

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]

# ...put your own build instructions here...
RUN apt update && apt install -y python3

RUN mkdir /utils
COPY artifacts/checker.py /utils/checker.py

RUN mkdir /etc/service/checker
COPY artifacts/checker_service.sh /etc/service/checker/run
RUN chmod +x /etc/service/checker/run

RUN useradd student
RUN mkdir /home/student
RUN chown student:student /home/student

RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /home/student
USER student
