#!/bin/sh
exec python /utils/checker.py >> /var/log/checker.log 2>&1
