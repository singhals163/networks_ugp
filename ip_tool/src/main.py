
# section to parse the routing table data
# assigning weights to each routing table entry
# conflict graph
# resolution
# consolidation
# conflict graph
# log file

import routingTableParser 
import overlaps 
# import weights 
from wis import *
import reallocation
import merge
import networkx as nx

# global MERGING_FRACTION
MERGING_FRACTION = 0.2

if __name__ == "__main__":
    # global all_routes_util
    # all_routes_util = dict()
    # load_parse_E1_E2_tables_to_dict()
    global all_routes  # , E1_routes, E2_routes
    all_routes = dict()
    E1_routes, E2_routes, all_routes_before_removing_conflicts = routingTableParser.routing_table_parser(MERGING_FRACTION)

    # Getting initial weights for all subnets
    merge.gen_random_values_for_addr_types({**E1_routes, **E2_routes})

    # ------------ Solving initial E1 overlaps ---------------
    print("############ E1 initial overlaps #############")
    E1_initial_overlaps = overlaps.find_coalition_overlaps(E1_routes)
    for edge in E1_initial_overlaps:
        print(edge)
    E1_removed_subnets = overlaps.solve_initial_overlaps(E1_initial_overlaps, E1_routes)
    # ------------ Solving initial E2 overlaps ---------------
    print("############ E2 initial overlaps #############")
    E2_initial_overlaps = overlaps.find_coalition_overlaps(E2_routes)
    for edge in E2_initial_overlaps:
        print(edge)
    E2_removed_subnets = overlaps.solve_initial_overlaps(E2_initial_overlaps, E2_routes)
    # E1_final_overlaps = overlaps.find_coalition_overlaps(E1_routes)
    # for edge in E1_final_overlaps:
    #     print(edge)
    # E2_final_overlaps = overlaps.find_coalition_overlaps(E2_routes)
    # for edge in E2_final_overlaps:
    #     print(edge)

    # E1_routes["22222"] = ["192.168.190.0/29"]


    # ------------ Solving initial E1-E2 overlaps ---------------
    conflict_edges = overlaps.new_find_conflicts(E1_routes, E2_routes)
    print("############# Conflict edges #############")
    for edge in conflict_edges:
        print(edge)

    G = overlaps.create_conflict_graph(conflict_edges)

    # TODO: check the wis_lp  implementation
    keep, subnets_to_be_changed = wis_lp(G)

    if len(subnets_to_be_changed) > 0:
        print("############ subnets to be changed ##############")
        for subnet in subnets_to_be_changed:
            print(subnet)
    
    count = 0
    for subnet in subnets_to_be_changed:
        for edge in conflict_edges:
            if subnet == edge[0] or subnet == edge[1]:
                count+=1
    if count != len(conflict_edges):
        print("Failed to resolve all conflicts")

    all_routes_after_removing_conflicts = overlaps.remove_subnets_to_be_changed(all_routes_before_removing_conflicts, subnets_to_be_changed)

    # for key, value in all_routes_after_removing_conflicts.items():
    #     print(key, value)


    # ----------- Assigning new subnets to removed subnets ----------------
    subnets_to_be_reassigned = set()
    subnets_to_be_reassigned.update(E1_removed_subnets)
    subnets_to_be_reassigned.update(E2_removed_subnets)
    subnets_to_be_reassigned.update(subnets_to_be_changed)

    all_routes_after_reassigning, new_allocated_subnets, x = reallocation.add_removed_subnets(all_routes_after_removing_conflicts, subnets_to_be_reassigned)
    merge.gen_random_values_for_addr_types(new_allocated_subnets)

    # ov = overlaps.find_coalition_overlaps(all_routes_after_reassigning)
    # if len(ov) > 0:
    #     print("Length of overlaps can't be non-zero after reassigning")


    # ------------- running merge-split process --------------
    d = merge.merge_split_process(all_routes_after_reassigning)
    print("Routing table size after merge split process", routingTableParser.routing_table_size(d))

    f_edges = overlaps.find_coalition_overlaps(d)
    print("Routing table size after finding overlaps", routingTableParser.routing_table_size(d))

    if len(f_edges) > 0:
        print("Conflicting edges found in the graph after consolidation: ", len(f_edges))

        # for edge in f_edges:
        #     print(edge)

    # if not d["13979"]:
    #     print("13979 not found")
    # else:
    #     print(d["13979"])
    # if not d["65432"]:
    #     print("65432 not found")
    # else:
    #     print(d["65432"])

    print ('creating overlap graph....')
    G = overlaps.create_conflict_graph(f_edges)
    frozen_graph = nx.freeze(G)
    unfrozen_graph = nx.Graph(frozen_graph)
    print(nx.is_frozen(unfrozen_graph))
    print("Routing table size after creating graph", routingTableParser.routing_table_size(d))

    # print 'graph nodes {}, \n edges {}'.format(G.nodes(), G.edges())

    print ('sending graph to wis_lp...')
    # TODO: reallocate this set as well
    to_be_kept, needs_to_be_changed = wis_lp(unfrozen_graph)
    print("Routing table size after running wis_lp", routingTableParser.routing_table_size(d))

    count = 0
    for subnet in needs_to_be_changed:
        for edge in f_edges:
            if subnet == edge[0] or subnet == edge[1]:
                count+=1
    print("count: ", count, " f_edges: ", len(f_edges))
    if count < len(f_edges):
        print("Failed to resolve all conflicts")
    else:
        print("Correctly found all conflicts")

    for values in d.values():
        for value in values:
            value = str(value)
# TODO: check if there may exist duplicate copies of the subnets in the dictionary
    d = overlaps.remove_subnets_to_be_changed(d, needs_to_be_changed)
    print("Routing table size after removing conflicts", routingTableParser.routing_table_size(d))
    
    # all_routes_after_removing_conflicts = overlaps.remove_subnets_to_be_changed(d, needs_to_be_changed)

    all_routes_after_reassigning, new_allocated_subnets, x = reallocation.add_removed_subnets(d, needs_to_be_changed)

    ov = overlaps.find_coalition_overlaps(all_routes_after_reassigning)
    if len(ov) > 0:
        print("Length of overlaps can't be non-zero after reassigning")
        for o in ov:
            print(o)
    else :
        print("Resolved all overlaps")



    
