#  Use IP solver to find max independent set in a graph
from __future__ import print_function
from netaddr import IPNetwork
from networkx import *
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
        if verbose:
            print('{} ({}) = {}'.format(x[v], Nodes[v][0], x[v].value()))
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
        for i, s in enumerate(sorted(list(S_1))):
            print('{:^6}{:^10}{:^25}'.format(i + 1, s[0], str(s[1])))

        print('\n# of subnets to change = {}'.format(len(S_0)))
        print("{:^6}{:^10}{:^25}".format('index', 'location', 'subnet'))
        for i, s in enumerate(sorted(list(S_0))):
            print('{:^6}{:^10}{:^25}'.format(i + 1, s[0], str(s[1])))

    return S_1, S_0  # KEEP S_1 (INDEPENDENT), CHANGE S_0

    # return S_0


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

        nbrs = []
        for nbr in conflict_graph.neighbors(v):
            nbrs.append(nbr)

        keep.add(v)
        conflict_graph.remove_node(v)
        conflict_graph.remove_nodes_from(nbrs)
        vertices.remove(v)
        weighted_degrees.remove(min_d)
        # list_to_change=[]
        # subnets_to_change=[]

        # for i, entry in enumerate(subnets_list):
        #         if (i+1) in change:
        #             print(subnets_name[i])
        #             print(entry['subnet'])
        #             list_to_change.append(entry)
        #             subnets_to_change.append(subnets_name[i])
        # for entry in list_to_change:
        #         subnets_list.remove(entry)


        for u in nbrs:
            i = vertices.index(u)
            vertices.remove(u)
            weighted_degrees.pop(i)
            change.add(u)

    return keep, change



