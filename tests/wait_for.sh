#!/bin/bash

set -Eeuo pipefail

until timeout 3 redis-cli -u redis://redis ping  &> /dev/null; do
	echo "Waiting for redis..."
	sleep 2
done
echo "Redis is reachable"

until timeout 3 curl -Is http://authconfig:6823 &> /dev/null; do
	echo "Waiting for authconfig..."
	sleep 2
done
echo "Authconfig server is reachable"

until timeout 3 head -n 1 < /dev/tcp/containerssh/2222 | grep -q "SSH"; do
	echo "Waiting for SSH..."
	sleep 2
done
echo "SSH is reachable"
