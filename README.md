# Auto parameter sweeping
* This program allows users do parameter sweeps of a scientific simulation software or any program parallelly in several different computing clusters/resouces which they own or have access to.

## Highlighted features
* Users can define parameter ranges and/or sets and ramdomly generate different parameter configurations.
* Set queue limits for each of the server resources.
* Parallel job execution amoung as many servers you connect.
* Automatic submit of jobs as they are being completed.
* Close the program anytime and restart from where you left off.
* Automatic download of the simulation data as they are completed.
* Resource monitoring of the connected servers.
* Commandline access to the cluster resources.

## Install methods
You can install this from docker hub or github.

### Install and run
* docker build -t kadupitiya/para_sweep .
* docker run -itd -p 8181:8181 kadupitiya/para_sweep

### download and run
* docker pull kadupitiya/para_sweep
* docker run -itd -p 8181:8181 kadupitiya/para_sweep

### install and run in your linux computer
* make install
* make run

### Access on cloud
* http://apps.kadupitiya.lk/parasweep/apps/para_sweep_GUI.ipynb

## Simple use case example



