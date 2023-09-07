# IP Consolidation




use to read routes files with lines in format --> 'asn', 'subnet'

1- subnets sizes 64 to 1024: randomly select DHCP / non-DHCP subnets for example %70/%30 --> DHCP_SUBNETS_PERCENTAGE

1.1- changing dhcp scope steps: assign a new range, change in the server, change the gateway, and restart computers

     first ip address .1 is always on the router interface for the range
     
     sometimes there are fixed (reserved with MAC) ip addresses for specific devices
     
     fixed ip addresses within the dhcp scopes are considered TYPE_2 or TYPE_3

2- randomly select active ip addressed in each subnet in order to make up subnet weights based on active addresses

2.1- consider the 5 cases below. 

    Case 1.1 and 1.2 are fixed. 
    
    Case 1.3 random select ip addresses from 1 up to %100 of the available addresses
    
    Case 2.1 and 2.2 randomly select number of active addrsses UPTO the percentages of the subnet sizes in the table below
    
    Case 3, will be marked as TYPE_0


| Case #    |  Mask     | Size      | Type 1 | Type 2 | Type 3 |
|-----------|-----------|-----------|--------|--------|--------|
| Case 1.1  |  /32      | 1         | 0      | 1*     | 0      |
| Case 1.2  |  /30      | 4         | 0      | 2*     | 0      |
| Case 1.3  |  /27 -/29 | 8-32      | 0      | 100%   | 0      |
| Case 2.1  |  /26-/22  | 64 - 1024 | 85%    | 10%    | 5%     |
| Case 2.2  |  /26-/22  | 64 - 1024 | 0%     | 80%    | 20%    |
| Case 3**  |  < /22    | > 1024    | 0      | 0      | 0      |

*-  special case for these very small subnets; /32 is a one address subnet that is used in virtual interfaces that are accessible for management, /30 is a two address subnet that usually used for point-to-point link connection.

**- large subnets usually are summary addresses

2.2- select ip addresses in each subnet based on 2.1 and mark them active

2.3- First IP address in a subnet is always Type 2

3-  construct dict for the above

    {   'table_id': 1,
        'table_name'='merging company or business unit'
        'subnets':
            {
                'subnet': x.x.x.x/x,
                'location': 'asn' OR 'table_id'
                'enabled': True/False,
                'last_seen': timestamp,
                'tags':[],
                'num_dependencies': #,  firewall, load-balancers, proxy, etc. 
                'weight': w,            sum of all actice addresses x cost of the change
                'ip_add_available':[],
                'ip_add_type_1':[],
                'ip_add_type_2':[],
                'ip_add_type_3':[],
                'log':[
                    {
                        'id': 0, 1, ...,
                        'timestamp': timestamp, 
                        'desc': such as: 'discovered', 
                                         'replaced from x to y',
                                         'disabled',
                                         'conflict detected w/(loc_id, subnet)'
                                         'sucessful split/merge processes in the consolidation'
                    }

                ]
            }, ...
    }, ...


