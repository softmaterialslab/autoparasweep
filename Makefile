docker-start:
	docker build -t kadupitiya/para_sweep .
	docker run -itd -p 8181:8181 kadupitiya/para_sweep
	
docker-stop:
	docker stop $$(docker ps -a -q -f status=running)