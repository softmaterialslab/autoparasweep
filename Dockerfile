FROM ubuntu:rolling
USER root

MAINTAINER Kadupitiya kadupitige <kadupitiya@kadupitiya.lk>

# Install some Debian package
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-setuptools     \
    python3-wheel          \
    python3-pip            \
    less                  \
    nano                  \
    sudo                  \
    git                   \
    npm                   \
  && rm -rf /var/lib/apt/lists/*

	
# install Jupyter via pip
RUN pip3 install notebook

# install ipywidgets
RUN pip3 install ipywidgets  && \
    jupyter nbextension enable --sys-prefix --py widgetsnbextension

# install Appmode
RUN pip3 install appmode && \
    jupyter nbextension     enable --py --sys-prefix appmode && \
    jupyter serverextension enable --py --sys-prefix appmode

# Possible Customizations
RUN mkdir -p ~/.jupyter/custom/                                          && \
     echo "\$('#appmode-leave').hide();" >> ~/.jupyter/custom/custom.js   && \
     echo "\$('#appmode-busy').hide();"  >> ~/.jupyter/custom/custom.js   && \
     echo "\$('#appmode-loader').append('<h2>Loading...</h2>');" >> ~/.jupyter/custom/custom.js


# Copy required files
COPY . /usr/src/app
WORKDIR /usr/src/app
#RUN ls -la

# install python libs
RUN pip3 install -r requirements.txt

# Launch Notebook server
EXPOSE 8181
CMD ["jupyter-notebook", "--ip=0.0.0.0", "--port=8181", "--allow-root", "--no-browser", "--NotebookApp.token=''", "para_sweep_GUI.ipynb"]
