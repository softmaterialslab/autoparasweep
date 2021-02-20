#!pip install --user paramiko
#!pip install --user --upgrade cffi cryptography  # this is to avoid waring about cffi
import paramiko
import os
from stat import S_ISDIR

class SSH:
    # ssh_client = SSH('bigred2.uits.iu.edu','kadu', key_file='ssh/private_key')
    # ssh_client = SSH('bigred2.uits.iu.edu','kadu', 'server_password')
    # ssh_client.put('source','destination/path')
    # ssh_client.put_all('source/dir','destination/path')
    # ssh_client.get_all('source/dir','destination/path')
    # ssh_client.execute_command('echo "ls"')

    #from codes.SSH import SSH
    #ssh_client = SSH('bigred3.uits.iu.edu','kadu', ssh_private_key='ssh-config/kadu_bigred')
    #remote_path = "/N/slate/kadu/confinement/sim_runs/Z_5.6_p_1_n_-1_d_0.313_a_0.209_c_1.5_i_-0.005"
    #local_path = "sweep_folder\\confinement\\sim_runs"
    #ssh_client.get_all_files(remote_path, local_path)
    
    def __init__(self, hostname = 'bigred2.uits.iu.edu', username = 'kadu', server_password = None, ssh_private_key = None, port = 22):
    #User configurable settings 

        try:
            self.username = username
            self.server_password = server_password
            self.hostname = hostname
            self.port = port
            
            #print ("Connecting to %s with username=%s..." %(hostname, username))
            self.ssh_private_key = ssh_private_key

            self.connect_server()
            self.attempts = 0
            self.MAX_ATTEMPTS = 3
            
        except Exception as e: print(e)


    def connect_server(self):
        try:
           
            self.sshclient = paramiko.SSHClient()
            self.sshclient.load_system_host_keys()
            self.sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 
            self.transport = paramiko.Transport((self.hostname, self.port))
                
            if self.ssh_private_key is not None:
                self.sshclient.connect(self.hostname, username=self.username, key_filename=self.ssh_private_key, timeout=1)
                mykey = paramiko.RSAKey.from_private_key_file(self.ssh_private_key)
                self.transport.connect(username=self.username, pkey = mykey)
            else:
                if self.server_password is not None:
                    self.sshclient.connect(self.hostname, username=self.username, password = self.server_password)
                    self.transport.auth_password(username = self.username, password = server_password, fallback=False)
                else: raise Exception('Please provide either ssh_private_key or server_password')     
    
            
            self.transport.default_window_size = paramiko.common.MAX_WINDOW_SIZE
            self.transport.packetizer.REKEY_BYTES = pow(2, 40)
            self.transport.packetizer.REKEY_PACKETS = pow(2, 40)
            #self.transport.set_keepalive(2) 
            #self.channel = self.sshclient.invoke_shell()
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)


        except Exception as e: print(e)          
    
    def close_ssh(self):
        try:
            if self.sshclient:
                self.sshclient.close()
            if self.sftp:
                self.sftp.close()
            self.transport.close()
            
        except Exception as e: print(e)


    def execute_command_dummy(self, cmd):
        self.sshclient.exec_command(cmd) 
            
    def execute_command(self, cmd):

        if not self.transport.is_active():
            #print('Transport is not active, Reconnecting...')
            self.connect_server()

        # execute a command in the server
        try:
            if self.sshclient:
                std_out_st = ''
                std_error_st = ''
                for command_to_execute in cmd.split('\n'):
                    stdin, stdout, stderr = self.sshclient.exec_command(command_to_execute)
                    std_out_st += stdout.read().strip().decode("utf-8") + '\n'
                    std_error_st += stderr.read().strip().decode("utf-8") + '\n'
                    stdout.close()
                    stderr.close()

                #Reset the attempts
                self.attempts = 0 
                return (std_out_st, std_error_st)
                   
        except Exception as e: 
            print(e)
            if self.attempts<self.MAX_ATTEMPTS:
                self.attempts += 1
                print("Reconnecting and Executing attempt: {}".format(self.attempts))
                self.connect_server()
                self.execute_command(cmd)
            #Reset the attempts
            self.attempts = 0           
            
    def put_file(self, local_file, remote_file):

        if not self.transport.is_active():
            #print('Transport is not active, Reconnecting...')
            self.connect_server()

        #upload of a file
        try:
            self.sftp.put(local_file, remote_file) 
        except Exception as e: 
            print(e)


    def put_all_files(self, local_path, remote_path):

        if not self.transport.is_active():
            #print('Transport is not active, Reconnecting...')
            self.connect_server()

        #  recursively upload of a dir
        try:
            owd = os.getcwd() 
            os.chdir(os.path.split(local_path)[0])
            parent=os.path.split(local_path)[1]
            exclude = set(["sim_runs"])
 
            for root, dirs, files in os.walk(parent, topdown=True):
                #removing sim_runs folder
                dirs[:] = [d for d in dirs if d not in exclude]
                
                try:
                    _path = os.path.join(remote_path, root).replace("\\", "/")
                    self.sftp.mkdir(_path)
                except:
                    pass    
                for name in dirs:
                    try:
                        _path = os.path.join(remote_path, root, name).replace("\\", "/")
                        self.sftp.mkdir(_path)
                    except:
                        pass

                for name in files:
                    _path = os.path.join(remote_path, root, name).replace("\\", "/")
                    self.sftp.put(os.path.join(root, name),_path)

            os.chdir(owd)
            #Reset the attempts
            self.attempts = 0 

        except Exception as e: 
            os.chdir(owd)
            print(e)

            if self.attempts<self.MAX_ATTEMPTS:
                self.attempts += 1
                print("Reconnecting and uploading attempt: {}".format(self.attempts))
                self.connect_server()
                self.put_all_files(local_path, remote_path)

            #Reset the attempts
            self.attempts = 0           

            
    def get_file(self, remote_file, local_file):

        if not self.transport.is_active():
            #print('Transport is not active, Reconnecting...')
            self.connect_server()

        #download of a file
        try:
            self.sftp.get(remote_file, local_file)
        
        except Exception as e: 
            print(e)

    def sftp_walk(self, remote_path):
        path=remote_path
        files=[]
        folders=[]
        for f in self.sftp.listdir_attr(remote_path):
            if S_ISDIR(f.st_mode):
                folders.append(f.filename)
            else:
                files.append(f.filename)
        if files:
            yield path, files
            
        for folder in folders:
            new_path=os.path.join(remote_path,folder).replace("\\", "/")
            yield (new_path, None)
            for gen_call in self.sftp_walk(new_path):
                yield gen_call
 
    def get_all_files(self, remote_path, local_path):
        #  recursively download of a dir
        # zip and download woulbe fatser: ssh user@host 'tar -cz /source/folder' | tar -xz
        try:

            if not self.transport.is_active():
                #print('Transport is not active, Reconnecting...')
                self.connect_server()

            try:
                __base_dir = os.path.split(remote_path)[1]  
                root_dir = os.path.join(local_path, __base_dir).replace("\\", "/")
                if not os.path.exists(root_dir): 
                    os.mkdir(root_dir)
                local_path = root_dir
            except:
                pass
            
            for path, files in self.sftp_walk(remote_path):
                root_dir = path.replace(remote_path,'')
                #print("ROOT DIR : " + root_dir)
                if not files:
                    #print(os.path.join(local_path, root_dir).replace("\\", "/"))
                    try:
                        os.mkdir(os.path.join(local_path, root_dir).replace("\\", "/"))
                    except:
                        pass
                else:
                    for file in files:
                        file_path_ = os.path.join(path, file).replace("\\", "/").strip()
                        local_file_path_ = os.path.join(local_path, root_dir, file).replace("\\", "/").strip()
                        #print(file_path_)
                        #print(local_file_path_)
                        self.sftp.get(file_path_, local_file_path_)

            #Reset the attempts
            self.attempts = 0

        except Exception as e: 
            print(e)
            # Trying for 3 times
            if self.attempts<self.MAX_ATTEMPTS:
                self.attempts += 1
                print("Reconnecting and downloading attempt: {}".format(self.attempts))
                self.connect_server()
                self.get_all_files(remote_path, local_path)

            #Reset the attempts
            self.attempts = 0
