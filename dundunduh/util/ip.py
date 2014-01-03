# -*- coding: utf-8 -*-

import socket
import struct
import re


def ipv4_dotted_to_integer(dotted_address):
    try:
        return struct.unpack("!I", socket.inet_aton(dotted_address))[0]
    except:
        return 0


def ipv4_integer_to_dotted(integer_address):
    return socket.inet_ntoa(struct.pack("!I", integer_address))


DOTTED_IPV4_MATCHER = re.compile(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$')


def extract_remote_ip_from_headers(headers):
    '''Get the remote IP from a list of headers, or None if not found.'''

    headers_to_search = (
        'X-FORWARDED-FOR',
        'X-CLIENT-IP',
        'CLIENT-IP',
        'X-REAL-IP',
        'REMOTE-ADDR'
    )

    for header in headers_to_search:
        for real_header in headers.keys():
            if header.lower() == real_header.lower():
                # Some of these are in the format of "client,proxy1,proxy2" so process them in order
                addrs = headers[real_header].split(',')

                for address in addrs:
                    address = address.strip()

                    if not DOTTED_IPV4_MATCHER.match(address):  # Does it even look like an IPv4 address?
                        continue

                    splits = address.split('.')

                    # check reserved range 10.0.0.0 - 10.255.255.255
                    if splits[0] == "10":
                        continue

                    # check reserved range 172.16.0.0 - 172.31.255.255
                    if splits[0] == "172" and int(splits[1]) > 15 and int(splits[1]) < 32:
                        continue

                    # check reserved range 192.168.0.0 - 192.168.255.255
                    if splits[0] == "192" and splits[1] == "168":
                        continue

                    return address

    return None
