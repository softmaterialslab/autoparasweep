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
  * Lets say we have a program which has 2 input paramters; one of it is a range (3.0 to 4.0 with 0.1 step size) and other one is a set which is num of mpi nodes {4, 16}. So this would have 22 jobs if you want to sweep all possible combinations for the defined two parameters.
  * Lets assume this program is going to be executed in two cluster resources.
### Step 01:
  * 



