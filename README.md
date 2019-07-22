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
 * Upload a zip file which contains all the content required to run your program in the computing clusters.

 * Zip all your executable, infiles, outfiles and jobsubmit template similar to the following directory structure. Check confinement example provided in sweepfolder. if the folder or file shown with <>, it may have any name. otherwise it must have same name as shown. 
```
. 
 ├── sweep_folder # All programs are put here. So the zip file you upload will eventually be put under this directory. 
   ├── <Application_name> # This is the application name you select; this is the folder you want to zip and upload. 
    ├── job_submit_template # Your job submit template must be just under your application name directory. 
    ├── programs # This where you will put executable and required directories. 
     ├── <executable> # Executable: can have any name. 
     ├── <infiles> # Required folder 1. 
     ├── <outfiles> # Required folder 2. 
     ├── <data> # Required folder 3.
```
 * job_submit_template must contain following format for parameter identification. 
  * Lets say you added a parameter called -R in step 02, the value for the parameter should be stated in the job script as:
    **-R USER-R-USER** 
 
### Step 04: Tab 03 (Submit jobs)
 * First thing you must see here is the connected servers with their connection name, remote path and the queue limit. Change the remote path and the maximum queue limit depending on the server policies and how much percentange you want to use.
 * Next, select the run configuration from the 'Select run cofiguration' dropdown widget. This configuration was created in the step 02 and it should have your application name followed by timestamp of the creation.
 * Then, select the staged program setup folder (using 'Program setup folder' dropdown) which you zipped and uploded in the step 03.
 * Next, you have the option to reduce the number of severs to use as well as if needed you can turn off download data as they are completing.
 * Finally, click on 
