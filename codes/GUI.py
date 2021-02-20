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
from codes.Sweep_Json import Sweep_Json
from codes.SSH_Manager import SSH_Manager
from codes.Job_Handler import Job_Handler


para_gen = Sweep_Json()
ssh_manager = SSH_Manager()
job_handler = Job_Handler(ssh_manager)

tab_contents = ['Connect servers', 'Setup the program', 'Submit jobs']
children = [ssh_manager.wigetbox, para_gen.wigetbox, job_handler.wigetbox]
tabSpace = widgets.Tab()
tabSpace.children = children
for i in range(len(children)):
	   tabSpace.set_title(i, str(tab_contents[i]))
tabSpace.selected_index = 0

#tabChange detection and plot data incase automatically not drawn
def onTabChange(change):
	if change.new == 2:
   		job_handler.refresh_ssh_manager(ssh_manager)
#Tab observer
tabSpace.observe(onTabChange, names='selected_index')

gui = widgets.VBox([tabSpace])