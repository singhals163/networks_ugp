from routingTableParser import routing_table_size
from netaddr import *
import math
import random
# from weights import cost_fuction

ALFA = 1000

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

# SORT A ROUTING TABLE -- TAKE A DICTIONARY AND RETURNS A SORTED LIST OF TUPLES (ASN,SUBNET)
def dict_to_sorted_tuple(d):
    sorted_tuple = []
    for key, values in d.items():
        for value in values:
            ip = IPNetwork(value)
            sorted_tuple.append((key, ip))
        # SORT THE LIST OF TUPLES USING THE IP SUBNET
        sorted_tuple.sort(key=lambda tup: tup[1])

    return sorted_tuple


# CHECK WHETHER OF NOT THERE IS AN OVERLAP WITH A SUBNET IN ANOTHER LOCATION
def is_overlapped(sorted_list_tuples, asn, subnet):
    first = 0
    last = len(sorted_list_tuples) - 1
    overlap = False
    item = IPNetwork(subnet)

    # start_binary_search = datetime.now()
    while first <= last and not overlap:
        midpoint = (first + last) // 2

        ip = sorted_list_tuples[midpoint][1]

        # print 'Is {} overlapping with {} ?'.format(item,ip)
        if IPSet(ip) & IPSet(item) and sorted_list_tuples[midpoint][0] != asn:
            overlap = True
        else:
            if item.first < ip.first:
                last = midpoint - 1
            else:
                first = midpoint + 1
    # print "--- start_binary_search {} seconds ---".format(datetime.now() - start_binary_search)
    return overlap

# RETURN THE OVERLAP WITH A SUBNET IN ANOTHER LOCATION
def new_find_overlaps(sorted_list_tuples, asn, subnet):
    first = 0
    last = len(sorted_list_tuples) - 1
    overlap = False
    item = IPNetwork(subnet)

    while first <= last and not overlap:
        midpoint = (first + last) // 2

        ip = sorted_list_tuples[midpoint][1]

        if IPSet(ip) & IPSet(item) and sorted_list_tuples[midpoint][0] != asn:
            return sorted_list_tuples[midpoint][0] + '_' + str(ip)
        else:
            if item.first < ip.first:
                last = midpoint - 1
            else:
                first = midpoint + 1

    return None


def benefit_fuction(M, cs_size):
    benefit = M - cs_size
    return ALFA * benefit

def utility_function(overlapping, M, cs):
    total_cost = 0
    total_benefit = benefit_fuction(M, cs)
    for overlap in overlapping:

        total_cost += cost_fuction(overlap)

    return total_benefit - total_cost

def map_supernet_subnets(asn, supernet, merged):#, supernet_subnets_d):
    skey = asn + '_' + supernet
    if skey not in supernet_subnets:
        supernet_subnets[skey] = set()
        for m in merged:
            supernet_subnets[skey].add(str(m))
    else:
        for m in merged:
            supernet_subnets[skey].add(str(m))


def modify_supernet_subnets(asn, supernet, splitted_subnets):#, supernet_subnets_d):
    skey0 = asn + '_' + supernet
    skey1 = asn + '_' + splitted_subnets[0]
    skey2 = asn + '_' + splitted_subnets[1]

    supernet1 = IPNetwork(splitted_subnets[0])
    supernet2 = IPNetwork(splitted_subnets[1])

    subnets = supernet_subnets[skey0]

    if skey1 not in supernet_subnets:
        supernet_subnets[skey1] = set()

    if skey2 not in supernet_subnets:
        supernet_subnets[skey2] = set()

    for s in subnets:
        subnet = IPNetwork(s)
        if IPSet(subnet) & IPSet(supernet1):
            supernet_subnets[skey1].add(str(s))
        elif IPSet(subnet) & IPSet(supernet2):
            supernet_subnets[skey2].add(str(s))

    if len(supernet_subnets[skey1]) == 0:
        del supernet_subnets[skey1]
        splitted_subnets.pop(0)
    elif len(supernet_subnets[skey2]) == 0:
        del supernet_subnets[skey2]
        splitted_subnets.pop(1)

    del supernet_subnets[skey0]

    return splitted_subnets


def merge_split_process(d):
    global asn_supernets, supernet_subnets, M, N
    M = 0
    asn_supernets = d.copy()  # key = asn , value = list of summaries
    supernet_subnets = dict()  # key = asn_supernet, value = original list subnets
    N = 512
    M = routing_table_size(asn_supernets)
    W = []
    W.append((0, 0, N))  # (Welfare, Overlaps, N)
    cs_size = M
    welfare = 0

    # list of all locations (Each is identified with ASN #)
    ASNs = [n for n in asn_supernets.keys()]

    all_routes_sorted_list = dict_to_sorted_tuple(asn_supernets)

    # compute the summaries/supernets of subnets in each location
    overlapping_subnets = set()
    overlap_pairs = set()
    I = 0
    while I < 100:
        I += 1
        print ('_________________________________________________________________________________________________________')
        print ('*************************************  merging .... Iteration # {:0>2d} **************************************'\
            .format(I))

        for asn in ASNs:
            ip_addrs = asn_supernets[asn]

            subnets = []

            for ip in ip_addrs:
                cidr = IPNetwork(ip)
                subnets.append(cidr)

            subnets.sort()

            # print '# of subnets = {} in ASN {}\nSubnets :{}'.format(len(subnets), asn, subnets)

            i = len(subnets) - 1
            # going through list of subnets in one location
            while i >= 0:
                # do the merge of the last two in the list
                to_merge = [subnets[i], subnets[i - 1]]
                supernets = merge(to_merge, N)

                # if merge did not happen, same subnets will return ...
                # do nothing and continue to the next in the list
                if len(supernets) == 1:
                    # check whether the supernet overlaps any other subnet in other locations
                    new_overlap = str()
                    if is_overlapped(all_routes_sorted_list, asn, supernets[0]):
                        new_overlap = new_find_overlaps(all_routes_sorted_list, asn, supernets[0])
                        overlap_pair = (asn + '_' + supernets[0], new_overlap)
                        overlap_pairs.add(overlap_pair)
                        overlapping_subnets.add(new_overlap)

                    # evaluate welfare
                    cs_size -= 1
                    new_welfare = utility_function(overlapping_subnets, M, cs_size)
                    # if welfare increased add new supernet
                    if new_welfare > welfare:
                        subnets[i - 1] = IPNetwork(supernets[0])
                        subnets.pop(i)
                        welfare = new_welfare
                        # keep track of supernets and their subnets
                        map_supernet_subnets(asn, supernets[0], to_merge)#, supernet_subnets)
                        # if welfare did not increase, remove the added overlaps and reset the cs_size
                    else:
                        if new_overlap in overlapping_subnets:
                            overlapping_subnets.remove(new_overlap)
                        cs_size += 1
                    asn_supernets[asn] = [str(subnet) for subnet in subnets]
                i -= 1
                # end of while loop

        print ('# of subnets before the merge process = {}\n' \
            '# of subnets after  the merge process = {}'.format(M, routing_table_size(asn_supernets)))
        print ('{} overlapped subnets, {} overlapped pairs, welfare {}, cs {}.'.format(len(overlapping_subnets),
                                                                                    len(overlap_pairs), welfare,
                                                                                    cs_size))
        print ('_________________________________________________________________________________________________________')
        print ('************************************* splitting .... Iteration # {:0>2d} *************************************' \
            .format(I))

        for asn in ASNs:
            ip_addrs = asn_supernets[asn]

            subnets = []

            for ip in ip_addrs:
                cidr = IPNetwork(ip)
                subnets.append(cidr)

            subnets.sort()

            i = len(subnets) - 1
            # going through list of subnets in one location
            while i >= 0:
                to_split = subnets[i]
                # add the asn to the subnet and put in to_split_asn
                to_split_asn = asn + '_' + str(to_split)
                if to_split_asn in overlapping_subnets:
                    cs_size += 1
                    overlapping_subnets.remove(to_split_asn)
                    new_welfare = utility_function(overlapping_subnets, M, cs_size)
                    tmp_splits = []
                    splits = []
                    if new_welfare > welfare:
                        prefix_len = to_split.prefixlen
                        if prefix_len < 32:
                            prefix_len += 1
                            tmp_splits = list(to_split.subnet(prefix_len))
                        splits = modify_supernet_subnets(asn, to_split, tmp_splits)#, supernet_subnets)
                        subnets.remove(to_split)
                        subnets.extend(splits)
                    else:
                        cs_size -= 1
                        overlapping_subnets.add(to_split_asn)

                    asn_supernets[asn] = [str(subnet) for subnet in subnets]
                i -= 1
                # end of while loop

        print ('# of subnets before the merge process = {}\n' \
            '# of subnets after  the merge process = {}'.format(M, routing_table_size(asn_supernets)))
        print ('{} overlapped subnets, {} overlapped pairs, welfare {}, cs {}.'.format(len(overlapping_subnets),
                                                                                    len(overlap_pairs), welfare,
                                                                                    cs_size))
        print ('_________________________________________________________________________________________________________')

        print ('Total utility = {}'.format(welfare))#, W, W[len(W) - 1][0]
        if welfare == W[len(W) - 1][0]:
            break
        W.append((welfare, len(overlapping_subnets), N))

    return asn_supernets




# MODIFIED FROM cidr_merge() IN netaddr
def merge(ip_addrs, N):
    if not hasattr(ip_addrs, '__iter__'):
        raise ValueError('A sequence or iterator is expected!')

    ranges = []

    for ip in ip_addrs:
        cidr = IPNetwork(ip)
        # Since non-overlapping ranges are the common case, remember the original
        ranges.append((cidr.version, cidr.last, cidr.first, cidr))

    ranges.sort()

    i = len(ranges) - 1
    while i > 0:
        if ranges[i][0] == ranges[i - 1][0] and \
                        ranges[i][2] <= ranges[i - 1][1] + N:
            version = ranges[i][0]
            new_last = max(ranges[i][1], ranges[i - 1][1])
            new_first = min(ranges[i][2], ranges[i - 1][2])
            ranges[i - 1] = (version, new_last, new_first)
            del ranges[i]
        i -= 1

    cidr_from_ranges = []

    for r in ranges:
        c = spanning_cidr([IPAddress(r[2]), IPAddress(r[1])])
        cidr_from_ranges.append(str(c))

    return cidr_from_ranges


def calc_mask(subnet):
    """
    find subnet mask of the subnet based on its class
    :param subnet: subnet without subnet mask
    :return: subnet with classful subnet mask
    """
    s = subnet.split('.')
    if int(s[0]) > 0 and int(s[0]) < 127:
        return subnet + '/' + '8'
    elif int(s[0]) > 127 and int(s[0]) < 192:
        return subnet + '/' + '16'
    elif int(s[0]) >= 192 and int(s[0]) < 223:
        return subnet + '/' + '24'


def int_to_binary(ip):
    """
    converts IP in decimal to binary
    :param ip:
    :return: a binary format of the IP
    """
    str = ip.split('.')
    binary_ip = ''
    for x in str:
        binary_ip = binary_ip + '{0:08b}'.format(int(x)) + '.'
    return binary_ip[0:-1]
