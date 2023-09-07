from netaddr import *


# from IPAddressMain import *

# N = 512


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
