from netaddr import *
import networkx as nx
from merge import cost_fuction



# FIND OVERLAPS OF SUBNETS IN DIFFERENT LOCATIONS
def find_coalition_overlaps(d):
    # print(d)
    sorted_tuple = []
    # CREATE A SORTED LIST OF TUPLES SORT KEY = SUBNETS
    for key, values in d.items():
        for value in values:
            ip = IPNetwork(value)
            sorted_tuple.append((key, ip))
    # sorting on the basis of subnets
    # ERROR_RESOLVED: sort called multiple times
    sorted_tuple.sort(key=lambda tup: tup[1])

    overlap_edges = set()
    for asn, subnets in d.items():
        # print ('.')
        # print asn
        for subnet in subnets:
            # print subnet
            first = 0
            last = len(sorted_tuple) - 1
            overlap = False
            item = IPNetwork(subnet)



            # while first <= last and not overlap:
            #     midpoint = (first + last) // 2

            # TODO: search for a faster way
            for midpoint in range(len(sorted_tuple)):
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

                #     if item.first < ip.first:
                #         last = midpoint - 1
                #     else:
                #         first = midpoint + 1
                # else:
                #     if item.first < ip.first:
                #         last = midpoint - 1
                #     else:
                #         first = midpoint + 1
    # exit

    return overlap_edges

def solve_initial_overlaps(overlapping, d):
    print ('Solving overlaps. . . ')
    remove_s = set()

    count = 0
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
            # if (asn2, s2) in remove_s:
            #     continue
            remove_s.add((asn1, s1))
        else:
            # if (asn1, s1) in remove_s:
            #     continue
            remove_s.add((asn2, s2))
    # print("SOME ASNs are extra deleted: ", count)
    removed = set()
    for i in remove_s:
        # print i
        asn = i[0]
        subnet = i[1]
        if subnet in d[asn] and subnet not in removed:
            print ('Removing {} from {}'.format(subnet, asn))
            d[asn].remove(subnet)
            removed.add(asn+"_"+subnet)
        else:
            print ('Subnet {} not found in {}!!'.format(subnet, asn))

        if not d[asn]:
            print ('asn {} has no subnets, {}'.format(asn, d[asn]))
            del d[asn]

    if len(removed) != len(remove_s):
        print ('ERROR REMOVING : {} subnets were not removed'.format(len(remove_s) - len(removed)))

    print ('Completed sovling overlaps..\nDeleted {}\nThe deleted subnets are {}'.format(len(remove_s), remove_s))
    return removed

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
        # print ('.')
        # print asn
        for subnet in subnets:
            # print subnet
            first = 0
            last = len(sorted_tuple) - 1
            overlap = False
            item = IPNetwork(subnet)

            # while first <= last and not overlap:
            for midpoint in range(len(sorted_tuple)):
                # midpoint = (first + last) // 2

                ip = sorted_tuple[midpoint][1]
                # TODO: confirm if the asn condition needs to be checked
                # if IPSet(item) & IPSet(ip) and asn != sorted_tuple[midpoint][0]:
                if IPSet(item) & IPSet(ip):
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

                #     if item.first < ip.first:
                #         last = midpoint - 1
                #     else:
                #         first = midpoint + 1
                # else:
                #     if item.first < ip.first:
                #         last = midpoint - 1
                #     else:
                #         first = midpoint + 1
    # for edge in overlap_edges:
        # print(edge)
    return overlap_edges


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

def remove_subnets_to_be_changed(d, subnets):
    removed = set()
    for i in subnets:
        temp = i.split('_')
        asn = temp[0]
        subnet = temp[1]
        # if subnet in d[asn] and subnet not in removed:
        if subnet in d[asn]:
            d[asn].remove(subnet)
            removed.add(subnet)
            # print 'Successfully removed {} from {}'.format(subnet, asn)
        else:
            print ('Attempting to remove {} from {} and not found'.format(subnet, asn))
            print(d[asn])

        if not d[asn]:
            # print 'asn {} has no subnets, {}'.format(asn, d[asn])
            del d[asn]
    return d
