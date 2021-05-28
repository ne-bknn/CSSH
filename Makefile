.PHONY: test
test:
	docker build -t "dummy" -f images/dummy/Dockerfile images/dummy
	docker-compose -f docker-compose-tests.yml up --build --abort-on-container-exit
