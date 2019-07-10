import os,sys
import numpy as np
import itertools
import random
import json

class BagOfJobs:
    # bagOfJobs = BagOfJobs()
    # bagOfJobs = BagOfJobs('config/sweep.json')
    # bagOfJobs = BagOfJobs('config/sweep.json', 500)
    # bagOfJobs =BagOfJobs(job_limit=100)
    # then
    # bagOfJobs.get_job_param_list()
    # or
    # job_generator = bagOfJobs.generate_job_params()
    #    for job in job_generator:
    #       print(job)
    #    or
    #    next(job_generator)
    
    def __init__(self, config_file = 'app-configs/confinement.json', job_limit = None):
        #User configurable settings
        self.config_file = config_file
        self.sweep_dic = {}
        self.expanded_dic = {}
        self.parameter_list = []
        
        try:
            with open(self.config_file) as json_file:  
                self.sweep_dic = json.load(json_file)
                
            self.maximum_jobs = self.get_maximum_num_of_jobs()

            if job_limit is None:
                self.job_limit = self.maximum_jobs
            else:
                self.job_limit = job_limit

            if self.maximum_jobs >= self.job_limit :
                self.attribute_list = self.sweep_dic.keys()
            else:
                raise Exception('maximum job possible: {} is lower than jobs requested: {}, please consider reducing the increament for range attributes'.format( self.maximum_jobs, self.job_limit))
       
        except Exception as e: print(e)
     
    def get_maximum_num_of_jobs(self):
        #Total combinations
        #"para":{"type":"set", "values":[1,2,3,4]}
        try:
            total_comb = 1 
            for para in self.sweep_dic:
                item = self.sweep_dic.get(para) 
                if item["type"] == "set":
                    num_values = len(item["values"])
                    total_comb *= num_values
                elif item["type"] == "range":
                    num_values = np.arange(item["range"][0],item["range"][1],item["inc"]).shape[0]
                    total_comb *= num_values

            return total_comb
        except Exception as e: print(e)
    
    def expand_dictionary(self):
        # fill expanded_dic with possibilities
        try:
            for para in self.sweep_dic:
                item = self.sweep_dic.get(para) 
                if item["type"] == "set":
                    self.expanded_dic[para] = item["values"]
                elif item["type"] == "range":
                    num_decimals = str(item["inc"])[::-1].find('.')
                    self.expanded_dic[para] = np.around(np.arange(item["range"][0], item["range"][1], item["inc"]), decimals = num_decimals) 
        except Exception as e: print(e)
    
    def gen_combinations(self):
        # Generate all unique combinations using expanded_dic
        self.generated_combinations = list(itertools.product(*(self.expanded_dic[para] for para in self.attribute_list)))
        random.shuffle(self.generated_combinations)
        self.generated_combinations = self.generated_combinations[0:self.job_limit]
        
    def gen_string_for_combo(self, param_tuple):
        # For a given combination, generate -param1 value1 -param2 value2 etc...
        try:
            param_string = ''
            for i, attribute in enumerate(self.attribute_list):
                param_string += '-{} {:n} '.format(attribute, param_tuple[i])

            return param_string
        except Exception as e: print(e)
    
    def get_job_param_list(self):
        # Entry point 1
        # This returns job parameters as a list
        try:
            self.expand_dictionary()
            self.gen_combinations()
            for param_tuple in self.generated_combinations:
                self.parameter_list.append(self.gen_string_for_combo(param_tuple)) 

            return self.parameter_list
        except Exception as e: print(e)
    
    
    def generate_job_params(self):
        # Entry point 2
        # This returns a generator
        try:
            self.expand_dictionary()
            self.gen_combinations()
            for param_tuple in self.generated_combinations:
                yield self.gen_string_for_combo(param_tuple)
                
        except Exception as e: print(e)
