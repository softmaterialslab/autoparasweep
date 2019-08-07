import matplotlib.pyplot as plt
#plt.style.use('ggplot')
import ipywidgets as widgets
import sys, os, io, string, shutil, math
import numpy as np
import re
import time
import threading
from threading import Thread
from io import StringIO
from ipywidgets import Layout, Box, Label, Output
from IPython.display import display,HTML
#sys.path.append('../python/')
#import train as nn
import random
import datetime
#from IPython.core.display import display, HTML
style = {'description_width': 'initial'}
# % is single line magic
# %% is magic cell
#!pip install jupyter_dashboards
#!jupyter dashboards quick-setup --sys-prefix
import glob, json
from codes.SSH import SSH
from codes.BagOfJobs import BagOfJobs

class ServerAttributes:
    def __init__(self, cluster_name='kadu@bigred2.uits.iu.edu', remote_path = '/N/dc2/scratch/kadu/', max_job_per_server=500, ssh_connection = None ):
        
        self.cluster_name = widgets.Text(
            value=cluster_name,
            description='SSH Con: ',
            disabled=True,
            style=style,
        )
            
        self.remote_path = widgets.Text(
            value=remote_path,
            description='Remote Path: ',
            style=style,
        )
  
        self.max_job_per_server = widgets.BoundedIntText(
                value=max_job_per_server,
                min=1,
                max=500,
                step=1,
                description='Maximum Job limit: ',
                style=style,
            )
    
        self.ssh_connection=ssh_connection
        
        self.server_progress = None
    
        self.attributes_widgets = widgets.HBox([self.cluster_name, self.remote_path, self.max_job_per_server])

class ServerProgressAttributes:
    def __init__(self, cluster_name='kadu@bigred2.uits.iu.edu', running_jobs=0, queued_jobs = 0, completed_jobs = 0 ):
        
        group_area_layout=Layout(
            display='flex',
            border='solid 1px',
            align_items='stretch',
            padding='5px',
            width='100%'
            )
        
        self.cluster_name = widgets.Text(
            value=cluster_name,
            description='Server: ',
            disabled=True,
            style=style,
        )
            
        self.running_jobs = widgets.BoundedIntText(
            value=running_jobs,
            description='Running: ',
            step=1,
            max=100000,
            disabled=True,
            style=style,
        )
  
        self.queued_jobs = widgets.BoundedIntText(
                value=queued_jobs,
                step=1,
                max=100000,
                description='Queued: ',
                disabled=True,
                style=style,
            )
    
        self.completed_jobs = widgets.BoundedIntText(
                value=completed_jobs,
                step=1,
                max=100000,
                description='Completed: ',
                disabled=True,
                style=style,
            )
        
        self.text_area_server_logs =  widgets.Textarea(
            value='',
            placeholder='',
            disabled=True,
            layout=Layout(flex='0 1 auto', height='100px', min_height='100px', width='100%')
        )
        
        self.text_area_server_logs_widgets = widgets.HBox([self.text_area_server_logs])
    
        self.attributes_widgets_first = widgets.HBox([self.cluster_name, self.running_jobs, self.queued_jobs, self.completed_jobs])
        
        self.attributes_widgets = widgets.VBox([self.attributes_widgets_first, self.text_area_server_logs_widgets] , layout = group_area_layout)
        
    
class Job_Handler:
    def __init__(self, ssh_manager = None):
        
        self.lock = threading.RLock()
        
        self.ssh_manager = ssh_manager
        
        self.run_servers = True

        self.server_threads = []
        
        self.executable_name = ''
        self.executable_folder = 'program'
        self.job_submission_template = 'job_submit_template'
        self.job_submit_cmd = 'qsub'
        self.sweep_folder = 'sim_runs'
        
        self.queue_check_interval = 30
        self.queue_job_submit_interval = 4
        
        group_area_layout=Layout(
            display='flex',
            border='solid 1px',
            align_items='stretch',
            padding='5px',
            width='100%'
            )
        
        self.ssh_attributes_widgets = widgets.VBox(layout=group_area_layout)
        
        
        self.pending_job_runs = widgets.Dropdown(
            options=['None'],
            value='None',
            description='Select run cofiguration: ',
            style=style,
            layout=Layout(flex='0 1 auto', width='35%')
        )
        
        self.pending_job_runs.observe(self.onValueChangePendingJobs,'value') 
        
        #self.load_btn.on_click(self.onclick_coonect_btn)
        
        self.load_job_config_att = widgets.HBox([self.pending_job_runs])
        
        #self.local_path = widgets.Text(
        #    value='sweep_folder/confinement',
        #    description='Program setup folder: ',
        #    style=style,
        #)

        self.local_path = widgets.Dropdown(
            options=['None'],
            value='None',
            description='Program setup folder: ',
            style=style,
            layout=Layout(flex='0 1 auto', width='35%')
        )

        
        self.servers_to_use = widgets.BoundedIntText(
                value=1,
                min=0,
                max=100,
                step=1,
                description='Number of servers to use : ',
                style=style,
        )
        
        self.run_btn = widgets.Button(description='Run')

        self.download_all_check = widgets.Checkbox(value=True, description='Download data as completing', disabled=False)
        
        self.run_details_widgets = widgets.HBox([self.local_path, self.servers_to_use, self.run_btn, self.download_all_check])
        
        self.sweep_config_widgets = widgets.VBox([self.load_job_config_att, self.run_details_widgets], layout=group_area_layout)
    
        self.refresh_ssh_con_btn = widgets.Button(description='Refresh Connections')
        
        self.refresh_widget = widgets.HBox([self.refresh_ssh_con_btn])
        
        self.refresh_ssh_con_btn.on_click(self.refresh_ssh_con_btn_click)
        
        self.text_area_job_run_logs =  widgets.Textarea(
            value='',
            placeholder='',
            disabled=True,
            layout=Layout(flex='0 1 auto', height='100px', min_height='100px', width='100%')
        )
        
        self.server_monitor_widgets = widgets.VBox(layout=group_area_layout)
        
        self.progress_bar = widgets.FloatProgress(
            value=0.0,
            min=0,
            max=100.0,
            step=0.1,
            description='Job completion:',
            bar_style='info',
            orientation='horizontal',
            style=style,
            layout=Layout(flex='0 1 auto', width='80%')
        )
        
        self.progress_value = widgets.Text(
            value='',
            description='Completed/Total:',
            disabled=True,
            style=style,
            layout=Layout(flex='0 1 auto', width='20%')
        )
        
        #self.progress_bar.style.width = '100%'
        
        self.progress_widget = widgets.HBox([self.progress_bar, self.progress_value])
        #self.progress_widget.layout.width = '100%'
    
        self.textlog_widget = widgets.HBox([ self.text_area_job_run_logs])   
        
        #self.refresh_widget, 
        self.wigetbox = widgets.VBox([self.refresh_widget, self.ssh_attributes_widgets, self.sweep_config_widgets, self.server_monitor_widgets, self.progress_widget, self.textlog_widget] , layout = group_area_layout)
            
        self.populate_job__drop()    
        self.refresh_ssh_manager(self.ssh_manager)
        
        self.run_btn.on_click(self.run_btn_on_click)
            
    def refresh_ssh_manager(self, ssh_manager = None):
        self.populate_job__drop()
        if not self.server_threads:
            if ssh_manager:
                self.ssh_manager = ssh_manager
                self.ssh_attributes = []
                self.ssh_attributes_widgets_items = []
                if self.ssh_manager.ssh_connections:
                    self.active_ssh_cons = 0
                    for con in self.ssh_manager.ssh_connections:
                        if con.ssh:
                            cluster_name_T = con.username.value +'@'+ con.hostname.value 
                            remote_path = '/N/dc2/scratch/'+con.username.value+'/'
                            self.ssh_attributes.append(ServerAttributes(cluster_name=cluster_name_T, remote_path = remote_path , max_job_per_server=500, ssh_connection= con))
                            self.ssh_attributes_widgets_items.append(self.ssh_attributes[-1].attributes_widgets)
                            self.active_ssh_cons += 1
                    self.servers_to_use.value = self.active_ssh_cons
                    if self.active_ssh_cons > 0:
                        self.servers_to_use.min = 1
                        self.servers_to_use.max = self.active_ssh_cons
                        self.enable_all()
                    else:
                        self.disable_all() 
                        self.text_area_job_run_logs.value += 'No active SSH connections were found. Please add SSH connection in SSH Manager tab to enable Run Jobs. \n'
                    self.ssh_attributes_widgets.children = self.ssh_attributes_widgets_items
        else:
            self.text_area_job_run_logs.value += 'There is an active job execution, therefor resetting ssh connections aborted. \n'        
        
    def refresh_ssh_con_btn_click(self, change):
        self.refresh_ssh_manager(self.ssh_manager)
        #self.ssh_attributes_widgets.children = []

        
    def populate_job__drop(self):
        self.all_configs = glob.glob("run-config/*.json")
        self.pending_job_runs.options = ['None']+ [ item.replace("\\", "/").split('/')[-1].split('.')[0] for item in self.all_configs]

        self.all_run_configs = glob.glob("sweep_folder/*")
        self.local_path.options = ['None']+ [ item for item in self.all_run_configs]


    def onValueChangePendingJobs(self, change):
        try:
            if not change.new == 'None':
                self.enable_all()
                file_name = change.new + '.json'
                self.selected_config_file = change.new
                file_path = os.path.join('run-config', file_name)         
                with open(file_path) as json_file:
                    self.generated_job_dic = json.load(json_file)
                    self.generated_job_dic['total_size_of_bag_of_jobs'] = len(self.generated_job_dic['bag_of_jobs'])
                    self.local_path.disabled = False
                    if self.generated_job_dic['run_index'] == None:
                        self.generated_job_dic['run_index'] = 0
                        self.generated_job_dic['completion_index'] = 0
                        self.update_config()
                        self.run_btn.disabled =False
                        self.run_btn.description='Run'
                    elif self.generated_job_dic['run_index'] == 0:
                        self.run_btn.disabled =False
                        self.run_btn.description='Run'
                    elif self.generated_job_dic['total_size_of_bag_of_jobs'] == self.generated_job_dic['completion_index']:
                        self.run_btn.disabled =False
                        self.run_btn.description='load'
                    elif self.generated_job_dic['total_size_of_bag_of_jobs'] > self.generated_job_dic['completion_index']:
                        self.run_btn.disabled =False
                        self.run_btn.description='Resume'
                        
                    self.text_area_job_run_logs.value += 'Job config loaded, bag of job size {} \n'.format(self.generated_job_dic['total_size_of_bag_of_jobs'])
                    self.text_area_job_run_logs.value += 'Number of jobs executed {} \n'.format(self.generated_job_dic['run_index'])
                        
        except Exception as e: print(e) 
               
    def update_config(self):
        try:
            file_path = os.path.join('run-config', self.selected_config_file+".json")
            with open(file_path, 'w') as json_file:
                json.dump(self.generated_job_dic, json_file)
                
        except Exception as e: print(e) 
            
    def disable_all(self):
        try:
            self.run_btn.disabled=True
            self.servers_to_use.disabled=True
            self.pending_job_runs.disabled=True
            self.download_all_check.disabled = True
                
        except Exception as e: print(e)  

    def enable_all(self):
        try:
            self.run_btn.disabled=False
            self.servers_to_use.disabled=False
            self.pending_job_runs.disabled=False
            self.download_all_check.disabled = False
            
            self.reset_all()
                
        except Exception as e: print(e)
            
            
    def reset_all(self):
        try:  
            self.ssh_monitor_attributes = []
            
        except Exception as e: print(e)            
  
    def reset_monitor_widget(self):
        try:  
            self.progress_bar.value=0.0
            self.progress_value.value=''
            self.text_area_job_run_logs.value=''
            self.ssh_monitor_attributes_widgets_items = []
            self.server_monitor_widgets.children = self.ssh_monitor_attributes_widgets_items 
            
        except Exception as e: print(e)         
            
    def run_btn_on_click(self, change):
        try:
            if self.local_path.value != 'None':
                if self.run_btn.description!='New Config':
                    if self.pending_job_runs.value != 'None':
                        if self.validate_job():
                            self.text_area_job_run_logs.value += 'Job submit template validation successful \n'
                            self.pending_job_runs.disabled=True
                            if self.generated_job_dic['run_index'] == 0:
                                self.run_btn.description='Running'
                                self.run_btn.disabled =True
                                self.download_all_check.disabled = True
                                self.new_job_execution()
                            else:
                                self.run_btn.disabled =True
                                self.download_all_check.disabled = True
                                self.resume_job_execution()
                        else:
                            self.text_area_job_run_logs.value += 'Job submit template validation failed, make sure you have {} file, and executable in {} folder \n'.format(self.job_submission_template, self.executable_folder)
                    else:
                        self.text_area_job_run_logs.value += 'Please first select run configuration. \n'
                else:
                    #new congig while executing
                    self.run_btn.disabled=True
                    self.stop_all_threads()
                    self.pending_job_runs.disabled=False
            else:
                self.text_area_job_run_logs.value += 'Please first select program setup folder. \n'

        except Exception as e: print(e)  

    def stop_all_threads(self):
        try:
            
            self.text_area_job_run_logs.value += 'Stoping all running threads, reselect the config file to continue. \n'
            self.run_servers = False
            for thread_item in self.server_threads:
                name__ = thread_item.name.split()
                self.text_area_job_run_logs.value += 'Stoping {}: {}... \n'.format(name__[0], name__ [-1])
                thread_item.join()
                self.text_area_job_run_logs.value += '{}: {} stopped \n'.format(name__[0], name__ [-1])
            
            self.server_threads = []

            self.reset_monitor_widget()
            self.enable_all()

 
        except Exception as e: print(e)  
            
            
    def validate_job(self):
        try:
            file_path_job = os.path.join(self.local_path.value, self.job_submission_template) 
            job_submit_path= glob.glob(file_path_job)
            if job_submit_path:
                self.text_area_job_run_logs.value += '{} file found in local path folder:{} \n'.format(self.job_submission_template, self.local_path.value)
                file_path_program = os.path.join(self.local_path.value, self.executable_folder)
                program_path= glob.glob(file_path_program)
                if program_path:
                    self.text_area_job_run_logs.value += '{} folder found in local path folder:{} \n'.format(self.executable_folder, self.local_path.value)
                    file_path_program_exe = os.path.join(file_path_program, "*")
                    program_path_exe= glob.glob(file_path_program_exe)
                    if program_path_exe:
                        self.exe_count = 0;
                        for item in program_path_exe:
                            if os.path.isfile(item) :
                                self.executable_name = item.replace("\\", "/").split('/')[-1]
                                self.text_area_job_run_logs.value += '{} is recognized as the executable \n'.format(self.executable_name)
                                self.exe_count += 1
                            else:
                                self.text_area_job_run_logs.value += '{} found in local path folder:{} recongized as a folder required for executable.\n'.format(item, file_path_program_exe)
                            if self.exe_count >1:
                                self.text_area_job_run_logs.value += 'You can only have one entry point executable in {} folder but more than 1 found.\n'.format(file_path_program_exe)
                                return False
                        if self.exe_count !=1:
                            self.text_area_job_run_logs.value += 'No executables found in {} folder.\n'.format(file_path_program_exe)
                            return False
                        self.text_area_job_run_logs.value += 'Make sure that above files and folders are be able to run standalone in your server. \n'
                        return True
                    else:
                        self.text_area_job_run_logs.value += 'Local path folder:{}, must have executable files... \n'.format(file_path_program_exe)
                        return False    
                else:
                    self.text_area_job_run_logs.value += 'Local path folder:{}, must have {} folder \n'.format(self.local_path.value)
                    return False    
            else:
                self.text_area_job_run_logs.value += 'Local path folder:{}, must have {} file \n'.format(self.job_submission_template, self.local_path.value)
                return False
        except Exception as e: print(e)
            
    def new_job_execution(self):
        try:
            self.text_area_job_run_logs.value += 'Starting a server stage for the executable. \n'

            self.generated_job_dic['download_all_check'] = self.download_all_check.value

            if self.stage_server_with_program(self.ssh_attributes[:self.servers_to_use.value]):
                
                self.text_area_job_run_logs.value += 'Starting a new job execution. \n'
 
                self.server_threads = []
                
                for connection_ in self.ssh_attributes[:self.servers_to_use.value]:
                    #self.text_area_job_run_logs.value += connection_.cluster_name.value+' \n'
                    #print(connection_.cluster_name.value)
                    thread = Thread(name=connection_.cluster_name.value, target=self.run_jobs_begin, args=(connection_,))
                    self.server_threads.append(thread)
                    self.server_threads[-1].start()    
 
            else:
                self.run_btn.disabled=False
                self.local_path.disabled = False
                self.pending_job_runs.disabled=False
                self.text_area_job_run_logs.value += 'Execution aborted. \n'
            
            

        except Exception as e: print(e)        

    def resume_job_execution(self):
        try:
            self.text_area_job_run_logs.value += 'Checking job resume posibility. \n'

            self.download_all_check.value = self.generated_job_dic['download_all_check']
            
            if self.load_server_details_from_config(self.ssh_attributes[:self.servers_to_use.value]):
                
                self.text_area_job_run_logs.value += 'Resuming the job execution. \n'
 
                self.server_threads = []
                
                for connection_ in self.ssh_attributes[:self.servers_to_use.value]:
                    #self.text_area_job_run_logs.value += connection_.cluster_name.value+' \n'
                    #print(connection_.cluster_name.value)
                    thread = Thread(name=connection_.cluster_name.value, target=self.run_jobs_begin, args=(connection_,))
                    self.server_threads.append(thread)
                    self.server_threads[-1].start()
 
            else:
                self.run_btn.disabled=False
                self.local_path.disabled = False
                self.pending_job_runs.disabled=False
                self.text_area_job_run_logs.value += 'Execution aborted. \n'
        
        except Exception as e: print(e)

    def set_total_progress(self, completion_index, total_jobs):
        self.progress_bar.value = completion_index/total_jobs * 100.0
        self.progress_value.value = str(completion_index)+' / '+str(total_jobs)

            
    def run_jobs_begin(self, ssh_server):   
        try:
            ssh_server.ssh_monitor_attributes = self.get_monitor_pannel(ssh_server)
            
            self.run_servers = True
            
            while self.run_servers:
                
                sleep_var = False
                
                with self.lock:
                    #check queue size every iteration
                    queued_jobs = self.get_queue_size(ssh_server, 'Q')
                    running_jobs = self.get_queue_size(ssh_server, 'R')
                    ssh_server.ssh_monitor_attributes.text_area_server_logs.value = self.get_qstat_all(ssh_server)


                    server_name = ssh_server.cluster_name.value
                    self.generated_job_dic['used_servers'][server_name]['queued_jobs'] = queued_jobs
                    completed_jobs = self.generated_job_dic['used_servers'][server_name]['completed_jobs']
                    submitted_jobs = self.generated_job_dic['used_servers'][server_name]['submitted_jobs']
                    self.generated_job_dic['used_servers'][server_name]['running_jobs'] = running_jobs
                    total_jobs = self.generated_job_dic['total_size_of_bag_of_jobs']
                    run_index = self.generated_job_dic['run_index']
                    completion_index = self.generated_job_dic['completion_index']
                    max_job_per_server = self.generated_job_dic['used_servers'][server_name]['max_job_per_server']

                    #Update all job info
                    ssh_server.ssh_monitor_attributes.running_jobs.value = running_jobs

                    ssh_server.ssh_monitor_attributes.queued_jobs.value = queued_jobs 

                    ssh_server.ssh_monitor_attributes.completed_jobs.value = completed_jobs

                    # monitor the server and get how many jobs are completed
                    #-----------------------------------------------------------
                    self.set_total_progress(completion_index, total_jobs)

                    if completion_index >= total_jobs:
                        #print('Came Gen Completed: '+server_name)
                        #This is ultimate exit
                        self.run_servers = False
                        self.progress_bar.value = 100.0
                        self.text_area_job_run_logs.value += 'All jobs are completed.\n'
                        self.run_btn.description='Completed'
                        self.pending_job_runs.disabled=False
                        sleep_var = False
                        break
                
                
                    if (queued_jobs + running_jobs) < max_job_per_server and  run_index < total_jobs:
                        # This is where we still want to submit jobs
                        #print('Came Gen Job exe: '+server_name)
                        root_path = self.generated_job_dic['used_servers'][server_name]['root_path']
                        executable_folder = self.generated_job_dic['used_servers'][server_name]['executable_folder_path']
                        sweep_folder_path = self.generated_job_dic['used_servers'][server_name]['sweep_folder_path']
                        job = self.generated_job_dic['bag_of_jobs'][run_index]

                        jobID = self.run_a_job(root_path, executable_folder, sweep_folder_path, ssh_server, job)

                        self.generated_job_dic['run_index'] += 1
                        job_ = {}
                        job_['parameters'] = job
                        job_['status'] = 'S'
                        job_['jobID'] = jobID
                        job_['submit_time'] = str(datetime.datetime.now())
                        job_['queue_time'] = str(datetime.datetime.now())
                        job_['start_time'] = ''
                        job_['end_time'] = ''

                        self.generated_job_dic['used_servers'][server_name]['bag_of_jobs_executed'][jobID] = job_
                        self.generated_job_dic['used_servers'][server_name]['submitted_jobs'] += 1
                            
                        sleep_var = False

                    else:

                        #print('Came Gen ELSE block: '+server_name)
                        self.update_job_status(ssh_server)
                        sleep_var = True
                        
                    self.update_config()
            
                if sleep_var:
                    self.run_btn.disabled=False
                    self.run_btn.description='New Config'
                    time.sleep(self.queue_check_interval)
                else:
                    time.sleep(self.queue_job_submit_interval)

        except Exception as e: print(e)

    def update_job_status(self, ssh_server):
        try:
            server_name = ssh_server.cluster_name.value
            
            for job_id in self.generated_job_dic['used_servers'][server_name]['bag_of_jobs_executed']:
                
                previous_job_status = self.generated_job_dic['used_servers'][server_name]['bag_of_jobs_executed'][job_id]['status']
                
                if previous_job_status != 'C':
                
                    job_status = self.get_job_infor(ssh_server, job_id)

                    #print(job_status)
                    if previous_job_status != 'C' and job_status == 'C':
                    
                        # downloading data
                        if self.generated_job_dic['download_all_check']:

                            self.text_area_job_run_logs.value += 'Downloading job ({}) data on {} \n'.format(job_id, ssh_server.cluster_name.value)
                            
                            local_path = self.generated_job_dic['used_servers'][server_name]['local_path']
                            local_sweep_path = os.path.join(local_path, self.sweep_folder).replace("\\", "/")

                            # creating run folder
                            if not os.path.exists(local_sweep_path):
                                os.makedirs(local_sweep_path)

                            job_paras = self.generated_job_dic['used_servers'][server_name]['bag_of_jobs_executed'][job_id]['parameters']
                            dir_name = job_paras.strip().replace(" ", "_").replace("-", "") 
                            local_job_dir_path = os.path.join(local_sweep_path, dir_name).replace("\\", "/")
                            
                            # creating job dir in local path
                            if not os.path.exists(local_job_dir_path):
                                os.makedirs(local_job_dir_path)
                            

                            sweep_folder_path = self.generated_job_dic['used_servers'][server_name]['sweep_folder_path']
                            job_dir = os.path.join(sweep_folder_path, dir_name, "").replace("\\", "/")
                            # Additing additional forward slash
                            local_job_dir_path = os.path.join(local_job_dir_path, "").replace("\\", "/")

                            ssh_server.ssh_connection.ssh.get_all_files(job_dir, local_job_dir_path)
                            self.text_area_job_run_logs.value += 'Job dir {} downloaded.\n'.format(dir_name) 

                        #If download successful update the indexes
                        self.generated_job_dic['completion_index'] += 1
                        self.set_total_progress(self.generated_job_dic['completion_index'], self.generated_job_dic['total_size_of_bag_of_jobs'])
                        self.generated_job_dic['used_servers'][server_name]['completed_jobs'] += 1
                        ssh_server.ssh_monitor_attributes.completed_jobs.value = self.generated_job_dic['used_servers'][server_name]['completed_jobs']

                        self.generated_job_dic['used_servers'][server_name]['bag_of_jobs_executed'][job_id]['end_time'] = str(datetime.datetime.now())

                    elif previous_job_status != 'R' and job_status == 'R':
                        self.generated_job_dic['used_servers'][server_name]['bag_of_jobs_executed'][job_id]['start_time'] = str(datetime.datetime.now())
                        
                    self.generated_job_dic['used_servers'][server_name]['bag_of_jobs_executed'][job_id]['status'] = job_status
                    
        except Exception as e: print(e)
            
    def run_a_job(self, root_path, executable_folder, sweep_folder_path, ssh_connection, job):
        try:
            jobID = ''
            # Make a new folder for parasweep
            dir_name = job.strip().replace(" ", "_").replace("-", "")    
            job_dir = os.path.join(sweep_folder_path, dir_name).replace("\\", "/")
            cmd = 'cp -a '+ os.path.join(root_path, executable_folder, '').replace("\\", "/") + ' ' + job_dir
            (std_out_st, std_error_st) = ssh_connection.ssh_connection.ssh.execute_command(cmd)
            
            # Copy job submission pbs
            job_script_name = os.path.join(job_dir, dir_name).replace("\\", "/")

            job_para_array = job.split()

            #This is hardcode for shapes issue: Add D para if it is shapes
            if 'shapes' in sweep_folder_path:
                if '-R' in job_para_array:
                    r_value = job_para_array[job_para_array.index('-R')+1]
                    if str(r_value) == '10':
                        job_para_array.append('-D')
                        job_para_array.append('8')
                    elif str(r_value) == '15':
                        job_para_array.append('-D')
                        job_para_array.append('12')
                    elif str(r_value) == '20':
                        job_para_array.append('-D')
                        job_para_array.append('18')

            # this is much better replace all parameters as they found
            paramter_string_rep = ""
            for i in range(0, len(job_para_array), 2):
                paramter_string_rep +=  " | sed -e 's/USER"+job_para_array[i]+"-USER/''"+job_para_array[i+1]+ "''/g'"
            paramter_string_rep += " | sed -e 's/ jobName/'' "+ dir_name+"''/g' > "

            cmd = "cat " + os.path.join(root_path, self.job_submission_template).replace("\\", "/") + paramter_string_rep + job_script_name
            (std_out_st, std_error_st) = ssh_connection.ssh_connection.ssh.execute_command(cmd)

            # qsub the job
            cmd = 'cd ' + job_dir + ' && ' + self.job_submit_cmd + ' ' + job_script_name
            self.text_area_job_run_logs.value += 'Job {} is submitting on {} ...\n'.format(dir_name, ssh_connection.cluster_name.value)
            (std_out_st, std_error_st) = ssh_connection.ssh_connection.ssh.execute_command(cmd)

            try:
                jobID = std_out_st.split()[0]
                self.text_area_job_run_logs.value += 'Job Submitted with ID : {} \n'.format(jobID)
            except:
                jobID = "Error"
                self.text_area_job_run_logs.value += 'Job Submit failed, something is wrong with job submission. Check your jobsubmit file in the folder \n'
                self.text_area_job_run_logs.value += std_error_st
                pass
                
            
            return jobID
            
        except Exception as e: print(e)

    def get_queue_size(self, ssh_connection, keyword):
        try:
            number_of_jobs = 0
            username_ = ssh_connection.cluster_name.value.split('@')[0]
            #This is an example command for two logic if: cmd = "qstat -u kadu | awk '{if (($10==\"alloc\") || ($5==\"idle\")) sum += $4} END {print sum}'"
            # Following two are two other ways to get the amount queued.
            #cmd = "qselect -s Q -u kadu | wc -l"
            #cmd = "qselect -s Q -u kadu | awk '{sum += 1} END {print sum}'"
            # This is the complex one but most useful and customizable: tail -n +6 removes header lines
            # $10 refers to 10th column
            cmd =  "qstat -u {} | tail -n +6 | awk '{{if ($10==\"{}\") sum += 1}} END {{print sum}}'".format(username_, keyword)
            (std_out_st, std_error_st) = ssh_connection.ssh_connection.ssh.execute_command(cmd)
            try:
                digit = std_out_st.split()[0]
                if digit.isdigit():
                    number_of_jobs = int(digit)
            except:
                pass
            
            self.text_area_job_run_logs.value += 'Queue status of {} is {} : {} \n'.format(ssh_connection.cluster_name.value, keyword, number_of_jobs)
            
            return number_of_jobs
            
        except Exception as e: print(e)
            
    def get_job_infor(self, ssh_connection, job_id):
        try:
            job_status = 'C'
            
            username_ = ssh_connection.cluster_name.value.split('@')[0]
            cmd =  "qstat -u {} {} | tail -n +6 | awk '{{print $10}}'".format(username_, job_id)
            #print(cmd)
            (std_out_st, std_error_st) = ssh_connection.ssh_connection.ssh.execute_command(cmd)
            try:
                job_status = std_out_st.split()[0]
                if not job_status:
                    job_status = 'C'
            except:
                pass
            
            return job_status
            
        except Exception as e: print(e)  
            
    def get_qstat_all(self, ssh_connection):
        try:
            username_ = ssh_connection.cluster_name.value.split('@')[0]
            cmd =  "qstat -u {} | tail -n +4".format(username_)
            (std_out_st, std_error_st) = ssh_connection.ssh_connection.ssh.execute_command(cmd)
        
            return std_out_st
            
        except Exception as e: print(e)
            
    def stage_server_with_program(self, ssh_con):
        return_boolean = True
        try:
            self.generated_job_dic['used_servers'] = {}
            # copy executable, infiles, outfiles, and job template, etc    
            for connection_ in ssh_con:
                server_ = {}
                self.text_area_job_run_logs.value += 'Staging program on {} \n'.format(connection_.cluster_name.value)
                server_['server_name'] = connection_.cluster_name.value
                local_path = self.local_path.value
                server_['local_path'] = local_path
                server_['max_job_per_server'] =  connection_.max_job_per_server.value
                remote_path = connection_.remote_path.value
                server_['remote_path'] = remote_path
                __base_dir = os.path.split(local_path)[1]
                server_['__base_dir'] = __base_dir
                root_path = os.path.join(remote_path, __base_dir).replace("\\", "/")
                server_['root_path'] = root_path
                connection_.ssh_connection.ssh.put_all_files(local_path, remote_path)
                self.text_area_job_run_logs.value += 'Program copied.\n'
                # Change the permission of the executable
                executable_folder_path = os.path.join(root_path, self.executable_folder).replace("\\", "/")
                executable_path = os.path.join(executable_folder_path, self.executable_name).replace("\\", "/")
                server_['executable_folder_path'] = executable_folder_path
                server_['executable_path'] = executable_path
                cmd = 'chmod +x ' + executable_path
                (std_out_st, std_error_st) = connection_.ssh_connection.ssh.execute_command(cmd)
                self.text_area_job_run_logs.value += 'Executable permision changed to +x \n'
                # Make a new folder for parasweep
                sweep_folder_path = os.path.join(root_path, self.sweep_folder).replace("\\", "/")
                server_['sweep_folder_path'] = sweep_folder_path
                server_['running_jobs'] = 0
                server_['queued_jobs'] = 0
                server_['submitted_jobs'] = 0
                server_['completed_jobs'] = 0
                server_['bag_of_jobs_executed'] = {}   
                #disable all the fieilds
                connection_.cluster_name.disabled = True     
                self.local_path.disabled = True     
                connection_.max_job_per_server.disabled = True     
                connection_.remote_path.disabled = True
                
                try:
                    connection_.ssh_connection.ssh.sftp.mkdir(sweep_folder_path)
                    self.text_area_job_run_logs.value += '{} folder created.\n'.format(sweep_folder_path)
                except:
                    pass

                #Making sure only one username+sever combo
                if not server_['server_name'] in self.generated_job_dic['used_servers']:
                    self.generated_job_dic['used_servers'][server_['server_name']] = server_
                    self.update_config()
                    self.add_server_monitor(ssh_con)
                 
                else:
                    self.text_area_job_run_logs.value += 'Program cant use same server two times with same user.\n'
                    return_boolean = False
                    return return_boolean

        except Exception as e: 
            print(e)
            return_boolean = False
        return return_boolean
 
    def load_server_details_from_config(self, ssh_con):
        return_boolean = True
        try:
            self.generated_job_dic['used_servers']
            # copy executable, infiles, outfiles, and job template, etc  
            servers_used = len(self.generated_job_dic['used_servers'])
            servers_active = len(ssh_con)
            server_string__active = []
            server_string__found = list(self.generated_job_dic['used_servers'].keys())
            if servers_used == servers_active:
                for connection_ in ssh_con:
                    #Making sure all the servers used are active
                    if connection_.cluster_name.value in self.generated_job_dic['used_servers']:
                        server_string__active.append(connection_.cluster_name.value)
                        server_ = self.generated_job_dic['used_servers'][connection_.cluster_name.value]
                        self.text_area_job_run_logs.value += 'Restaging program on {} \n'.format(connection_.cluster_name.value)
                        connection_.cluster_name.value = server_['server_name']
                        connection_.cluster_name.disabled = True
                        local_path = self.local_path.value = server_['local_path']
                        self.local_path.disabled = True
                        connection_.max_job_per_server.value= server_['max_job_per_server']
                        connection_.max_job_per_server.disabled = True
                        remote_path = connection_.remote_path.value = server_['remote_path'] 
                        connection_.remote_path.disabled = True
                        __base_dir = os.path.split(local_path)[1]
                        root_path = os.path.join(remote_path, __base_dir).replace("\\", "/")

                        # If job is completed dont bother
                        if self.generated_job_dic['total_size_of_bag_of_jobs'] != self.generated_job_dic['completion_index']:
                            connection_.ssh_connection.ssh.put_all_files(local_path, remote_path)
                            self.text_area_job_run_logs.value += 'Program recopied.\n'
                            # Change the permission of the executable
                            executable_folder_path = os.path.join(root_path, self.executable_folder).replace("\\", "/")
                            executable_path = os.path.join(executable_folder_path, self.executable_name).replace("\\", "/")
                            cmd = 'chmod +x ' + executable_path
                            (std_out_st, std_error_st) = connection_.ssh_connection.ssh.execute_command(cmd)
                            self.text_area_job_run_logs.value += 'Executable permision changed to +x \n'
                            # Make a new folder for parasweep
                            sweep_folder_path = os.path.join(root_path, self.sweep_folder).replace("\\", "/") 

                            try:
                                connection_.ssh_connection.ssh.sftp.mkdir(sweep_folder_path)
                                self.text_area_job_run_logs.value += '{} folder created if not exists.\n'.format(sweep_folder_path)
                            except:
                                pass

                        self.add_server_monitor(ssh_con)

                    else:
                        self.text_area_job_run_logs.value += '{} is not connected, it is required to resume the job.\n'.format(connection_.cluster_name.value)
                        return False
                
                            
                if set(server_string__active) != set(server_string__found):
                    self.text_area_job_run_logs.value += 'Please makesure all the servers used ({}) are connected ({}).\n'.format(server_string__found, server_string__active)
                    return False
                    
            else:
                self.text_area_job_run_logs.value += 'Numer of servers previously used({}), must be the same savers connected right now ({})\n'.format(servers_used, servers_active)
                return False    
        except Exception as e: 
            print(e)
            return_boolean = False
            
        return return_boolean


    def add_server_monitor(self, ssh_con):
        try:
            #self.text_area_job_run_logs.value += 'Adding server monitoring. \n'
            self.ssh_monitor_attributes = []
            self.ssh_monitor_attributes_widgets_items = []
            for connection_ in ssh_con: 
                self.ssh_monitor_attributes.append(ServerProgressAttributes(cluster_name=connection_.cluster_name.value))
                self.ssh_monitor_attributes_widgets_items.append(self.ssh_monitor_attributes[-1].attributes_widgets)
                
            self.server_monitor_widgets.children = self.ssh_monitor_attributes_widgets_items
            
        except Exception as e: print(e)
            
    def get_monitor_pannel(self, ssh_con):
        try:
            for connection_ in self.ssh_monitor_attributes:
                if connection_.cluster_name.value==ssh_con.cluster_name.value:
                    return connection_
            
        except Exception as e: print(e)