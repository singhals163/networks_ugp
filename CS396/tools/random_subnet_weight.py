from __future__ import print_function

from datetime import datetime
from netaddr import IPNetwork
import numpy as np
import os, pprint, math, random
import json


PATH = '../tools/'
# routes_1 = PATH + 'routes_1.txt'
# routes_2 = PATH + 'routes_2.txt'
# routes_data_1 = PATH + 'routes_data_1.txt'
# routes_data_2 = PATH + 'routes_data_2.txt'
DHCP_SUBNETS_PERCENTAGE = 0.70 # percentage of subnets that have DHCP scopes; subnets between the size 64 and 1024
TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'
COST_1 = 5  # cost per subnet to configure a scope in the dhcp server 
COST_2 = 5  # cost per subnet to perform network routing change
TYPE_0 = 5  # fixed cost for Case 5 
TYPE_1 = 1  # x num of active hosts       # dhcp
TYPE_2 = 3  # x num of active hosts       # static
TYPE_3 = 20 # x num of active hosts       # static critical 
TYPE_4 = 2  # x num of active hosts x num of changes      # firewall, load balancer, etc.

PERCENTAGE_13_1 = 0.0
PERCENTAGE_13_2 = 1.0
PERCENTAGE_13_3 = 0.0
PERCENTAGE_21_1 = 0.85 
PERCENTAGE_21_2 = 0.10
PERCENTAGE_21_3 = 0.05
PERCENTAGE_22_1 = 0.0
PERCENTAGE_22_2 = 0.80 
PERCENTAGE_22_3 = 0.20

DISTRIBUTION_1 = 22 # SUBNET MASK 
DISTRIBUTION_2 = 30 # SUBNET MASK 

"""
use to read routes files with lines in format --> 'asn', 'subnet'
1- subnets sizes 64 to 1024: randomly select DHCP / non-DHCP subnets for example %70/%30 --> DHCP_SUBNETS_PERCENTAGE
1.1- changing dhcp scope steps: assigne a new range, change in the server, change the gateway, and restart computers
     first ip address .1 is always on the router interface for the range
     sometimes there are fixed (reserved with MAC) ip addresses for specific devices
     fixed ip addresses within the dhcp scopes are considered TYPE_2 or TYPE_3

2- randomly select active ip addressed in each subnet in order to make up subnet weights based on active addresses
2.1- consider the 5 cases below. 
    Case 1.1 and 1.2 are fixed. 
    Case 1.3 random select ip addresses from 1 up to %100 of the available addresses
    Case 2.1 and 2.2 randomly select number of active addrsses UPTO the percentages of the subnet sizes in the table below
    Case 3, will be marked as TYPE_0

Case #      Mask        Size        Type 1  Type 2  Type 3
Case 1.1    /32         1           0       1*      0
Case 1.2    /30         4           0       2*      0
Case 1.3    /27 -/29    8-32        0       100%    0
Case 2.1    /26-/22     64 - 1024   85%     10%     5%
Case 2.2    /26-/22     64 - 1024   0%      80%     20%
Case 3**    < /22       > 1024      0       0       0

*-  special case for these very small subnets; /32 is a one address subnet that is used in virtual interfaces that are 
    accessible for management, /30 is a two address subnet that usually used for point-to-point link connection.
**- large subnets usually are summary addresses

2.2- select ip addresses in each subnet based on 2.1 and mark them active

2.3- First IP address in a subnet is always Type 2

3-  construct dict for the above

    {   'table_id': 1,
        'table_name'='merging company or business unit'
        'subnets':
            {
                'subnet': x.x.x.x/x,
                'location': 'asn' OR 'table_id'
                'enabled': True/False,
                'last_seen': timestamp,
                'tags':[],
                'num_dependencies': #,  firewall, load-balancers, proxy, etc. 
                'weight': w,            sum of all actice addresses x cost of the change
                'ip_add_available':[],
                'ip_add_type_1':[],
                'ip_add_type_2':[],
                'ip_add_type_3':[],
                'log':[
                    {
                        'id': 0, 1, ...,
                        'timestamp': timestamp, 
                        'desc': such as: 'discovered', 
                                         'replaced from x to y',
                                         'disabled',
                                         'conflict detected w/(loc_id, subnet)'
                                         'sucessful split/merge processes in the consolidation'
                    }

                ]
            }, ...
    }, ...

"""


def write_to_file(lines, filename, mode='a', verbose=False):
    f = open(filename, mode)
    for l in lines:
        if verbose:
            print(l)
        f.write(str(l) + '\n')
    f.close()


def open_a_file(file_name):
    try:
        with open(file_name) as f:
            lines = [line.rstrip('\n') for line in f]
            return lines
    except:
        print('cannot open \"{}\"'.format(file_name))
        #return None
        sys.exit(2)


def examine_data_format(line):
    tmp = None
    subnet = None
    asn = None
    tmp = line.split(',')
    if len(tmp) == 2:
        try:
            asn = int(tmp[0].strip('\' '))
            subnet = IPNetwork(tmp[1].strip('\' '))
        except Exception as e:
            print(e)
        if asn != None and subnet != None:
            return 1 # data format is 'asn, subnet'
    else:
        try:
            subnet = IPNetwork(line.strip('\' '))
        except Exception as e:
            print(e)
        if subnet != None:
            return 0 # data format is 'subnet'
    raise TypeError('Unsupported data format, please check README file!')
    sys.exit()


def skewed_distribution_ipaddr_wieght(subnet_size):
    """
    this function assigns wieght to each IP address in the subnet 
    the wieght is used in the random function to change IP status to enabled (active address)
    the random choice function uses this wieghts list  (right skewed distribution)
    ip addresses are usually assigned from the start to the end of the range mostly in a squential order
    e.g. 
    10.0.0.0/29 = [10.0.0.1, 10.0.0.2,... 10.0.0.7]
    10.0.0.1 is the first ip address
    10.0.0.7 is the broadcast address
    wieghts = [7, 6, ..., 1]
    Then we div each w to the sum of all to get total sum == 1
    """
    wieghts_list = np.array(list(reversed(range(1, subnet_size - 1))))
    p = wieghts_list / wieghts_list.sum()
    return p


def exclude_items_from_random_choice(subnet_size, subnet, exclude_list):
    """
    zero the wieght of the item that needs exlcusion
    """
    wieghts_list = np.array(list(reversed(range(1, subnet_size - 1))))
    for ip in exclude_list:
        i = subnet.index(ip)
        wieghts_list[i] = 0
    p = wieghts_list / wieghts_list.sum()
    return p


def random_select_dhcp_subnets(subnets):
    """
    randomly choose % of the subnets and marks them as dhcp subnets
    the % is defined in DHCP_SUBNETS_PERCENTAGE
    """
    a = list(range(len(subnets)))
    b = np.random.choice(a, int(len(a) * (1 - DHCP_SUBNETS_PERCENTAGE)), replace=False)
    non_dhcp = [subnets[x] for x in b]
    dhcp = list(set(subnets) - set(non_dhcp))
    return dhcp, non_dhcp


def process_small_subnets(subnets_tuples):
    list_subnets = []
    for t in subnets_tuples:
        x = {}
        location = t[0]
        subnet = t[1]
        time_stamp = '{}'.format(datetime.now().strftime(TIMESTAMP_FORMAT)) # read back the time from string using --> y = datetime.strptime(x, TIMESTAMP_FORMAT)
        x['subnet'] = str(subnet)
        x['location'] = location
        x['enabled'] = True
        x['last_seen'] = time_stamp
        x['tags'] = []
        x['num_dependencies'] = 0      
        if subnet.size <= 4:
            active_hosts = [str(x) for x in subnet.iter_hosts()] #list(subnet.iter_hosts())
            x['weight'] = TYPE_2 * len(active_hosts)
            x['ip_add_available'] = []
            x['ip_add_type_1'] = []
            x['ip_add_type_2'] = active_hosts
            x['ip_add_type_3'] = []
        else:
            subnet_hosts = [str(x) for x in subnet.iter_hosts()] #list(subnet.iter_hosts())
            active_hosts = []
            active_hosts = np.random.choice(subnet_hosts, int(random.uniform(1, subnet.size - 1) * PERCENTAGE_13_2), replace=False, p=distribution[subnet.size])
            x['weight'] = TYPE_2 * len(active_hosts)
            x['ip_add_available'] = sorted(list(set(subnet_hosts) - set(active_hosts)))
            x['ip_add_type_1'] = []
            x['ip_add_type_2'] = list(active_hosts)
            x['ip_add_type_3'] = []
        x['log'] = [ 
            { 'id': 0, 'timestamp': time_stamp, 'desc': 'discovered' } 
        ] 
        list_subnets.append(x)
    return list_subnets


def process_medium_subnets(subnets_tuples):
    list_subnets = []
    dhcp, non_dhcp = random_select_dhcp_subnets(subnets_tuples)
    for t in dhcp:
        x = {}
        location = t[0]
        subnet = t[1]
        time_stamp = '{}'.format(datetime.now().strftime(TIMESTAMP_FORMAT)) # read back the time from string using --> y = datetime.strptime(x, TIMESTAMP_FORMAT)
        x['subnet'] = str(subnet)
        x['location'] = location
        x['enabled'] = True
        x['last_seen'] = time_stamp
        x['tags'] = []
        x['num_dependencies'] = 0      

        subnet_hosts = [str(x) for x in subnet.iter_hosts()] #list(subnet.iter_hosts())
        distribution_type1 = distribution[subnet.size]
        active_type1 = np.random.choice(subnet_hosts, int(random.uniform(1, subnet.size - 1) * PERCENTAGE_21_1), replace=False, p=distribution_type1)
        distribution_type2 = exclude_items_from_random_choice(subnet.size, subnet_hosts, active_type1)
        active_type2 = np.random.choice(subnet_hosts, int(random.uniform(1, subnet.size - 1) * PERCENTAGE_21_2), replace=False, p=distribution_type2)
        distribution_type3 = exclude_items_from_random_choice(subnet.size, subnet_hosts, list(set(active_type1) | set(active_type2)))
        active_type3 = np.random.choice(subnet_hosts, int(random.uniform(1, subnet.size - 1) * PERCENTAGE_21_3), replace=False, p=distribution_type3)

        x['weight'] = TYPE_1 * len(active_type1) + TYPE_2 * len(active_type2) + TYPE_3 * len(active_type3)
        x['ip_add_available'] = sorted(list(set(subnet_hosts[:-1]) - set(active_type1) - set(active_type2) - set(active_type3)))
        x['ip_add_type_1'] = list(active_type1)
        x['ip_add_type_2'] = list(active_type2)
        x['ip_add_type_3'] = list(active_type3)

        x['log'] = [ 
            { 'id': 0, 'timestamp': time_stamp, 'desc': 'discovered' } 
        ] 
        list_subnets.append(x)
    for t in non_dhcp:
        x = {}
        location = t[0]
        subnet = t[1]
        time_stamp = '{}'.format(datetime.now().strftime(TIMESTAMP_FORMAT)) 
        x['subnet'] = str(subnet)
        x['location'] = location
        x['enabled'] = True
        x['last_seen'] = time_stamp
        x['tags'] = []
        x['num_dependencies'] = 0      

        subnet_hosts = [str(x) for x in subnet.iter_hosts()] #list(subnet.iter_hosts())
        distribution_type1 = distribution[subnet.size]
        active_type1 = np.random.choice(subnet_hosts, int(random.uniform(1, subnet.size - 1) * PERCENTAGE_22_1), replace=False, p=distribution_type1)
        distribution_type2 = exclude_items_from_random_choice(subnet.size, subnet_hosts, active_type1)
        active_type2 = np.random.choice(subnet_hosts, int(random.uniform(1, subnet.size - 1) * PERCENTAGE_22_2), replace=False, p=distribution_type2)
        distribution_type3 = exclude_items_from_random_choice(subnet.size, subnet_hosts, list(set(active_type1) | set(active_type2)))
        active_type3 = np.random.choice(subnet_hosts, int(random.uniform(1, subnet.size - 1) * PERCENTAGE_22_3), replace=False, p=distribution_type3)

        x['weight'] = TYPE_1 * len(active_type1) + TYPE_2 * len(active_type2) + TYPE_3 * len(active_type3)
        x['ip_add_available'] = sorted(list(set(subnet_hosts[:-1]) - set(active_type1) - set(active_type2) - set(active_type3)))
        x['ip_add_type_1'] = list(active_type1)
        x['ip_add_type_2'] = list(active_type2)
        x['ip_add_type_3'] = list(active_type3)
        x['log'] = [ 
            { 'id': 0, 'timestamp': time_stamp, 'desc': 'discovered' } 
        ] 
        list_subnets.append(x)
    
    return list_subnets


def process_large_subnets(subnets_tuples):
    list_subnets = []
    dhcp, non_dhcp = random_select_dhcp_subnets(subnets_tuples)
    for t in dhcp:
        x = {}
        location = t[0]
        subnet = t[1]
        time_stamp = '{}'.format(datetime.now().strftime(TIMESTAMP_FORMAT)) 
        x['subnet'] = str(subnet)
        x['location'] = location
        x['enabled'] = True
        x['last_seen'] = time_stamp
        x['tags'] = []
        x['num_dependencies'] = 0      
        subnet_hosts = [str(x) for x in subnet.iter_hosts()] #list(subnet.iter_hosts())
        x['weight'] = TYPE_2 * 1
        x['ip_add_available'] = subnet_hosts[1:]
        x['ip_add_type_1'] = []
        x['ip_add_type_2'] = subnet_hosts[0]
        x['ip_add_type_3'] = []
        x['log'] = [ 
            { 'id': 0, 'timestamp': time_stamp, 'desc': 'discovered' } 
        ] 
        list_subnets.append(x)
    return list_subnets


def processing(lines, table_id):
    print('processing table_id: {} is started'.format(table_id))
    data_format = examine_data_format(lines[1])
    global distribution 
    subnets_with_details = []
    distribution = {}
    location = None
    subnets_with_details = []
    small_subnets = []
    medium_subnets = []
    large_subnets = []
    # pre compute the distribution of the subnet sizes that we need to randomly activate ip addresses
    for m in range(DISTRIBUTION_1, DISTRIBUTION_2 + 1):
        size = int(math.pow(2, (32 - m)))
        distribution[size] = skewed_distribution_ipaddr_wieght(size)

    if data_format == 0:
        location = table_id

    for line in lines:

        if location == None:
            try:
                tmp = line.split(',')
                asn = tmp[0].strip('\' ') 
                subnet = IPNetwork(tmp[1].strip('\' '))
            except Exception as e:
                print(e)
        else:
            try:
                asn = location
                subnet = IPNetwork(line.strip('\' '))
            except Exception as e:
                print(e)
        # classify the subnets into small, medium, large
        if subnet.size <= 32:
            small_subnets.append((asn, subnet))
        elif subnet.size > 1024:
            large_subnets.append((asn, subnet))
        else:
            medium_subnets.append((asn, subnet))

    subnets_with_details.extend(process_small_subnets(small_subnets))
    subnets_with_details.extend(process_medium_subnets(medium_subnets))
    subnets_with_details.extend(process_large_subnets(large_subnets))

    print('processing table_id: {} is completed'.format(table_id))

    return subnets_with_details
    

def main():
    start_time = datetime.now()
    table_id = 0
    routes_info = []
    
    for f in os.listdir(PATH):
        if f.startswith('routes'):
            lines = open_a_file(os.path.join(PATH, f))
            table_id += 1   
            routes_info_table = {}
            routes_info_table['table_id'] = table_id
            routes_info_table['table_name'] = '{}'.format(f)
            routes_info_table['subnets'] = processing(lines, table_id)
            routes_info.append(routes_info_table)

        try:
            
            with open(PATH + 'data_{}.txt'.format(table_id), 'w') as outfile:
                json.dump(routes_info_table, outfile, indent=4)
            print('data_{}.txt'.format(table_id))
        except Exception as e:
            print(e)
    

    end_time = datetime.now()

    total_time = end_time - start_time
    print('Total time = {}'.format(total_time))


if __name__ == '__main__': 
    main()

