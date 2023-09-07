
#  Use IP solver to find max independent set in a graph
from __future__ import print_function
from netaddr import IPNetwork
from networkx import *
import ipaddr
from pulp import *
import random


# Solve Weighted Independent Set using LP Solver pulp
def wis_lp(G, enable_logging=False, verbose=False):
    if verbose:
        enable_logging = True

    if enable_logging:
        print('\nGraph size = {}, \nNodes : {}\n'.format(len(G.nodes()), sorted(list(G.nodes()))))

    S_05 = set()
    S_0 = set()  # subnets that should be changed
    S_1 = set()  # subnets that should stay (INDEPENDENT)

    # Parameters
    # Size of the problem   'n'
    Nodes = list(G.nodes(data=True))
    n = len(Nodes)

    # list of edges
    E = G.edges()

    # A new LP problem
    prob = LpProblem("Weighted Independent Set", LpMaximize)

    # Variables
    # A vector of n binary variables
    x = LpVariable.matrix("x", list(range(n)), 0, 1)  # , LpInteger)

    # A vector of weights ## tuple (node, cost)
    w = [(v[0], v[1]['cost']) for v in Nodes]

    # objective
    prob += lpSum([x[v] * w[v][1] for v in range(n)])

    # Constraint
    for i in range(n):
        for j in range(n):
            if (w[i][0], w[j][0]) in E and i != j:
                prob += x[i] + x[j] <= 1

    # Resolution
    prob.solve()

    # Print the status of the solved LP
    if verbose:
        print("Status:", LpStatus[prob.status])

    # Print the value of the variables at the optimum
    for v in range(n):
        # for verification
        
        if x[v].value() == 1:
            S_1.add(Nodes[v][0])
            G.remove_node(Nodes[v][0])
        elif x[v].value() == 0.5:
            S_05.add(Nodes[v][0])
        else:
            S_0.add(Nodes[v][0])
            G.remove_node(Nodes[v][0])

    # Print the value of the objective
    if verbose:
        print("objective=", value(prob.objective))

    # create the graph H from the graph G from the nodes in the set S 1/2 and their neighbors
    if len(S_05) > 0:
        H = G.subgraph(list(S_05))
        if enable_logging:
            S_1, S_0 = wis_heuristic(S_1, S_0, H, enable_logging=True)
        else:
            S_1, S_0 = wis_heuristic(S_1, S_0, H)

    if enable_logging:
        print('\n# of subnets to keep = {}'.format(len(S_1)))
        print("{:^6}{:^10}{:^25}".format('index', 'location', 'subnet'))
        # for i, s in enumerate(sorted(list(S_1))):
        #     print('{:^6}{:^10}{:^25}'.format(i + 1, s[0], str(s[1])))

        print('\n# of subnets to change = {}'.format(len(S_0)))
        print("{:^6}{:^10}{:^25}".format('index', 'location', 'subnet'))
        # for i, s in enumerate(sorted(list(S_0))):
        #     print('{:^6}{:^10}{:^25}'.format(i + 1, s[0], str(s[1])))

    # return S_1, S_0  # KEEP S_1 (INDEPENDENT), CHANGE S_0

    return S_0


def equal_weighted_degree(min_degree, weighted_degrees_list):
    indices_eq_degrees = []

    for index, val in enumerate(weighted_degrees_list):
        if min_degree == weighted_degrees_list[index]:
            indices_eq_degrees.append(index)

    return indices_eq_degrees


# max Weighted Independent Set heuristic algorithm
def wis_heuristic(keep, change, conflict_graph, enable_logging=False, verbose=False):
    if enable_logging:
        print('\nRunning wis_heuristic heuristic algorithm for set: \nS 1/5 = \n'), conflict_graph.nodes()

    vertices = []
    weighted_degrees = []

    # find d or every node and store in the D dictionary
    for v in conflict_graph.nodes():
        w_v = conflict_graph.nodes[v]['cost']
        w_nbr = 0.0
        for nbr in conflict_graph.neighbors(v):
            w_nbr += conflict_graph.nodes[nbr]['cost']
        d = w_nbr / w_v
        weighted_degrees.append(d)
        vertices.append(v)

    if verbose:
        print("{:^8}{:^25}{:^15}".format('location', 'subnet', 'weighted degree'))
        for i in range(len(vertices)):
            print("{:^8}{:^25}{:^15}".format(vertices[i][0], vertices[i][1], weighted_degrees[i]))

    while len(vertices) > 0:
        min_d = min(weighted_degrees)

        # check if there are many weighted degrees are similar and randomly choose one
        eq_degrees = equal_weighted_degree(min_d, weighted_degrees)
        if eq_degrees:
            x = random.choice(eq_degrees)
        else:
            x = weighted_degrees.index(min_d)

        v = vertices[x]

        nbrs = [v]
        for nbr in conflict_graph.neighbors(v):
            nbrs.append(nbr)

        keep.add(v)
        # conflict_graph.remove_node(v)
        conflict_graph=networkx.Graph(conflict_graph)
        conflict_graph.remove_nodes_from(nbrs)
        nbrs.remove(v)
        vertices.remove(v)
        weighted_degrees.remove(min_d)

        for u in nbrs:
            i = vertices.index(u)
            vertices.remove(u)
            weighted_degrees.pop(i)
            change.add(u)

    return keep, change


def example_1():
    print("\n\n")
    print("*", 5 * " * ")
    print("* Example 1... *")
    print("*", 5 * " * ")

    G = networkx.Graph()

    subnets = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']
    subnets_costs = [0.3, 1.3, 1.3, 1.6, 2.2, 0.5, 0.9, 1.4, 1.1]

    conflicts = [
        # a  b  c  d  e  f  g  h  i
        # 1  2  3  4  5  6  7  8  9
        [0, 0, 1, 0, 0, 0, 0, 0, 0],  # 1 a
        [0, 0, 1, 0, 0, 0, 0, 0, 0],  # 2 b
        [0, 0, 0, 0, 0, 0, 0, 0, 0],  # 3 c
        [0, 1, 1, 0, 0, 1, 0, 0, 0],  # 4 d
        [0, 0, 0, 0, 0, 0, 0, 1, 0],  # 5 e
        [0, 0, 0, 0, 0, 0, 0, 0, 0],  # 6 f
        [0, 0, 0, 0, 0, 0, 0, 0, 0],  # 7 g
        [0, 0, 1, 0, 0, 0, 0, 0, 0],  # 8 h
        [0, 1, 0, 0, 0, 0, 1, 0, 0]  # 9 i
    ]

    # Add nodes from the subnets list and costs from subnets_cost list
    for i in range(len(subnets)):
        s = subnets[i]
        c = subnets_costs[i]
        G.add_node(s, cost=c)

    # Add edges from conflicts matrix
    for i in range(len(subnets)):
        for j in range(len(subnets)):
            if conflicts[i][j] == 1:
                G.add_edge(subnets[i], subnets[j])

    wis_lp(G, enable_logging=True)


def example_2():
    print("\n\n")
    print("*", 13 * " * ")
    print("* The example that is in the paper ... *")
    print("*", 13 * " * ", "\n")

    G = networkx.Graph()

    # 's_1', 's_2', 's_3', 's_4', 's_5', 's_6', 's_7', 's_8', 's_9', 's_10', 's_11'
    # subnets = ['s_{}'.format(i + 1) for i in range(11)]
    subnets = ['s_1', 's_2', 's_3', 's_4', 's_6', 's_9', 's_11']
    subnets_costs = [1 for i in range(11)]
    subnets_costs[5] = 1
    subnets_costs[3] = 2
    conflicts = [('s_9', 's_1'), ('s_9', 's_2'), ('s_9', 's_3'),
                 ('s_9', 's_4'), ('s_9', 's_11'), ('s_4', 's_11'),
                 ('s_6', 's_11'), ('s_6', 's_4')]
    for i in range(len(subnets)):
        G.add_node(subnets[i], cost=subnets_costs[i])
    G.add_edges_from(conflicts)

    print(G.nodes(data=True))
    print()
    print(G.edges())

    change = wis_lp(G, verbose=True)#, logging=True)

    print('\nchange', change)


def example_comm_mag():
    print("\n\n")
    print("*", 13 * " * ")
    print("* The example in the ICCN paper w/cost = size of the subnet ... *")
    print("*", 13 * " * ", "\n")

    G = networkx.Graph()

    subnets = [IPNetwork('10.1.0.0/24'), IPNetwork('10.1.1.0/24'), IPNetwork('10.1.2.0/24'), IPNetwork('10.1.3.0/24'),
               IPNetwork('10.1.3.0/24'), IPNetwork('10.1.0.0/22'), IPNetwork('10.1.3.0/24')]

    subnets_no = ['s_1', 's_2', 's_3', 's_4', 's_6', 's_9', 's_11']

    subnets_costs = [subnet.size for subnet in subnets]

    for i in range(len(subnets)):
        print('{:^10}\t{:^20}\t{:5}'.format(subnets_no[i], str(subnets[i]), subnets_costs[i]))

    conflicts = [('s_9', 's_1'), ('s_9', 's_2'), ('s_9', 's_3'),
                 ('s_9', 's_4'), ('s_9', 's_11'), ('s_4', 's_11'),
                 ('s_6', 's_11'), ('s_6', 's_4')]

    for i in range(len(subnets)):
        G.add_node(subnets_no[i], cost=subnets_costs[i])

    G.add_edges_from(conflicts)

    print(G.nodes(data=True))
    print()
    print(G.edges())

    change = wis_lp(G, verbose=True)#, logging=True)

    print('\nchange', change)

def conflict_resolution_dataset():
    print("\n\n")
    print("*", 13 * " * ")
    print("* Conflict Resolution performed on the Dataset... *")
    print("*", 13 * " * ", "\n")  
    PATH_1 = '../tools/'
    G = networkx.Graph()
    subnets_list=[]
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
                subnets_list = subnets_list + d['subnets']
                if d['table_id']==1:
                    continue

            num_of_subnets_before = len(subnets_list)
            subnets=[i for i in range(1, num_of_subnets_before+1)]
            subnets_costs=[]
            subnets_name=[]
            E=[]
            for i, entry in enumerate(subnets_list):
                for j, entry1 in enumerate(subnets_list): 
                    if entry['location']!=entry1['location'] and ipaddr.IPNetwork(entry['subnet']).overlaps(ipaddr.IPNetwork(entry1['subnet'])):
                        E.append((i+1, j+1))
                subnets_costs.append(entry['weight'])
                subnets_name.append(entry['subnet'])

            for i in range(len(subnets)):
                G.add_node(subnets[i], cost=subnets_costs[i])
            G.add_edges_from(E)
            print(G.nodes(data=True))
            print(len(E))
            print(G.edges())

            change = wis_lp(G, verbose=True)#, logging=True)

            print('\nchange', change)
            list_to_change=[]
            subnets_to_change=[]

            for i, entry in enumerate(subnets_list):
                if (i+1) in change:
                    print(subnets_name[i])
                    print(entry['subnet'])
                    list_to_change.append(entry)
                    subnets_to_change.append(subnets_name[i])
            for entry in list_to_change:
                subnets_list.remove(entry)
            print(len(subnets_list))
            print(subnets_name)
            print(subnets_to_change)
            try:
                with open(PATH_2 + os.path.basename(file_name)+'_conflict_free', 'w') as outfile:
                    outfile.writelines(subnets_list)
            except Exception as e:
                print(e)
        


def main():
    # example_1()
    #example_2()
    # example_comm_mag()
    conflict_resolution_dataset()


if __name__ == '__main__': main()


