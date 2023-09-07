import math
import re

from netaddr import *

## Regex ##
IPSUBNET_ZERO = '\d{1,3}\.\d{1,3}\.\d{1,3}\.0'
IPSUBNET_MASK = '(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{2})'
IPADDR = '(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
ASN = '(\d{1,4})|(\d{1,5})'


# Read/return lines from file
def readFromFile(file):
    fileSubnets = open(file, 'r')
    lines = fileSubnets.read().splitlines()
    fileSubnets.close()
    return lines


# Write lines from file
def writeToFile(lines, filename):
    fname = open(filename, 'w')
    for l in lines:
        fname.write(str(l) + '\n')
    fname.close()


# If a subnet in the routing table without a mask '/xx',
# check the class and assign a mask according to the class
def calc_mask(subnet):
    s = subnet.split('.')
    if int(s[0]) > 0 and int(s[0]) < 127:
        return subnet + '/' + '8'
    elif int(s[0]) > 127 and int(s[0]) < 192:
        return subnet + '/' + '16'
    elif int(s[0]) >= 192 and int(s[0]) < 223:
        return subnet + '/' + '24'


#### NOT WORKING GOOD
'''
# Read line by line and use regex to match subnets/mask, hexthop, and as-path
def parse_using_regex(lines):
    Table = []
    for line in lines:
        l = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}|"
                       r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
                       r"\d{4,5}", line)  # , re.M|re.I)
        Table.append(l)
    return Table
'''


def is_valid_ip(s):
    a = s.split('.')
    if len(a) != 4:
        return False
    for x in a:
        if not x.isdigit():
            return False
        i = int(x)
        if i < 0 or i > 255:
            return False
    return True


def is_valid_cidr(s):
    a = s.split('/')
    if len(a) != 2:
        return False
    if not is_valid_ip(a[0]):
        return False
    if not a[1].isdigit():
        return False
    if a[1] < 1 and a[1] > 32:
        return False
    return True


def parse_file(fname, local_asn):
    lines = readFromFile(fname)
    # print('Number of lines routing table = {}').format(len(lines))

    new_lines = []
    for line in lines:
        i = line.index(' ', 1)
        tmp = line[i:i + 19].strip().split(' ')
        subnet = tmp[0].strip()
        path = line[i + 59:].strip()
        new_line = [str(subnet), str(path)]
        new_lines.append(new_line)

    i = len(new_lines) - 2
    while i >= 0:
        line_i = new_lines[i]

        # incorrect line
        if len(line_i[0]) < 2 and len(line_i[1]) < 3:
            # print('*  case 1  *')
            new_lines.pop(i)
            continue
        # BGP route from same ASN as the router in which we get the routing information
        if (is_valid_ip(line_i[0]) or is_valid_cidr(line_i[0])) and len(line_i[1]) < 3:
            # print('II case 2 II')
            line_i[1] = local_asn
            continue

        line_j = new_lines[i - 1]

        if len(line_i[0]) < 8 and len(line_j[1]) < 1:
            # print('### case 3 ###')
            line_i[1] = line_i[1].rstrip('i\?e ').lstrip('0').strip()
            temp_line = [line_j[0], line_i[1]]
            # print(line_i, line_j, temp_line)
            new_lines.append(temp_line)
            new_lines.pop(i)
            new_lines.pop(i - 1)
            continue

        if len(line_i[0]) < 2:
            # print('$$$$ case 4 $$$$')
            new_lines.pop(i)
            continue

        line_i[1] = line_i[1].rstrip('i\?e ').lstrip('0').strip()
        i -= 1

    for line in new_lines:
        # Deals with 192.115.248.151/3 --> should be 192.115.248.151/32
        if len(line[0]) >= 16:
            # print('*0*  case 0  *0*')
            tmp = line[0].split('/')
            bytes = tmp[0].split('.')
            if tmp[1] == '3':
                count = 0
                for byte in bytes:
                    if int(byte) > 99:
                        count += 1
                    if count >= 3:
                        tmp[1] = '32'
                        line[0] = tmp[0] + '/' + tmp[1]
                        continue
            if tmp[1] == '2':
                tmp_mask = 32 - math.log(256 - int(bytes[3]), 2)
                tmp[1] = str(int(tmp_mask))
                line[0] = tmp[0] + '/' + tmp[1]

        if not is_valid_cidr(line[0]):  # and len(line[0]) > 8:
            # print('$$$$% case 5 %$$$$')
            line[0] = calc_mask(line[0])

    return new_lines


def map_subnets_asn(lines,company):
    ASN_Subnets = dict()
    ASN_Subnets['company']= company
    for line in lines:
        subnet = line[0]
        tmp = line[1].split(' ')
        asn = tmp[len(tmp) - 1]
        if asn in ASN_Subnets:
            ASN_Subnets[asn].append(subnet)
        else:
            ASN_Subnets[asn] = [subnet]
    return ASN_Subnets


