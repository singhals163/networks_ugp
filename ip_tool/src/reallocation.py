# from IPAddressConflicts import *
import ipaddress
from netaddr import *

def print_ip_range(address_space):
    for range in address_space.iter_ipranges():
        print(range)

def number_of_subnets_in_remaining_address_space(d) :
    cidrs = []
    for ip_range in d.iter_ipranges():
        # print("hi")
        # print(str(iprange_to_cidrs(ip_range[0], ip_range[-1])))
        cidrs.extend(iprange_to_cidrs(ip_range[0], ip_range[-1]))
    return len(cidrs)

def get_initial_summarised_number_of_subnets(all_routes_before_removing_conflicts) :
    # Define the full address space
    # full_address_space = IPSet(['0.0.0.0/0'])

    # Create an IPSet from the allocated subnets
    allocated_subnets = all_routes_before_removing_conflicts.values()
    allocated_ipset = IPSet()
    
    for subnet_list in allocated_subnets:
        for subnet in subnet_list:
            allocated_ipset = allocated_ipset | IPSet([subnet])
    return number_of_subnets_in_remaining_address_space(allocated_ipset)        

def get_remaining_address_space(all_routes_before_removing_conflicts):
    # Define the full address space
    full_address_space = IPSet(['0.0.0.0/0'])

    # Create an IPSet from the allocated subnets
    allocated_subnets = all_routes_before_removing_conflicts.values()
    allocated_ipset = IPSet()
    
    for subnet_list in allocated_subnets:
        for subnet in subnet_list:
            allocated_ipset = allocated_ipset | IPSet([subnet])

    # Perform a bitwise XOR operation to find the remaining address space
    remaining_address_space = allocated_ipset ^ full_address_space

    return remaining_address_space

def convert_ip_set_to_list_of_subnets(d) :
    cidrs = []
    for ip_range in d.iter_ipranges():
        # print("hi")
        # print(str(iprange_to_cidrs(ip_range[0], ip_range[-1])))
        cidrs.extend(iprange_to_cidrs(ip_range[0], ip_range[-1]))
    return cidrs

def subtract_ip_range(curr_addr_space, remove_ip_range) : 
    s1 = remove_ip_range
    # print(s1)
    return curr_addr_space ^ s1

def allocate_space(remaining_address_space, address_space_segment, subnet_size):
    ipstart = ipaddress.IPv4Address(str(address_space_segment[0]))
    start_ip_end = ipstart + subnet_size - 1
    # ipend = ipaddress.IPv4Address(str(address_space_segment[-1]))
    # end_ip_start = ipend - subnet_size

    # print(address_space_segment[0], IPAddress(str(start_ip_end)))
    remove_ip_range = IPSet(IPRange(address_space_segment[0], IPAddress(str(start_ip_end))))
    remaining_address_space = subtract_ip_range(remaining_address_space, remove_ip_range)
    # print("___________final ip range_____________")
    return remaining_address_space, convert_ip_set_to_list_of_subnets((remove_ip_range))

def address_space_size(ip_range):
    val = int(ipaddress.IPv4Address((str(ip_range[-1])))) - int(ipaddress.IPv4Address((str(ip_range[0]))))
    # print(val)
    return val


def get_asn_subnet(subnet) :
    # print(subnet)
    temp = subnet.split('_')
    y = int(temp[1].split('/')[1])
    return temp[0], temp[1], 2 ** (32-y)

def number_of_ranges_in_remaining_address_space(remaining_address_space) :
    return len(address_space_size.iter_ipranges())

    


def best_fit_algorithm(all_routes_before_removing_conflicts, subnets_to_be_changed) :
    remaining_address_space = get_remaining_address_space(all_routes_before_removing_conflicts)
    new_space_allocated_to_subnets = dict()
    # print(len(list(remaining_address_space.iter_cidrs())))
    for i in subnets_to_be_changed:
        asn, subnet, subnet_size = get_asn_subnet(i)
        optimal_address_space = None
        optimal_size = 0
        for curr_address_space in remaining_address_space.iter_ipranges():
            size = address_space_size(curr_address_space)
            if size > subnet_size :
                if not optimal_address_space or optimal_size > size :
                    optimal_address_space = curr_address_space
                    optimal_size = size
        remaining_address_space, allocated_subnets = allocate_space(remaining_address_space, optimal_address_space, subnet_size)
        allocated_subnets = [str(subnet) for subnet in allocated_subnets]
        if asn in all_routes_before_removing_conflicts :
            all_routes_before_removing_conflicts[asn].extend(allocated_subnets)
        else :
            all_routes_before_removing_conflicts[asn] = allocated_subnets

        new_space_allocated_to_subnets[i] = allocated_subnets
    x = number_of_subnets_in_remaining_address_space(IPSet(remaining_address_space))
        
    # print(len(list(remaining_address_space.iter_cidrs())))
    return all_routes_before_removing_conflicts, new_space_allocated_to_subnets, x

def worst_fit_algorithm(all_routes_before_removing_conflicts, subnets_to_be_changed) :
    remaining_address_space = get_remaining_address_space(all_routes_before_removing_conflicts)
    new_space_allocated_to_subnets = dict()
    # print(len(list(remaining_address_space.iter_cidrs())))
    for i in subnets_to_be_changed:
        asn, subnet, subnet_size = get_asn_subnet(i)
        optimal_address_space = None
        optimal_size = 0
        for curr_address_space in remaining_address_space.iter_ipranges():
            size = address_space_size(curr_address_space)
            if size > subnet_size :
                if not optimal_address_space or optimal_size < size :
                    optimal_address_space = curr_address_space
                    optimal_size = size
        remaining_address_space, allocated_subnets = allocate_space(remaining_address_space, optimal_address_space, subnet_size)
        allocated_subnets = [str(subnet) for subnet in allocated_subnets]
        if asn in all_routes_before_removing_conflicts :
            all_routes_before_removing_conflicts[asn].extend(allocated_subnets)
        else :
            all_routes_before_removing_conflicts[asn] = allocated_subnets

        new_space_allocated_to_subnets[i] = allocated_subnets
        
    x = number_of_subnets_in_remaining_address_space(remaining_address_space)
    # print(len(list(remaining_address_space.iter_cidrs())))
    return all_routes_before_removing_conflicts, new_space_allocated_to_subnets, x

def first_fit_algorithm(all_routes_before_removing_conflicts, subnets_to_be_changed) :
    remaining_address_space = get_remaining_address_space(all_routes_before_removing_conflicts)
    new_space_allocated_to_subnets = dict()
    # print(len(list(remaining_address_space.iter_cidrs())))
    for i in subnets_to_be_changed:
        asn, subnet, subnet_size = get_asn_subnet(i)
        optimal_address_space = None
        optimal_size = 0
        for curr_address_space in remaining_address_space.iter_ipranges():
            size = address_space_size(curr_address_space)
            if size > subnet_size :
                # if not optimal_address_space or optimal_size < size :
                optimal_address_space = curr_address_space
                optimal_size = size
                break
        remaining_address_space, allocated_subnets = allocate_space(remaining_address_space, optimal_address_space, subnet_size)
        allocated_subnets = [str(subnet) for subnet in allocated_subnets]
        if asn in all_routes_before_removing_conflicts :
            all_routes_before_removing_conflicts[asn].extend(allocated_subnets)
        else :
            all_routes_before_removing_conflicts[asn] = allocated_subnets

        new_space_allocated_to_subnets[i] = allocated_subnets
        
    x = number_of_subnets_in_remaining_address_space(remaining_address_space)
    # print(len(list(remaining_address_space.iter_cidrs())))
    return all_routes_before_removing_conflicts, new_space_allocated_to_subnets, x

def get_subnet_size(subnet):
    # Extract subnet size from ASN_subnet format
    return int(subnet.split('/')[1])

def sort_subnet_size_descending(subnets):
    # ordering in ascending order, orders all subnets based on its subnet based which is also the decreasing order of their sizes
    sorted_subnets = sorted(subnets, key=get_subnet_size, reverse=False)
    return sorted_subnets


def add_removed_subnets(all_routes, subnets_to_be_added) :
    print("__________ running best fit allocation ____________")
    subnets_to_be_added = sort_subnet_size_descending(subnets_to_be_added)
    # print("#######################")
    all_routes, allocated_subnet_spaces, x = worst_fit_algorithm(all_routes, subnets_to_be_added)    
    # print(allocated_subnet_spaces)
    new_allocated_subnets = dict()
    # TODO: remove the cost of old subnets from all_routes_util
    count_new_subnets = 0
    for (key, value) in allocated_subnet_spaces.items() :
        asn = key.split('_')[0]
        count_new_subnets += len(value)
        if asn in new_allocated_subnets :
            new_allocated_subnets[asn].extend(value)
            # print("a", str(subnet))
        else :
            new_allocated_subnets[asn] = value
            # print("b", str(subnet))
    # IPAddress_Main.gen_random_values_for_addr_types(new_allocated_subnets)
    print("# of new subnets allocated: ", count_new_subnets)
    print("__________ completed best fit allocation ___________")
    return all_routes, new_allocated_subnets, x

# Example usage:
# all_routes_before_removing_conflicts = {
#     'ASN1': [IPNetwork('192.168.1.0/24')],
#     'ASN2': [IPNetwork('10.0.0.0/16')],
#     # Add more allocated subnets as needed
# }

# subnets_to_be_changed = {
#     'ASN1': [IPNetwork('192.168.1.0/24')],
#     'ASN2': [IPNetwork('10.0.0.0/16')],
#     'ASN1': [IPNetwork('192.168.1.0/24')],
#     'ASN2': [IPNetwork('10.0.0.0/16')],
#     'ASN1': [IPNetwork('192.168.1.0/24')],
#     'ASN2': [IPNetwork('10.0.0.0/16')],
#     'ASN1': [IPNetwork('192.168.1.0/24')],
#     'ASN2': [IPNetwork('10.0.0.0/16')],
# }
# subnets = [24, 167772159]

# remaining_space = get_remaining_address_space(all_routes_before_removing_conflicts)
# for range in remaining_space.iter_ipranges():
#     print(range)
# remaining_space = best_fit_algorithm(all_routes_before_removing_conflicts, subnets)
# # print(remaining_space)
# for range in remaining_space.iter_ipranges():
#     print(range, address_space_size(range))

# cidrs = []
# for ip_range in remaining_space.iter_ipranges():
#     cidrs.extend(iprange_to_cidrs(ip_range[0], ip_range[-1]))

# print(cidrs)