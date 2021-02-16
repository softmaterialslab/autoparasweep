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
from ipyupload import FileUpload

class SSHAttributes:
    def __init__(self, hostname = 'bigred3.uits.iu.edu', username = 'kadu', server_password = None, ssh_private_key = None, port = 22 ):
        
        self.ssh = None
        
        self.hostname = widgets.Text(
            value=hostname,
            description='Hostname: ',
            style=style,
        )

        self.username = widgets.Text(
            value=username,
            description='Username: ',
            style=style,
        )
        
        self.server_password = widgets.Password(
            value=server_password,
            description='Password: ',
            placeholder='********',
            style=style,
        )
        
        
        self.ssh_private_key = widgets.Dropdown(
            options=['None'],
            value='None',
            description='ssh key: ',
            style=style,
        )

        self.port = widgets.BoundedIntText(
            value=port,
            description='Port: ',
            style=style,
        )
        
        self.connect_btn = widgets.Button(description='Connect')
        self.connect_btn.on_click(self.onclick_coonect_btn)
        
        
        self.attribute_widget = widgets.HBox([ self.hostname, self.username, self.server_password, self.ssh_private_key, self.port, self.connect_btn])
        
        
        self.command_line = widgets.Text(
            value='',
            description='Enter Command: ',
            style=style,
            layout=Layout(flex='0 1 auto', width='100%')
        )
        
        self.execute_btn = widgets.Button(description='Execute')
        self.execute_btn.on_click(self.onclick_execute_btn)
        
        self.clear_btn = widgets.Button(description='Clear')
        self.clear_btn.on_click(self.onclick_clear_btn)
        
        self.command_exe_widget = widgets.HBox([ self.command_line, self.execute_btn, self.clear_btn ])
        
        
        self.ssh_log =  widgets.Textarea(
            value='',
            placeholder='',
            disabled=True,
            layout=Layout(flex='0 1 auto', height='100px', min_height='100px', width='100%')
        )
        
        group_area_layout=Layout(
            display='flex',
            border='solid 1px',
            align_items='stretch',
            padding='5px',
            width='100%'
        )
        
        self.textlog_widget = widgets.HBox([ self.ssh_log])

        
        self.wigetbox =  widgets.VBox([self.attribute_widget, self.command_exe_widget, self.textlog_widget], layout=group_area_layout)
        
        self.populate_ssh_key_drop()
       
        
    def populate_ssh_key_drop(self):
        file_path = os.path.join('ssh-config', '*')
        self.all_keys = glob.glob(file_path)
        self.ssh_private_key.options = ['None'] + [ item.replace("\\", "/").split('/')[-1] for item in self.all_keys]
        if len(self.ssh_private_key.options) > 1:
            self.ssh_private_key.value = self.ssh_private_key.options[1]
        
    def onclick_coonect_btn(self, change):
        try:
            if self.connect_btn.description != 'Disconnect':
                if self.username.value != '' and self.hostname.value != '' and  self.port: 
                    key_file = self.ssh_private_key.value 
                    key_path = os.path.join('ssh-config', key_file)
                    if key_file != 'None':
                        self.ssh_log.value += "Connecting to %s with username=%s with ssh key...\n" %(self.hostname.value, self.username.value)
                        self.ssh = SSH(username = self.username.value, hostname = self.hostname.value, port = self.port.value, ssh_private_key = key_path)
                    elif self.server_password.value !='':
                        self.ssh_log.value += "Connecting to %s with username=%s with password...\n" %(self.hostname.value, self.username.value)
                        self.ssh = SSH(username = self.username.value, hostname = self.hostname.value, port = self.port.value, server_password = self.server_password.value)
                    else:
                        self.ssh_log.value += 'Please provide either ssh_private_key or server_password.\n'

                    if(self.ssh and self.ssh.sshclient):
                        self.connect_btn.description = 'Disconnect'

                        self.ssh_log.value += 'Connected...\n'

                    else:
                        self.connect_btn.description = 'Retry' 
                else:
                    self.ssh_log.value += 'Check username, hostname and port.\n'
            else:
                self.ssh.close_ssh()
                self.ssh = None
                self.connect_btn.description = 'Connect'
                self.ssh_log.value += 'Connection colsed...\n'
                
        except Exception as e: print(e)
            
    def onclick_execute_btn(self, change):
        try:
            if(self.ssh and self.ssh.sshclient and self.command_line.value != ''):
                (std_out_st, std_error_st) = self.ssh.execute_command(self.command_line.value)
                self.ssh_log.value +=  std_out_st
                self.command_line.value = ''
        except Exception as e: print(e)
            
    def onclick_clear_btn(self, change):
        try:
            self.command_line.value = ''
            self.ssh_log.value = ''
        except Exception as e: print(e)

class SSH_Manager:
    def __init__(self):
        
        self.num_of_ssh_connections = widgets.BoundedIntText(
            value=1,
            min=0,
            max=100,
            step=1,
            description='How many SSH connections: ',
            style=style,
        )

        self.ssh_description = widgets.HTML(
            value="Upload a ssh key<b></b>",
            placeholder='',
            description='       ',
        )

        self.sshkey_upload = FileUpload(
            # https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input#attr-accept
            # eg. '.txt', '.pdf', 'image/*', 'image/*,.pdf'
            accept='', # default
            # True to accept multiple files upload else False
            multiple=False, # default
            # True to disable the button else False to enable it
            disabled=False, # default
            # CSS transparently passed to button (a button element overlays the input[type=file] element for better styling)
            # e.g. 'color: darkblue; background-color: lightsalmon; width: 180px;'
            style_button='', # default
            # to compress data from browser to kernel
            # compress level from 1 to 9 incl. - 0 for no compression
            compress_level=0 # default
        )


        self.save_btn = widgets.Button(description='Save the key')
        
        self.save_btn.on_click(self.save_ssh_key)

        self.connnect_all = widgets.Button(description='Connect all') 

        self.connnect_all.on_click(self.connnect_all_clicked) 

        self.check_queue_info = widgets.Button(description='Check queue info')   

        self.check_queue_info.on_click(self.check_queu_info_click)
        
        
        self.header_wigetbox = widgets.HBox([self.num_of_ssh_connections, self.connnect_all,  self.check_queue_info, self.ssh_description, self.sshkey_upload, self.save_btn])
        
        #self.ssh_connections = [SSHAttributes()]
        #self.ssh_connections = [SSHAttributes(), SSHAttributes(username = 'nhewagam'), SSHAttributes(username = 'vjadhao'), SSHAttributes(username = 'huanshen'), SSHAttributes(username = 'knilsson'), SSHAttributes(username = 'nbrunk'), SSHAttributes(username = 'lm44')]
        self.ssh_connections = [SSHAttributes(), SSHAttributes(username = 'nhewagam'), SSHAttributes(username = 'vjadhao')]
        
        #self.attributes_widgets = widgets.VBox([self.ssh_connections[0].wigetbox])
        self.attributes_widgets = widgets.VBox([item.wigetbox for item in self.ssh_connections])

        self.num_of_ssh_connections.value = len(self.ssh_connections)
        
        #self.footer_wigetbox = widgets.HBox([self.gen_config_btn])

        self.text_area_for_ssh =  widgets.Textarea(
            value='',
            placeholder='',
            disabled=True,
            layout=Layout(flex='0 1 auto', height='100px', min_height='100px', width='100%')
        )
              
        self.textlog_widget = widgets.HBox([ self.text_area_for_ssh])  

        
        group_area_layout=Layout(
            display='flex',
            border='solid 1px',
            align_items='stretch',
            padding='5px',
            width='100%'
        )
        
        self.wigetbox =  widgets.VBox([self.header_wigetbox, self.attributes_widgets, self.textlog_widget], layout = group_area_layout)
        
        self.num_of_ssh_connections.observe(self.onChange_num_of_ssh_connection,'value')  

    def onChange_num_of_ssh_connection(self, change):
        try:
            if int(change.new) > int(change.old):
                for i in range(int(change.new) - int(change.old)):
                    self.ssh_connections.append(SSHAttributes())
                    self.attributes_widgets.children += (self.ssh_connections[-1].wigetbox,)
            elif int(change.new) < int(change.old):
                self.attributes_widgets.children = self.attributes_widgets.children[:change.new]
                self.ssh_connections = self.ssh_connections[:change.new]
        except Exception as e: print(e) 

    def save_ssh_key(self, change):
        try:
            if self.sshkey_upload.value:
                for filename, data in self.sshkey_upload.value.items():
                    self.text_area_for_ssh.value += 'File is being uploaded.\n'
                    file_path = os.path.join('ssh-config', filename) 
                    with open(file_path, "bw") as file:
                        file.write(data['content'])

                    self.refresh_drop_key()
                    self.text_area_for_ssh.value += 'key file: {} should be available to select.\n'.format(filename)


            else:
                self.text_area_for_ssh.value += 'Please select a private key file to save.\n'

        except Exception as e: print(e)  

    def refresh_drop_key(self):
        try:
            for con in self.ssh_connections:
                con.populate_ssh_key_drop()

        except Exception as e: print(e) 


    def check_queu_info_click(self, change):
        try:
            for connection_ in self.ssh_connections:
                command_str = 'qstat -u ' + connection_.username.value
                if(connection_.ssh and connection_.ssh.sshclient):
                    (std_out_st, std_error_st) = connection_.ssh.execute_command(command_str)
                    connection_.ssh_log.value +=  std_out_st

        except Exception as e: print(e)  

        
    def connnect_all_clicked(self, change):
        try:
            if self.connnect_all.description == 'Connect all':
                self.connnect_all.description = 'Disconnect all'
            elif self.connnect_all.description == 'Disconnect all':
                self.connnect_all.description = 'Connect all'
                
            self.text_area_for_ssh.value += 'Clicking all connect/disconnect buttons...\n'
            for connection_ in self.ssh_connections:
                connection_.onclick_coonect_btn({})
                #connection_.wigetbox 
            self.text_area_for_ssh.value += 'Clicking Done.\n'

        except Exception as e: print(e)  