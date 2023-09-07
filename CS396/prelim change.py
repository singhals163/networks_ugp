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
                        print(supernets[0], subnets[i], subnets[i-1], new_overlap)
                        overlap_pair = (asn + '_' + supernets[0], new_overlap[0])
                        overlap_pairs.add(overlap_pair)
                        overlapping_subnets.add(new_overlap[0])

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
                        if new_overlap[0] in overlapping_subnets:
                            overlapping_subnets.remove(new_overlap[0])
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
    o=[]

    while first <= last:
        midpoint = (first + last) // 2

        ip = sorted_list_tuples[midpoint][1]

        if IPSet(ip) & IPSet(item) and sorted_list_tuples[midpoint][0] != asn:
            o.append(sorted_list_tuples[midpoint][0] + '_' + str(ip))
            overlap=True
        
        if item.first < ip.first:
                last = midpoint - 1
        else:
                first = midpoint + 1
    if overlap:
        return o
    return None