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
  * Lets start the auto parasweeper; it will be opened as a notebook or notebook app depending on how you ran it. 
### Step 01: Tab 01 (Connect servers)
  * First connect your servers using either the sshkey or a password.
### Step 02: Tab 02 (Setup the program)
  * First fill application name
  * Second select how many parameters invoved in your sweep. As you increase the number you will see attributes added. In our example this number is 2.
  * Next, select the attribute name which will be the actual command line argument you will use in your jobscript. If it is a range select type as range and also select increment for the range. If it is a set (which are unique values, this canbe string, int or any type), increment will be automatically disabled. For both cases fill the values text field with the values seperated with a comma.
  * Next you must select how many jobs you want to run from the inputs you had selected. If the number of jobs is greater than the max possible jobs, program would show you the max possible job number. 
  * Finally, click on the 'generate and save' button which would save your application configuration (this is what you just selected with ranges and sets), and the run configuration (this is the jobs generated from this process and saved with timestamp and application name). In the step 04 (in Tab 03) we will use this run configuration.

### Step 03: Tab 02 (Setup the program) :- Create a folder structure with staged executable
 * 



