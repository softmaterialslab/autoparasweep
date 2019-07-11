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
from ipyupload import FileUpload
#from IPython.core.display import display, HTML
style = {'description_width': 'initial'}
# % is single line magic
# %% is magic cell
#!pip install jupyter_dashboards
#!jupyter dashboards quick-setup --sys-prefix
import glob, json
from codes.SSH import SSH
from codes.BagOfJobs import BagOfJobs
import zipfile

class Attributes:


    def __init__(self, var_name= 'Z', var_type = 'range', var_values= '3, 4', var_inc_value= 0.1 ):
        self.var_name = widgets.Text(
            value=var_name,
            description='Attribute name: ',
            style=style,
        )

        self.var_type = widgets.Dropdown(
            options=['range', 'set'],
            value=var_type,
            description='Type: ',
            style=style,
        )
        
        
        def onValueChangeVar_type(change):
            if change.new == 'range':
                self.var_inc.disabled=False
            else:
                self.var_inc.disabled=True
        
        self.var_type.observe(onValueChangeVar_type,'value')

        self.var_values = widgets.Text(
            value=var_values,
            description='Values: ',
            style=style,
        )

        self.var_inc = widgets.BoundedFloatText(
            value=var_inc_value,
            description='Incement for range: ',
            style=style,
        )
        
        if self.var_type.value == 'set':
            self.var_inc.disabled=True
        
        self.attribute_widget = widgets.HBox([ self.var_name, self.var_type, self.var_values, self.var_inc])
 

class Sweep_Json:
    def __init__(self):
        
        self.sweep_name = widgets.Text(
            value='',
            description='Application name: ',
            style=style,
        )
        
        self.app_select = widgets.Dropdown(
            options=['Select'],
            value='Select',
            description='Existing Configs: ',
            style=style,
        )
        
        self.del_config_btn = widgets.Button(description='Delete selected config')
        self.del_config_btn.on_click(self.onChange_del_btn)
        self.del_config_btn.layout.visibility = 'hidden'
        
        
        self.num_of_parameters = widgets.BoundedIntText(
                value=1,
                min=0,
                max=100,
                step=1,
                description='How many parameters: ',
                style=style,
            )
        
        self.job_limit = widgets.BoundedIntText(
                value=1,
                min=1,
                max=10000,
                step=1,
                description='How many jobs to run: ',
                style=style,
            )       
        
        self.populate_app_select_drop()
        
        self.app_select.observe(self.onChange_app_select,'value')
        
        #self.load_config_btn = widgets.Button(description='Load')
        
        self.gen_config_btn = widgets.Button(description='Generate and Save')
        
        self.gen_config_btn.on_click(self.onclick_gen_btn)
        
        #self.start_att = Attributes()
        
        #self.attributes = [self.start_att]
        
        #self.attributes_widgets = [Attributes()]
        
        self.header_select_config = widgets.HBox([self.sweep_name, self.app_select, self.del_config_btn])
        
        self.header_wigetbox = widgets.HBox([self.num_of_parameters, self.job_limit])#, self.load_config_btn])
        
        self.attributes_widgets = widgets.VBox([Attributes().attribute_widget])
        
        self.footer_wigetbox = widgets.HBox([self.gen_config_btn])
        
        self.text_area_for_jobs =  widgets.Textarea(
            value='',
            placeholder='',
            disabled=True,
            layout=Layout(flex='0 1 auto', height='100px', min_height='100px', width='100%')
        )
              
        self.textlog_widget = widgets.HBox([ self.text_area_for_jobs])        
        
        group_area_layout=Layout(
            display='flex',
            border='solid 1px',
            align_items='stretch',
            padding='5px',
            width='100%'
        )
        
        self.wigetbox_top =  widgets.VBox([self.header_select_config, self.header_wigetbox, self.attributes_widgets, self.footer_wigetbox, self.textlog_widget ], layout = group_area_layout)
        
        self.num_of_parameters.observe(self.onChange_num_of_parameters,'value')



        self.upload_btn = FileUpload(
            # https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input#attr-accept
            # eg. '.txt', '.pdf', 'image/*', 'image/*,.pdf'
            accept='.zip', # default
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


        self.unzip_btn = widgets.Button(description='Unzip and Save')
        
        self.unzip_btn.on_click(self.unzip_btn_on_click)

        self.file_btn_widget = widgets.HBox([ self.upload_btn, self.unzip_btn ]) 

        path_string = 'Zip all your executable, infiles, outfiles and jobsubmit template similar to the following directory structure. Check confinement example provided in sweepfolder. \n'
        path_string += 'if the folder or file shown with <>, it may have any name. otherwise it must have same name as shown. \n'
        path_string += '. \n\
├── sweep_folder                          # All programs are put here. So the zip file you upload will eventually be put under this directory. \n\
    ├── <Application_name>          # This is the application name you select; this is the folder you want to zip and upload. \n\
        ├── job_submit_template     # Your job submit template must be just under your application name directory.\n\
        ├── programs                       # This where you will put executable and required directories. \n\
            ├── <executable>            # Executable: can have any name. \n\
            ├── <infiles>                   # Required folder 1. \n\
            ├── <outfiles>                # Required folder 2. \n\
            ├── <data>                     # Required folder 3. \n' 


        self.text_area_for_file_paths =  widgets.Textarea(
            value=path_string,
            placeholder='',
            disabled=True,
            layout=Layout(flex='0 1 auto', height='250px', min_height='100px', width='100%')
        )
              
        self.text_file_widget = widgets.HBox([ self.text_area_for_file_paths])    

        self.wigetbox_bottom =  widgets.VBox([self.file_btn_widget, self.text_file_widget ], layout = group_area_layout)     

        self.wigetbox =  widgets.VBox([self.wigetbox_top, self.wigetbox_bottom ], layout = group_area_layout)   
        
    
    def populate_app_select_drop(self):
        self.all_configs = glob.glob("app-configs/*")
        self.app_select.options = list(self.app_select.options) + [ item.replace("\\", "/").split('/')[-1] for item in self.all_configs]

    def onChange_num_of_parameters(self, change):
        
        if int(change.new) > int(change.old):
            for i in range(int(change.new) - int(change.old)):
                self.attributes_widgets.children += (Attributes().attribute_widget,)
        elif int(change.new) < int(change.old):
            self.attributes_widgets.children = self.attributes_widgets.children[:change.new]

    def onChange_app_select(self, change):
        
        if change.new != 'Select':
            
            self.del_config_btn.layout.visibility = 'visible'
            
            try:
                with open(os.path.join('app-configs', change.new)) as json_file:
                    self.sweep_dic = json.load(json_file) 
                
                self.num_of_parameters.value = len(self.sweep_dic) 
                
                self.attributes_widgets.children = []
                
                for para in self.sweep_dic:
                    
                    item = self.sweep_dic.get(para)

                    if item["type"] == "set":
                        display_str = ""
                        for item_val in item["values"]:
                            display_str += str(item_val)+ ', '

                        display_str = display_str[:-2] 

                        self.attributes_widgets.children += (Attributes(var_name= para, var_type = 'set', var_values=display_str, var_inc_value= 0.0).attribute_widget,)

                    elif item["type"] == "range":
                        display_str = ""
                        for item_val in item["range"]:
                            display_str += str(item_val)+ ', '

                        display_str = display_str[:-2] 

                        self.attributes_widgets.children += (Attributes(var_name= para, var_type = 'range', var_values=display_str, var_inc_value= item["inc"]).attribute_widget,)

                self.sweep_name.value = change.new.split('.')[0] 
            
            except Exception as e: print(e)
        else:
            self.del_config_btn.layout.visibility = 'hidden'
            self.refresh_para_config()
                
    def onclick_gen_btn(self, change):
        try:
            self.new_para_dic = {}
            for item in self.attributes_widgets.children:
                name_A = item.children[0].value
                type_A = item.children[1].value
                values_A = item.children[2].value
                inc_A = item.children[3].value

                if type_A == "set":
                    self.new_para_dic[name_A] = {"type": "set", "values": values_A.split(',') }

                elif type_A == "range":
                    self.new_para_dic[name_A] = {"type": "range", "range": list(map(float, values_A.split(','))), "inc": inc_A }
        
            file_name = self.sweep_name.value +'.json'
            file_path = os.path.join('app-configs', file_name)
            with open(file_path, 'w') as json_file:
                json.dump(self.new_para_dic, json_file)
            
            #refresh sweep selector
            if not file_name in list(self.app_select.options):
                self.app_select.options = list(self.app_select.options) + [ file_name]
                
            self.app_select.value = file_name
        
            self.bagOfJobsObj = BagOfJobs(config_file = file_path, job_limit=self.job_limit.value)
            
            if self.bagOfJobsObj.maximum_jobs >= self.bagOfJobsObj.job_limit:
                
                self.bagOfJobs = self.bagOfJobsObj.get_job_param_list()

                self.generated_job_dic = {}
                self.generated_job_dic['bag_of_jobs'] = self.bagOfJobs
                self.generated_job_dic['run_index'] = None
                time_stamp = str(datetime.datetime.now()).replace('-', '').replace('.', '_').replace(' ', '_').replace(':', '_')
                unique_name_for_para_sweep = self.sweep_name.value + '_'  + time_stamp
                file_name = unique_name_for_para_sweep +'.json'
                file_path = os.path.join('run-config', file_name)
                with open(file_path, 'w') as json_file:
                    json.dump(self.generated_job_dic, json_file)

                self.text_area_for_jobs.value = 'Printing first few jobs...\n'

                for item in self.bagOfJobs[:10]:
                    self.text_area_for_jobs.value += item + '\n'
            else:
                self.text_area_for_jobs.value += 'maximum job possible: {} is lower than jobs requested: {}, please consider reducing the increament for range attributes'.format( self.bagOfJobsObj.maximum_jobs, self.bagOfJobsObj.job_limit)+'\n'
            #len(bagOfJobs.get_job_param_list())
                  
        except Exception as e: print(e)
 
    def unzip_btn_on_click(self, change):
        try:
            if self.upload_btn.value:
                for filename, data in self.upload_btn.value.items():
                    if '.zip' in filename:

                        self.text_area_for_file_paths.value += 'Files are being uploaded.\n'

                        files_uploaded = []
                        file_path = os.path.join('sweep_folder', filename) 
                        with open(file_path, "bw") as file:
                            file.write(data['content'])
                        zip_ref = zipfile.ZipFile(file_path, 'r')
                        zip_ref.extractall('sweep_folder')
                        files_uploaded = zip_ref.namelist()
                        zip_ref.close()

                        if os.path.exists(file_path):
                            os.remove(file_path)

                        for item in files_uploaded:
                            self.text_area_for_file_paths.value += '{} is uploaded.\n'.format(item)

                        self.text_area_for_file_paths.value += 'Please check whether folder hierarchy is correct, otherwise program will fail in the submit jobs stage.\n'


                    else:
                       self.text_area_for_file_paths.value += 'You can only upload a zip file, but found: {}.\n'.format(filename) 
            else:
                self.text_area_for_file_paths.value += 'Please select a zip file containing the program to execute.\n'
            #len(bagOfJobs.get_job_param_list())
                  
        except Exception as e: print(e)


    def refresh_para_config(self):
        #refresh sweep selector
        self.app_select.value = 'Select'
        self.attributes_widgets.children = []
        self.num_of_parameters.value = 0 
        self.sweep_name.value =''
            
    def onChange_del_btn(self, change):
        
        try:
            file_name = self.sweep_name.value +'.json'
            file_path = os.path.join('app-configs', file_name)

            os.remove(file_path)
            new_list_A = list(self.app_select.options)
            new_list_A.remove(file_name)
            self.app_select.options = new_list_A
            self.refresh_para_config()
            
        except Exception as e: print(e)                    