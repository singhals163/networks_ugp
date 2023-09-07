import csv
import random

from IPAddressConflicts import *
from ParsingRoutingTable import *
from datetime import *
from wis import *
import networkx as nx

## Files ##
# These log files where paresed with parse_routing_file and saved into <Company>Routes.txt on 5/10
E1_ROUTES_FILE = 'routing_tables/E1Routes20160509.log'
E2_ROUTES_FILE = 'routing_tables/E2Routes20160407.log'
# Saved after parse_file from .log files and manual review
E1_ROUTES = 'D:/6th sem/UGP/data/org_1/routes_1.txt'
E2_ROUTES = 'D:/6th sem/UGP/data/org_1/routes_2.txt'

TYPE_1_COST = 1
TYPE_2_COST = 2
TYPE_3_COST = 10
change_Array=[]
sub_Array=[]

for i in range(1, 6):
    ALFA = 1000
    BETA = 2000
    MERGING_FRACTION=0+0.2*i
    


    def write_to_csv(fname, mydict):
        writer = csv.writer(open(fname, 'w'))
        for key, value in mydict.items():
            writer.writerow([key, value])


    def read_dict_from_csv(fname):
        reader = csv.reader(open(fname, 'rb'))
        mydict = dict(reader)
        for n in mydict.keys():
            temp = mydict[n].translate(None, '\'[]').split(',')
            subnets = [s.strip() for s in temp]
            mydict[n] = subnets
        return mydict


    # using csv to save tuple in this function was not good,, not easy to retrieve because of comma seperation
    def gen_random_values_for_addr_types(d):
        global all_routes_util
        all_routes_util = dict()

        for asn, subnets in d.items():

            for subnet in subnets:
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


    # cost function for each subnet
    def cost_fuction(subnet):
        if subnet in all_routes_util:
            return cost(subnet)
        else:
            tmp = subnet.split('_')
            asn = tmp[0]
            c = 0
            subnets = supernet_subnets[subnet]
            for s in subnets:
                print(subnets, subnet)
                c = + cost(asn + '_' + s)
            return int(c)


    def benefit_fuction(M, cs_size):
        benefit = M - cs_size
        return ALFA * benefit


    def utility_function(overlapping, M, cs):
        total_cost = 0
        total_benefit = benefit_fuction(M, cs)
        for overlap in overlapping:

            total_cost += cost_fuction(overlap)

        return total_benefit - total_cost


    def new_utility_function(G, M, cs):
        total_cost = 0
        total_benefit = benefit_fuction(M, cs)
        for overlap in G.nodes:

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
                        asn_supernets[asn] = subnets
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

                        asn_supernets[asn] = subnets
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


    # FIND OVERLAPS OF SUBNETS IN DIFFERENT LOCATIONS
    def find_coalition_overlaps(d):
        print(d)
        sorted_tuple = []
        # CREATE A SORTED LIST OF TUPLES SORT KEY = SUBNETS
        for key, values in d.items():
            for value in values:
                ip = IPNetwork(value)
                sorted_tuple.append((key, ip))

            sorted_tuple.sort(key=lambda tup: tup[1])

        overlap_edges = set()
        for asn, subnets in d.items():
            print ('.')
            # print asn
            for subnet in subnets:
                # print subnet
                first = 0
                last = len(sorted_tuple) - 1
                overlap = False
                item = IPNetwork(subnet)

                while first <= last and not overlap:
                    midpoint = (first + last) // 2

                    ip = sorted_tuple[midpoint][1]

                    if IPSet(item) & IPSet(ip) and asn != sorted_tuple[midpoint][0]:
                        asn1 = asn
                        s1 = str(item)
                        asn2 = sorted_tuple[midpoint][0]
                        s2 = str(ip)
                        node1 = asn1 + '_' + s1
                        node2 = asn2 + '_' + s2

                        if item.size == ip.size:
                            if int(asn1) < int(asn2):
                                overlap_edges.add((node1, node2))
                            else:
                                overlap_edges.add((node2, node1))

                        if item.size < ip.size:
                            overlap_edges.add((node1, node2))
                        else:
                            overlap_edges.add((node2, node1))

                        if item.first < ip.first:
                            last = midpoint - 1
                        else:
                            first = midpoint + 1
                    else:
                        if item.first < ip.first:
                            last = midpoint - 1
                        else:
                            first = midpoint + 1

        return overlap_edges


    # ENHANCED FUNCTION TO FIND CONFLICTS
    def new_find_conflicts(d1, d2):
        print ('Finding conflicts. . . ')
        sorted_tuple = []
        # CREATE A SORTED LIST OF TUPLES SORT KEY = SUBNETS
        for key, values in d2.items():
            for value in values:
                ip = IPNetwork(value)
                sorted_tuple.append((key, ip))

            sorted_tuple.sort(key=lambda tup: tup[1])

        overlap_edges = set()
        for asn, subnets in d1.items():
            print ('.')
            # print asn
            for subnet in subnets:
                # print subnet
                first = 0
                last = len(sorted_tuple) - 1
                overlap = False
                item = IPNetwork(subnet)

                while first <= last and not overlap:
                    midpoint = (first + last) // 2

                    ip = sorted_tuple[midpoint][1]

                    if IPSet(item) & IPSet(ip) and asn != sorted_tuple[midpoint][0]:
                        asn1 = asn
                        s1 = str(item)
                        asn2 = sorted_tuple[midpoint][0]
                        s2 = str(ip)
                        node1 = asn1 + '_' + s1
                        node2 = asn2 + '_' + s2

                        if item.size == ip.size:
                            if int(asn1) < int(asn2):
                                overlap_edges.add((node1, node2))
                            else:
                                overlap_edges.add((node2, node1))

                        if item.size < ip.size:
                            overlap_edges.add((node1, node2))
                        else:
                            overlap_edges.add((node2, node1))

                        if item.first < ip.first:
                            last = midpoint - 1
                        else:
                            first = midpoint + 1
                    else:
                        if item.first < ip.first:
                            last = midpoint - 1
                        else:
                            first = midpoint + 1

        return overlap_edges


    # OLD IMPLEMENTATION THAT WORKS SEQUENTIALLY
    def find_overlaps(d):
        print ('Finding overlaps. . . ')
        clone = d.copy()
        overlapped_subnets = set()
        overlapping = set()

        for asn1, subnets1 in d.items():
            print ('.')
            for asn2, subnets2 in clone.items():
                if asn1 == asn2:
                    continue

                for s1 in subnets1:
                    for s2 in subnets2:
                        if IPSet(IPNetwork(s1)) & IPSet(IPNetwork(s2)):
                            node1 = asn1 + '_' + str(s1)
                            node2 = asn2 + '_' + str(s2)
                            overlapped_subnets.add(node1)
                            overlapped_subnets.add(node2)

                            tmp = tuple()
                            if IPNetwork(s1).size == IPNetwork(s2).size:
                                if int(asn1) < int(asn2):
                                    tmp = (node1, node2)
                                else:
                                    tmp = (node2, node1)
                            if IPNetwork(s1).size < IPNetwork(s2).size:
                                tmp = (node1, node2)
                            else:
                                tmp = (node2, node1)
                            overlapping.add(tmp)
        # print '\nOverlapped pairs {}, \n# of overlapped subnets {}'.format(len(overlapping), len(overlapped_subnets))
        return [overlapping, overlapped_subnets]


    # resolve initial overlaps within the same company (could be mis-configuration)
    # removes the large subnet and keep the more specific (assuming all more specifics are in the routing table
    def solve_initial_overlaps(overlapping, d):
        print ('Solving overlaps. . . ')
        remove_s = set()

        for overlap in overlapping:
            # print overlap
            o = []
            o.append(overlap[0].split('_'))
            o.append(overlap[1].split('_'))
            asn1 = o[0][0]
            s1 = o[0][1]
            asn2 = o[1][0]
            s2 = o[1][1]
            if IPNetwork(s1).size > IPNetwork(s2).size:
                remove_s.add((asn1, s1))
            else:
                remove_s.add((asn2, s2))

        removed = set()
        for i in remove_s:
            # print i
            asn = i[0]
            subnet = i[1]
            if subnet in d[asn] and subnet not in removed:
                print ('Removing {} from {}'.format(subnet, asn))
                d[asn].remove(subnet)
                removed.add(subnet)
            else:
                print ('Subnet {} not found in {}!!'.format(subnet, asn))

            if not d[asn]:
                print ('asn {} has no subnets, {}'.format(asn, d[asn]))
                del d[asn]

        if len(removed) != len(remove_s):
            print ('ERROR REMOVING : {} subnets were not removed'.format(len(remove_s) - len(removed)))

        print ('Completed sovling overlaps..\nDeleted {}\nThe deleted subnets are {}'.format(len(remove_s), remove_s))


    def load_parse_E1_E2_tables_to_dict():  # load_parse_E1_E2_tables_to_dict() and deletes allergan asn
        global E1D
        global E2D
        global all_routes
        all_routes = dict()

        E2 = parse_file(E2_ROUTES_FILE, '22222')
        E1 = parse_file(E1_ROUTES_FILE, '11111')

        E1D = map_subnets_asn(E1, 'E1')
        E2D = map_subnets_asn(E2, 'E2')

        # print ('E1 has {} locations'.format(len(E1D.keys())))
        # for key, subnets in E1D.items():
        #     print ('')  # key, subnets
        # print

        # # Allergan ASN
        # del E2D['64694']

        # print ('E2 has {} locations'.format(len(E2D.keys())))
        # for key, subnets in E2D.items():
        #     print ('')  # key, subnets
        # print

        # writeToFile(E2, E2_ROUTES)
        # writeToFile(E1, E1_ROUTES)

        # # remove duplicated asn # in this case the duplicated asn are the service provider asn because they share same provider
        # for k in E1D.keys():
        #     for l in E2D.keys():
        #         if l == k:
        #             del E2D[l]
        #             del E1D[k]
        E1D=read_dict_from_csv(E1_ROUTES)
        E2D=read_dict_from_csv(E2_ROUTES)

        all_routes.update(E1D)
        all_routes.update(E2D)

        write_to_csv('files/E1_routes_dict.txt', E1D)
        write_to_csv('files/E2_routes_dict.txt', E2D)

        write_to_csv('files/E1_E2_routes_dict.txt', all_routes)


    def create_conflict_graph(conflict_edges):
        # Create a graph
        G = nx.Graph()
        # add nodes and edges from the conflict list
        G.add_edges_from(conflict_edges)
        # update the nodes costs
        for v in G.nodes():
            cost = cost_fuction(v)
            G.nodes[v]['cost'] = cost
        return G


    def routing_table_size(d):
        count = 0
        for k, v in d.items():
            for u in v:
                count += 1
        return count


    def remove_subnets_to_be_changed(d, subnets):
        for i in subnets:
            temp = i.split('_')
            asn = temp[0]
            subnet = temp[1]
            removed = set()
            if subnet in d[asn] and subnet not in removed:
                d[asn].remove(subnet)
                removed.add(subnet)
                # print 'Successfully removed {} from {}'.format(subnet, asn)
            else:
                print ('Attempting to remove {} from {} and not found'.format(subnet, asn))

            if not d[asn]:
                # print 'asn {} has no subnets, {}'.format(asn, d[asn])
                del d[asn]
        return d


    def delete_public_subnets(d, fname):
        empty_asn = []
        for asn, subnets in d.items():
            for subnet in subnets:
                if not IPNetwork(subnet).is_private():
                    d[asn].remove(subnet)
            if not d[asn]:
                empty_asn.append(asn)

        for asn in empty_asn:
            del d[asn]

        write_to_csv(fname, d)


    def paper():
        start_time = datetime.now()
        # load_parse_E1_E2_tables_to_dict()
        global all_routes  # , E1_routes, E2_routes
        all_routes = dict()
        # global all_routes_util, asn_supernets, supernet_subnets, M, N  # key = 'asn_subnet', value=(size, t1,t2,t3) generated using random function
        # all_routes_util = read_dict_from_csv('routing_tables/all_routes_util.txt')

        # # ''
        # E1_routes = read_dict_from_csv('files/E1_routes_dict.txt')
        # E2_routes = read_dict_from_csv('files/E2_routes_dict.txt')
        # #
        # all_routes_before_removing_conflicts = dict()
        # all_routes_before_removing_conflicts.update(E1_routes)
        # all_routes_before_removing_conflicts.update(E2_routes)

        PATH_1 = 'D:/6th sem/UGP/tools/'
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
        print(A1)
        E2_routes=dict(sorted(d2.items(), key=lambda item: len(item[1]), reverse=True)[0:int(len(d2)*MERGING_FRACTION)])
        A2=[len(item[1]) for item in sorted(d2.items(), key=lambda item: len(item[1]), reverse=True)]
        import matplotlib.pyplot as plt
        fig, ax=plt.subplots()
        plt.hist(A1, histtype='step')
        plt.hist(A2, histtype='step')
        ax.legend()
        plt.show()
        print(len(sorted(d2.items(), key=lambda item: len(item[1]), reverse=True)[0][1]))
        write_to_csv('files/E1_routes_dict.txt', E1_routes)
        write_to_csv('files/E2_routes_dict.txt', E2_routes)

        all_routes_before_removing_conflicts = dict()
        all_routes_before_removing_conflicts.update(E1_routes)
        all_routes_before_removing_conflicts.update(E2_routes)
        
        for key1, values1 in E1_routes.items():
            for key2, values2 in E2_routes.items():
                if key1==key2:
                    all_routes_before_removing_conflicts[key1]+=values1
        write_to_csv('files/E1_E2_routes_dict.txt', all_routes_before_removing_conflicts)

        gen_random_values_for_addr_types({**E1_routes, **E2_routes})
        #
        print ('*****************************\n' \
            '  Finding overlaps in E1   \n' \
            '*****************************')
        overlaps = find_coalition_overlaps(E1_routes)
        if len(overlaps) > 0:
            print
            for o in overlaps:
                print (o)
        solve_initial_overlaps(overlaps, E1_routes)
        #     # *********** may generate the graph of overlaps to show it *********** #
        #
        print ('*****************************\n' \
            ' Finding overlaps in E2 \n' \
            '*****************************')
        overlaps = find_coalition_overlaps(E2_routes)
        if len(overlaps) > 0:
            print
            for o in overlaps:
                print (o)

        solve_initial_overlaps(overlaps, E2_routes)

        print ('*****************************\n' \
            '   Checking conflicts... \n' \
            '*****************************')
        conflict_edges = new_find_conflicts(E1_routes, E2_routes)

        # all_routes_before_removing_conflicts = dict()
        # all_routes_before_removing_conflicts.update(E1_routes)
        # all_routes_before_removing_conflicts.update(E2_routes)
        
        # for key1, values1 in E1_routes.items():
        #     for key2, values2 in E2_routes.items():
        #         if key1==key2:
        #             all_routes_before_removing_conflicts[key1]+=values1
        # write_to_csv('files/E1_E2_routes_dict.txt', all_routes_before_removing_conflicts)

        if len(conflict_edges) > 0:
            print ('\n____________________________________')
            print
            print ('************  conflicts ************')
            print ('____________________________________')
            for c in conflict_edges:
                print (c)

            G = create_conflict_graph(conflict_edges)

            print ('*****************************\n' \
                '   Running MAX WIS... \n' \
                '*****************************')
            # run weighted S_1 set LP solver and heuristic algorithm
            keep, subnets_to_be_changed = wis_lp(G)
            if (len(subnets_to_be_changed) > 0):
                print ('\n____________________________________')
                print
                print ('**** subnets that should change ****')
                print(len(all_routes_before_removing_conflicts), len(E1_routes), len(E2_routes))
                print ('____________________________________')
                for c in subnets_to_be_changed:
                    print (c)

                print ('*****************************\n' \
                    'Removing \'S_0\' \n' \
                    '*****************************')

                all_routes = remove_subnets_to_be_changed(all_routes_before_removing_conflicts, subnets_to_be_changed)
                write_to_csv('files/all_routes_no_public_conflicts_removed_dict.txt', all_routes)

        print ('**************************************\n' \
            ' Starting \'merging/splitting process\' \n' \
            '**************************************')
        ''

        d = merge_split_process(all_routes)
        print

        f_edges = find_coalition_overlaps(d)

        print ('\n# of overlaps after merge/split process is {}'.format(len(f_edges)))  # , f_edges)

        print ('creating overlap graph....')
        G = create_conflict_graph(f_edges)

        # print 'graph nodes {}, \n edges {}'.format(G.nodes(), G.edges())

        print ('sending graph to wis_lp...')
        to_be_kept, needs_to_be_changed = wis_lp(G)

        print ('# of nodes to change {}'.format(len(needs_to_be_changed)))
        print ('Nodes {}'.format(needs_to_be_changed))

        write_to_csv('files/reduced_all_routes.txt',d)

        # STEP COMPLETED AND SAVED ROUTING TABLE OF E1 AND E2 IN CSV FILE
        ''
        # load_parse_E1_E2_tables_to_dict()
        ''
        # run this block to generate random util the three types values
        
        # all_routes = read_dict_from_csv('files/E1_E2_routes_dict.txt')
        # gen_random_values_for_addr_types(all_routes)
        change_Array.append(len(to_be_kept))
        sub_Array.append(len(all_routes_before_removing_conflicts))
        print ("--- {} seconds ---".format(datetime.now() - start_time))


    if __name__ == '__main__':
        paper()
        '''
        E2_routes = read_dict_from_csv('files/E2_routes_dict.txt')
        print routing_table_size(E2_routes)

        list_tup = dict_to_sorted_tuple(E2_routes)

        new_find_overlaps(sorted_list_tuples, asn, subnet)
        '''

import matplotlib.pyplot as plt
import numpy as np
quotients=[1-(change_Array[i])/(sub_Array[i]) for i in range(0,5)]

xpoints = np.array([0.2+0.2*i for i in range(0,5)])
ypoints = np.array(quotients)

plt.plot(xpoints, ypoints)
plt.show()