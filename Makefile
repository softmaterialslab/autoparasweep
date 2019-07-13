docker-start:
	docker build -t kadupitiya/para_sweep .
	docker run -itd -p 8181:8181 kadupitiya/para_sweep
	
docker-stop:
	docker stop $$(docker ps -a -q -f status=running)
	
	
docker-pull-start:
	docker pull kadupitiya/para_sweep
	docker run -itd -p 8181:8181 kadupitiya/para_sweep
	
	
install:
	pip3 install --user notebook
	pip3 install --user ipywidgets  && jupyter nbextension enable --sys-prefix --py widgetsnbextension
	pip3 install --user appmode && jupyter nbextension enable --py --sys-prefix appmode && jupyter serverextension enable --py --sys-prefix appmode
	mkdir -p ~/.jupyter/custom/                                          && \
     echo "\$('#appmode-leave').hide();" >> ~/.jupyter/custom/custom.js   && \
     echo "\$('#appmode-busy').hide();"  >> ~/.jupyter/custom/custom.js   && \
     echo "\$('#appmode-loader').append('<h2>Loading...</h2>');" >> ~/.jupyter/custom/custom.js
	 
run:
	jupyter-notebook --NotebookApp.token='' para_sweep_GUI.ipynb