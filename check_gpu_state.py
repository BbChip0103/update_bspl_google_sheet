import paramiko
from paramiko import SSHClient
import json

def get_cmd_result_from_ip(ip, username, passwd, command):
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.load_system_host_keys()
    ssh.connect(ip, username=username, password=passwd)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(command)
    return ssh_stdout.read().decode()

def parse_gpu_text(query_list, gpu_text):
    gpu_inform_list = [[text.strip() for text in line.split(',')] 
                        for line in gpu_text.splitlines()]

    gpu_inform = [{k:v for k, v in zip(query_list, each_gpu_inform)} 
                    for each_gpu_inform in gpu_inform_list]
    return gpu_inform

def parse_gpu_process_text(gpu_process_text):
    gpu_process_list = [[text.strip() for text in line.split(',')] 
                        for line in gpu_process_text.splitlines()]    
    # gpu_process_dict = {inform[0]:inform[1] for inform in gpu_process_list}
    gpu_process_dict = {}
    for inform in gpu_process_list:
        if inform[0] in gpu_process_dict:
            gpu_process_dict[inform[0]].append(inform[1])
        else:
            gpu_process_dict[inform[0]] = [inform[1]]
    gpu_process_dict = {k:','.join(v) for k,v in gpu_process_dict.items()}
    return gpu_process_dict



def get_gpu_state_from_ip(ip):
    with open('../METADATA/account.json', 'r') as f:
        account = json.loads(f.read())
    username = account['username']
    passwd = account['password']
    query_list = ['gpu_uuid', 'index', 'driver_version', 'name', 
                'memory.used', 'memory.total', 'utilization.gpu', 
                'utilization.memory', 'temperature.gpu', 'fan.speed'
                ]
    command = 'nvidia-smi --query-gpu={} --format=csv,noheader'.format(','.join(query_list))

    try:
        gpu_text = get_cmd_result_from_ip(ip, username, passwd, command)
        gpu_inform = parse_gpu_text(query_list, gpu_text)
        result =[
                    [ 
                        each_gpu_inform['memory.used']+' / '+each_gpu_inform['memory.total'],
                        each_gpu_inform['utilization.gpu'],
                        each_gpu_inform['temperature.gpu']+'°C'
                    ]
                    for each_gpu_inform in gpu_inform
                ]
    except Exception as e:
        return [[str(e),gpu_text.strip(),'','','']]

    query_list = ['gpu_uuid', 'pid', 'process_name', 'used_memory']
    command = 'nvidia-smi --query-compute-apps={} --format=csv,noheader'.format(','.join(query_list))
    try:
        gpu_process_text = get_cmd_result_from_ip(ip, username, passwd, command)
        gpu_process_dict = parse_gpu_process_text(gpu_process_text)
        gpu_pid_list = [
                    gpu_process_dict.get(each_gpu_inform['gpu_uuid'], '')
                    for each_gpu_inform in gpu_inform
                ]
    except Exception as e:
        return [str(e),gpu_text.strip()[:20],'','','']

    def make_uid_text(pid_text):
        uid_list = [get_cmd_result_from_ip(ip, username, passwd,
                        command_base.format(pid)).strip() 
                            for pid in pid_text.split(',')]
        uid_text = ','.join(uid_list)
        return uid_text

    command_base = 'ps -fp {} -o uname --no-headers'
    try:
        gpu_uid_list = [make_uid_text(pid_text) 
                            for pid_text in gpu_pid_list]
    except Exception as e:
        return [str(e),gpu_text.strip()[:20],'','','']

    gpu_pid_list = [[pid_text] for pid_text in gpu_pid_list]
    gpu_uid_list = [[uid_text] for uid_text in gpu_uid_list]
    result = [gpu_inform+gpu_pids+gpu_uids
                for gpu_inform, gpu_pids, gpu_uids 
                    in zip(result, gpu_pid_list, gpu_uid_list)]
    return result


if __name__=='__main__':
    print(get_gpu_state_from_ip('163.152.29.182'))

    # with open('../METADATA/account.json', 'r') as f:
    #     account = json.loads(f.read())
    # username = account['username']
    # passwd = account['password']

    # query_list = ['gpu_uuid', 'index', 'driver_version', 'name', 
    #             'memory.used', 'memory.total', 'utilization.gpu', 
    #             'utilization.memory', 'temperature.gpu', 'fan.speed'
    #             ]
    # command = 'nvidia-smi --query-gpu={} --format=csv,noheader'.format(','.join(query_list))
    # gpu_text = get_cmd_result_from_ip('163.152.29.182', username, passwd, command)
    # print(gpu_text)


    # query_list = ['gpu_uuid', 'pid', 'process_name', 'used_memory']
    # command = 'nvidia-smi --query-compute-apps={} --format=csv,noheader'.format(','.join(query_list))
    # gpu_process_text = get_cmd_result_from_ip('163.152.29.182', username, passwd, command)
    # print(gpu_process_text)