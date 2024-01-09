import os
import json
import csv
import random
from netaddr import *



def write_to_csv(fname, mydict):
    writer = csv.writer(open(fname, 'w'))
    for key, value in mydict.items():
        writer.writerow([key, value])

def routing_table_parser(MERGING_FRACTION, path = "../tools/"):
    # global all_routes_util, asn_supernets, supernet_subnets, M, N  # key = 'asn_subnet', value=(size, t1,t2,t3) generated using random function
    # all_routes_util = read_dict_from_csv('routing_tables/all_routes_util.txt')

    # # ''
    # E1_routes = read_dict_from_csv('files/E1_routes_dict.txt')
    # E2_routes = read_dict_from_csv('files/E2_routes_dict.txt')
    # #
    # all_routes_before_removing_conflicts = dict()
    # all_routes_before_removing_conflicts.update(E1_routes)
    # all_routes_before_removing_conflicts.update(E2_routes)

    PATH_1 = path
    subnets_list=[]
    d1={}
    d2={}
    for f in os.listdir(PATH_1):
        if f.startswith('data_'):
            d = None
            table_id = None
            g={}
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
            

            for entry in subnets_list:
                try:
                        g[entry['location']].append(entry['subnet'])
                except:
                        g[entry['location']]=[entry['subnet']]
            # for asn, subnets in g.items():
            #     if (len(subnets)>MERGING_FRACTION):
            #         X[asn]=subnets
            if d['table_id']==1:
                d1=g
            else:
                d2=g
    E1_routes=dict(sorted(d1.items(), key=lambda item: len(item[1]), reverse=True)[0:int(len(d1)*MERGING_FRACTION)])
    A1=[len(item[1]) for item in sorted(d1.items(), key=lambda item: len(item[1]), reverse=True)]
    # print(A1)
    E2_routes=dict(sorted(d2.items(), key=lambda item: len(item[1]), reverse=True)[0:int(len(d2)*MERGING_FRACTION)])
    A2=[len(item[1]) for item in sorted(d2.items(), key=lambda item: len(item[1]), reverse=True)]
    # import matplotlib.pyplot as plt
    # fig, ax=plt.subplots()
    # plt.hist(A1, histtype='step')
    # plt.hist(A2, histtype='step')
    # ax.legend()
    # plt.show()
    # print(len(sorted(d2.items(), key=lambda item: len(item[1]), reverse=True)[0][1]))
    # write_to_csv('files/E1_routes_dict.txt', E1_routes)
    # write_to_csv('files/E2_routes_dict.txt', E2_routes)

    all_routes_before_removing_conflicts = dict()
    all_routes_before_removing_conflicts.update(E1_routes)
    
    for key1, _ in E1_routes.items():
        for key2, values2 in E2_routes.items():
            if key1==key2:
                all_routes_before_removing_conflicts[key1]+=values2
            else :
                all_routes_before_removing_conflicts[key2] = values2
    # write_to_csv('files/E1_E2_routes_dict.txt', all_routes_before_removing_conflicts)

    return E1_routes, E2_routes, all_routes_before_removing_conflicts


# using csv to save tuple in this function was not good,, not easy to retrieve because of comma seperation
# TODO: weights are getting randomly initialised and not based on what is the type of device that it has been allocated to
def gen_random_values_for_addr_types(d, all_routes_util):
    # global all_routes_util
    # all_routes_util = dict()

    for asn, subnets in d.items():

        for subnet in subnets:
            # print(asn, subnet)
            util_key = asn + '_' + subnet
            size = IPNetwork(subnet).size
            # subnet with /32 subnet mask
            if size == 1:
                temp = ([size, 0, 1, 0])
                all_routes_util[util_key] = temp
                continue
            # subnet with subnet mask /28
            if size <= 16:
                t2 = random.randint(0, int(size * 0.80))
                temp = ([size, 0, t2, 0])
                all_routes_util[util_key] = temp
                continue

            t1 = random.randint(0, int(size * 0.50))
            t2 = random.randint(0, int(size * 0.20))
            t3 = random.randint(0, int(size * 0.05))

            temp = [size, t1, t2, t3]
            # print temp
            if not util_key in all_routes_util:
                all_routes_util[util_key] = temp

    write_to_csv('routing_tables/all_routes_util.txt', all_routes_util)

def routing_table_size(d):
    count = 0
    for k, v in d.items():
        count += len(v)
    return count