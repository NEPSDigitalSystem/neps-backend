IMAGE_NAME=neps-backend
CONTAINER_NAME=neps-backend-container
PORT=8000

build:
	docker build -t $(IMAGE_NAME) .

run:
	docker run -p $(PORT):$(PORT) --name $(CONTAINER_NAME) $(IMAGE_NAME)

run-bg:
	docker run -d -p $(PORT):$(PORT) --name $(CONTAINER_NAME) $(IMAGE_NAME)

stop:
	docker stop $(CONTAINER_NAME)

remove:
	docker rm $(CONTAINER_NAME)

restart: stop remove run

logs:
	docker logs -f $(CONTAINER_NAME)

clean:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true
	docker rmi $(IMAGE_NAME) || true

install:
	pip install -r requirements.txt


.PHONY: makemigrations migrate


makemigrations:
	alembic revision --autogenerate -m "$(m)"

migrate:
	alembic upgrade head