from netaddr import IPNetwork
from datetime import datetime
import json
import sys, os


PATH_1 = '../tools/'
PATH_2 = '../data/org_1/'

JSON_IN_FILE = True

def remove_public_subnets_json():
    for f in os.listdir(PATH_1):
        if f.startswith('data_'):
            d = None
            table_id = None
            try:
                file_name = os.path.join(PATH_1, f)
                print(f'openning file: {file_name}')
                with open(file_name) as json_data:
                    d = json.load(json_data)
            except Exception as e:
                print(e)
            if d is not None:
                print("table id = ", d['table_id'])
                subnets_list = d['subnets']

            num_of_subnets_before = len(subnets_list)
            
            for entry in subnets_list:

                if not IPNetwork(entry['subnet']).is_private():
                    print(entry['subnet'])
                    subnets_list.remove(entry)

            print(f'number of subnets before removing the public = {num_of_subnets_before}')
            print(f'number of subnets after removing the public = {len(subnets_list)}')

            try:
                with open(PATH_1 + os.path.basename(file_name), 'w') as outfile:
                    json.dump(d, outfile, indent=4)
            except Exception as e:
                print(e)



def remove_public_subnets_lines():
    for f in os.listdir(PATH_1):
        if f.startswith('routes_'):

            try:
                file_name = os.path.join(PATH_1, f)
                print(f'openning file: {file_name}')
                with open(file_name) as f:
                    subnets_list = f.readlines()
            except Exception as e:
                print(e)

            num_of_subnets_before = len(subnets_list)
            
            for entry in subnets_list:
                # print(entry)

                if not IPNetwork(entry[1]).is_private():
                    print(entry[1])
                    subnets_list.remove(entry)

            print(f'number of subnets before removing the public = {num_of_subnets_before}')
            print(f'number of subnets after removing the public = {len(subnets_list)}')

            try:
                with open(PATH_2 + os.path.basename(file_name), 'w') as outfile:
                    outfile.writelines(subnets_list)
            except Exception as e:
                print(e)


if __name__ == "__main__":
    start_time = datetime.now()

    if JSON_IN_FILE:
        remove_public_subnets_json()
    else:
        remove_public_subnets_lines()


    exec_time = datetime.now() - start_time
    print('{}\n*{:^98}*\n{}'.format('*' * 100, 'exec time = ' + str(exec_time), '*' * 100))

