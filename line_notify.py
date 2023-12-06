'''
Line Notification from Rack Monitor
'''
import json
import numpy as np
import time
import datetime
import os
import shutil
import requests
import sys
import configparser
current_dir = os.getcwd()
############# Make Rack Record Matrix ############
record_raw = 8 # Setting the amount of total record items
rack_name=[]
rack_matrixlist=[]
rack_dic = {}
####################  Fill json data in Matrix  ########################################
rack_info = {} # Make Dictionary to input key and value
rack_nodes = {}
tmp_nodes = {}
##################### Check Test State and record #######################
sn_dict = {}
old_failure_dict = {}


class DUT_State:
    def __init__(self,sn):
        self.sn = sn
        self.rack_name = None
        self.physical_position = None
        self.run_count = None
        self.stage = None
        self.test_state = None
        self.test_case_name = None
        self.state = None
        self.snlink = None

    def set_attributes(self,rack_name,physical_position,run_count,stage,test_state,test_case_name,state,snlink):
        self.rack_name = rack_name
        self.physical_position = physical_position
        self.run_count = run_count
        self.stage = stage
        self.test_state = test_state
        self.test_case_name = test_case_name
        self.state = state
        self.snlink = snlink

    def print_info(self):
         print(f"\nSN: {self.sn}")
         print(f"Rack Name: {self.rack_name}")
         print(f"Postition: {self.physical_position}")
         print(f"Run Count: {self.run_count}")
         print(f"Stage: {self.stage}")
         print(f"Test State: {self.test_state}")
         print(f"Test case name: {self.test_case_name}")
         print(f"State: {self.state}")
         print(f"DUT Link:\n{self.snlink}")

    def send_to_line(self, message):
        line_notify_token = 'cRFU2L6E0pt5XvSWVedowynY7xilXA0ktRCPKvKPYyB' #Test team
        
        
        # LINE Notify API URL
        line_notify_api = 'https://notify-api.line.me/api/notify'
        headers = {
            'Authorization': f'Bearer {line_notify_token}',
        }
        payload = {
            'message': message,
        }
        response = requests.post(line_notify_api, headers=headers, data=payload)
        if response.status_code == 200:
            print(f"Message sent to LINE: {message}")
        else:
            print(f"Error sending message to LINE: {response.status_code}, {response.text}")
        

    def print_line_msg(self):
        info_message = (
            f"\nSN: {self.sn}\n"
            f"Rack Name: {self.rack_name}\n"
            f"Postition: {self.physical_position}\n"
            f"Stage: {self.stage}\n"
            f"Test State: {self.test_state}\n"
            f"Test case name: {self.test_case_name}\n"
            f"State: {self.state}\n"
            f"DUT Link:\n{self.snlink}"
        )
        self.send_to_line(info_message)
def get_t2_rm_cfg():
    config = configparser.ConfigParser()
    rm_cfg_path = os.path.join(current_dir,'cfg','teton2_rm.cfg')
    config.read(rm_cfg_path)
    url = config['url_link']['url_teton2_LZ']
    user = config['account']['username']
    pw = config['account']['password']
    url_link = url
    account = {"username":user,"password":pw}

    return url_link,account
def output_gen2RMtorecord_path():
    current_time = datetime.datetime.now()
    current_dir = os.getcwd()
    gen2RM_outputfile = f"gen2_Teton2_RM_{current_time.strftime('%Y%m%d_%H%M%S')}.json"
    gen2RM_output_dir = os.path.join(current_dir,'results','gen2_RM','Teton2')
    gen2RM_output_path = os.path.join(gen2RM_output_dir,gen2RM_outputfile)
    return gen2RM_output_path
############ Web Crawling from Gen2 Rack Monitor ####################
def gen2_RM_WB_Crawling(url,account):
    s = requests.session()
   
    s.post(f"{url}",account)
    hn_l10 = s.get(f"{url}"+"/v1/projects/1/containers?")
    hn_bs = s.get(f"{url}"+"/v1/projects/2/containers?")
    t2_l11_evt = s.get(f"{url}"+"/v1/projects/5/containers?")
    t2_l105_evt = s.get(f"{url}"+"/v1/projects/6/containers?")
    t2_jb_l10_2u_evt = s.get(f"{url}"+"/v1/projects/7/containers?")
    t2_jb_pt_2u_evt = s.get(f"{url}"+"/v1/projects/8/containers?")
    hn_l10_data = hn_l10.json()
    hn_bs_data = hn_bs.json()
    t2_l11_evt_data = t2_l11_evt.json()
    t2_l105_evt_data = t2_l105_evt.json()
    t2_jb_l10_2u_evt_data = t2_jb_l10_2u_evt.json()
    t2_jb_pt_2u_evt_data = t2_jb_pt_2u_evt.json()

    return hn_bs_data,hn_l10_data,t2_jb_pt_2u_evt_data,t2_jb_l10_2u_evt_data,t2_l105_evt_data,t2_l11_evt_data
########### Read RM Json data #############
def get_json(filepath):
    with open(filepath, 'r') as infile:
        rm_data = json.load(infile)
    rm_amount = len(rm_data) # get all racks amount
    # print(f"Totol Racks: {rm_amount}")
    return rm_data,rm_amount
############# Make Rack Record Matrix ############
def make_rk_mat(rm_data,rm_amount):
    for i in range(rm_amount):
        # print(f"i: {i}")
        # rack_name.append(f"matrix_{i}") # Make each rack matrix
        rack_name.append(rm_data[i]["location"]) # Make each rack matrix
        rack_nodes = rm_data[i]["nodes"] # Read all nodes of each rack
        rack_nodes_amount = len(rack_nodes) # Read total nodes of each rack
        # print(f"rack_nodes_amount:{rack_nodes_amount}")
        # matrix = np.empty((record_raw,rack_nodes_amount), dtype='U') # Numpy cannot store String
        matrix =[['' for _ in range(rack_nodes_amount)] for _ in range(record_raw)]
        rack_matrixlist.append(matrix)
        # print(f"Matrix: {matrix}")
    rack_dic = dict(zip(rack_name,rack_matrixlist))
# print(rack_dic)
    return rack_dic
####################  Fill json data in Matrix  ########################################
def fill_data_in_mat(rm_data,rack_dic):
    for i in range(len(rm_data)):
        rack_location = rm_data[i]["location"]
        tmp_nodes =rm_data[i]["nodes"]
        tmp_matrix =rack_dic[rack_location] # This is assign not copy
        # tmp_matrix = list(rack_dic.values())[i]
        for j in range(len(tmp_nodes)):
            sn = tmp_nodes[j]["serial_num"]
            pos = tmp_nodes[j]["physical_position"]
            stage = tmp_nodes[j]["stage"]
            run_count = tmp_nodes[j]["run"]
            test_state = tmp_nodes[j]["test_state"]
            test_case_name = tmp_nodes[j]["test_case_name"]
            state = tmp_nodes[j]["state"]
            snlink = "http://10.245.12.120:9882/node/" + sn +"?api=http%3A%2F%2F10.245.12.132"
                        
            tmp_matrix[0][j] =sn
            tmp_matrix[1][j] =pos
            tmp_matrix[2][j] =stage
            tmp_matrix[3][j] =run_count
            tmp_matrix[4][j] =test_state
            tmp_matrix[5][j] =test_case_name
            tmp_matrix[6][j] =state
            tmp_matrix[7][j] =snlink
    # print(f"{rack_dic}")
    return rack_dic
##################### Check Test State and record #######################
def check_state(rack_dic):
    rack_failsn_dic ={}
    
    for key in rack_dic:
        for j in range(len(rack_dic[key][0])):
            state = rack_dic[key][6][j]
            test_state = rack_dic[key][4][j]
            
            if state =="failed" and test_state !="0/0":
                rk_location = key
                fail_sn_input = rack_dic[key][0][j]
                pos = rack_dic[key][1][j]
                stage = rack_dic[key][2][j]
                run_count = rack_dic[key][3][j]
                test_state = rack_dic[key][4][j]
                test_case_name = rack_dic[key][5][j]
                state = rack_dic[key][6][j]
                snlink = rack_dic[key][7][j]
                dut_sn_info = DUT_State(fail_sn_input)
                dut_sn_info.set_attributes(rk_location,pos,run_count,stage,test_state,test_case_name,state,snlink)
                sn_dict[fail_sn_input]=dut_sn_info
                
    
    return sn_dict,rack_failsn_dic
############### Check repeat SN failure by reading prev mat. and latest mat. ##############
def repeat_check(prev_rk_dic,new_rk_dic):
    new_fail_sn_dict ={}
    for rack, data_list in new_rk_dic.items():
        for i, sn_list in enumerate(data_list[0]):
            sn = sn_list
            
            state = data_list[-2][i]
            if state == 'failed':
                if sn in prev_rk_dic.get(rack, [[]])[0]:
                    # SN in prev_rk_dic, check if any information is different
                    index_in_dict1 = prev_rk_dic[rack][0].index(sn)
                    if data_list[1][i] != prev_rk_dic[rack][1][index_in_dict1] or \
                        data_list[2][i] != prev_rk_dic[rack][2][index_in_dict1] or \
                        data_list[3][i] != prev_rk_dic[rack][3][index_in_dict1] or \
                        data_list[4][i] != prev_rk_dic[rack][4][index_in_dict1] or \
                        data_list[5][i] != prev_rk_dic[rack][5][index_in_dict1] or \
                        data_list[7][i] != prev_rk_dic[rack][7][index_in_dict1] or \
                        state != prev_rk_dic[rack][6][index_in_dict1]:
                        
                        fail_sn = sn
                        rack_name = rack
                        pos = data_list[1][i]
                        stage = data_list[2][i]
                        run_count = data_list[3][i]
                        test_state = data_list[4][i]
                        test_case_name = data_list[5][i]
                        state = state
                        snlink = data_list[7][i]
                        dut_sn_info = DUT_State(fail_sn)
                        dut_sn_info.set_attributes(rack_name,pos,run_count,stage,test_state,test_case_name,state,snlink)
                        new_fail_sn_dict[fail_sn]=dut_sn_info
                else:
                    # SN not in dict1, but state is failed in dict2
                        fail_sn = sn
                        rack_name = rack
                        pos = data_list[1][i]
                        stage = data_list[2][i]
                        run_count = data_list[3][i]
                        test_state = data_list[4][i]
                        test_case_name = data_list[5][i]
                        state = state
                        snlink = data_list[7][i]
                        dut_sn_info = DUT_State(fail_sn)
                        dut_sn_info.set_attributes(rack_name,pos,run_count,stage,test_state,test_case_name,state,snlink)
                        new_fail_sn_dict[fail_sn]=dut_sn_info
    return new_fail_sn_dict

################# Big Func ################
def big_func(t2_rm_data):
    rack_empty_dic = make_rk_mat(t2_rm_data,len(t2_rm_data))
    rack_dic = fill_data_in_mat(t2_rm_data,rack_empty_dic)
    sn_dict,rack_failsn_dic = check_state(rack_dic)

    return rack_dic,sn_dict,rack_failsn_dic
################################################
def lineNotify(token, msg):
 
    url = "https://notify-api.line.me/api/notify"
    headers = {
        "Authorization": "Bearer " + token, 
        "Content-Type" : "application/x-www-form-urlencoded"
    }
    
    payload = {'message': msg}
    r = requests.post(url, headers = headers, params = payload)
    return r.status_code
# ### Web Crawling from Rack Monitor and Check ###
# if __name__ == "__main__":
#     while True:
#         url_link,account = get_t2_rm_cfg()
#         url_link=url_link.replace('"','') # Fix the bug for replace "" symbols to none 
#         # print("Connect Teton2 RM CFG completed !")
#         gen2RM_output_path=output_gen2RMtorecord_path()
#         # print(url_link)
#         hn_bs_data,hn_l10_data,t2_jb_pt_2u_evt_data,t2_jb_l10_2u_evt_data,t2_l105_evt_data,t2_l11_evt_data = gen2_RM_WB_Crawling(url_link,account)

#         rack_dic,sn_dict,rack_failsn_dic = big_func(hn_bs_data)
#         rack_dic,sn_dict,rack_failsn_dic = big_func(hn_l10_data)
#         rack_dic,sn_dict,rack_failsn_dic = big_func(t2_jb_pt_2u_evt_data)
#         rack_dic,sn_dict,rack_failsn_dic = big_func(t2_jb_l10_2u_evt_data)
#         rack_dic,sn_dict,rack_failsn_dic = big_func(t2_l105_evt_data)
#         rack_dic,sn_dict,rack_failsn_dic = big_func(t2_l11_evt_data)
        
#         print(f"Total Failure DUT on T2 Project: {len(sn_dict)} units")
#         # for fail_sn_input, dut_sn_info in sn_dict.items():
#             # dut_sn_info.print_line_msg()
            
#             # dut_sn_info.print_info()
#             # time.sleep(1)
        
#         # print(sn_dict)
#         new_fail_sn_dict = repeat_check(old_failure_dict,rack_dic)
#         for  new_fail_sn,dut_sn_info in new_fail_sn_dict.items():
#             dut_sn_info.print_info()
#     #       # dut_sn_info.print_line_msg()
        
#             old_failure_dict = rack_dic.copy()
#         time.sleep(120)
#         print("Next Round")


### Open and read Json File then Check ###
if __name__ == "__main__":
        
        
        rm_data_old,rm_amount_old = get_json("T2_rm_old.json")
        print("Get T2 RM json files completed !")
        old_rack_dic,sn_dict,old_rack_failsn_dic = big_func(rm_data_old)
 
        
        rm_data_new,rm_amount_new = get_json("T2_rm_new.json")
        print("Get T2 RM json files completed !")
        rack_dic,sn_dict,rack_failsn_dic = big_func(rm_data_new)
    
        new_fail_sn_dict = repeat_check(old_rack_dic,rack_dic)

        # for fail_sn_input, dut_sn_info in sn_dict.items():
             # dut_sn_info.print_line_msg()
             # dut_sn_info.print_info()

        for  new_fail_sn,dut_sn_info in new_fail_sn_dict.items():
            dut_sn_info.print_info()
            dut_sn_info.print_line_msg()
