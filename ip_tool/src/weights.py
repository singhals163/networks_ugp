import random
from netaddr import *
import math
from merge import merge_split_process

# using csv to save tuple in this function was not good,, not easy to retrieve because of comma seperation
# TODO: weights are getting randomly initialised and not based on what is the type of device that it has been allocated to
all_routes_util = dict()
TYPE_1_COST = 1
TYPE_2_COST = 2
TYPE_3_COST = 10

def gen_random_values_for_addr_types(d):
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

    # write_to_csv('routing_tables/all_routes_util.txt', all_routes_util)



def cost(s):
    if s not in all_routes_util:
        print('ERROR {} IS NOT IN all_routes_util'.format(s))
        return 1
    tmp = all_routes_util[s]
    t1 = math.ceil(int(tmp[1]) - 1 / int(tmp[0]))
    t2 = int(tmp[2]) - 1
    t3 = int(tmp[3]) - 1
    cost = t1 + TYPE_2_COST * t2 + TYPE_3_COST * t3
    return int(cost)


def cost_fuction(subnet):
    if subnet in all_routes_util:
        return cost(subnet)
    # else:
    #     print("This should not be called until coalition game")
    else:
        tmp = subnet.split('_')
        asn = tmp[0]
        c = 0
        subnets = supernet_subnets[subnet]
        for s in subnets:
            # print(subnets, subnet)
            c = + cost(asn + '_' + s)
        return int(c)