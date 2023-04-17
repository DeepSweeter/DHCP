import random
import json
from struct import *

CONFIGURATION = 'configuration'

# The client sends a DHCPDISCOVER packet
DHCPDISCOVER = 'discover'

# The DHCP server responds by sending a DHCPOFFER packet
DHCPOFFER = 'offer'

# The DHCP server responds to the DHCPREQUEST with a DHCPACK
DHCPACK = 'acknowledge'

#
DHCPNACK = 'notacknowledge'

# The client responds to the DHCPOFFER by sending a DHCPREQUEST
DHCPREQUEST = 'request'

DHCPRELEASE = 'release'

TYPE_DISCOVER = b'\x01'
TYPE_OFFER = b'\x02'
TYPE_REQUEST = b'\x03'
TYPE_ACK = b'\x05'
TYPE_NACK = b'\x06'
TYPE_RELEASE = b'\x07'

OP_SUBNET_MASK = b'\x01'  # option 1
OP_DEFAULT_ROUTER = b'\x03'  # option 3
OP_DNS = b'\x06'  # option 6 Domain Name Server
OP_HOST_NAME = b'\x0C'  # option 12
OP_DOMAIN_NAME = b'\x0F'  # option 15 Domain Name
OP_REQUESTED_ADDRESS = b'\x32'  # option 50 Requested IP Address
OP_REQUESTED_LEASE_TIME = b'\x33'  # option 51 IP address lease option
OP_MESSAGE_TYPE = b'\x35'  # option 53
OP_MESSAGE = b'\x38'  # option 56
OP_CLIENT_IDENTIFIER = b'\x3D'  # option 61 MAC address of the client
OP_PARAMETER_REQUEST_LIST = b'\x37' #option 55 The parameters requested by the client

OP_END = b'\xff'  # opt 255

class Options:
    def __init__(self, options_text):
        self.options = []
        if options_text != '':
            options_list = list(options_text)
            current_index = 0
            while options_list[current_index] != 255:
                current_option = []

                current_option_id = options_list[current_index]

                current_option.append(current_option_id)
                current_index += 1

                current_option_len = options_list[current_index]
                current_option.append(current_option_len)
                current_index += 1

                current_option_value = options_text[current_index: current_index + current_option_len]

                current_index += current_option_len

                current_option.append(current_option_value)

                self.options.append(current_option)

    def __str__(self):
        text = ''
        for op in self.options:
            text += f"Code:{op[0]} Value:{str(op[2])} \n"
        return text


class Packet(object):
    def __init__(self, dhcp_type: str, configuration=None):
        self.op = None  # Op code
        self.htype = None  # Hardware Type
        self.hlen = None  # Hardware Address Length
        self.hops = None  # Hops
        self.xid = None  # Transaction ID
        self.secs = None  # Seconds
        self.flags = None  # Flags
        self.ciaddr = None  # Client address
        self.yiaddr = None  # Your address
        self.siaddr = None  # Server address
        self.giaddr = None  # Relay address
        self.chaddr = None  # Client Eth address
        self.sname = None  # Server Host Name
        self.file = None  # Boot File Name
        self.magic_cookie = None
        self.options = None
        match dhcp_type:
            case 'discover':
                self.dhcp_discover()
            case 'request':
                self.dhcp_request()
            case 'offer':
                self.dhcp_offer()
            case 'acknowledge':
                self.dhcp_ack()
            case 'notacknowledge':
                self.dhcp_nack()
            case 'release':
                self.dhcp_release()
            case "configuration":
                if configuration != '':
                    self.dhcp_configuration(configuration)

    def dhcp_discover(self):
        self.op = b'\x01'
        self.htype = b'\x01'
        self.hlen = b'\x06'
        self.hops = b'\x00'
        self.xid = random.randbytes(4)
        self.secs = b'\x00'
        self.flags = b'\x80\x00'
        self.ciaddr = b'\x00\x00\x00\x00'
        self.yiaddr = b'\x00\x00\x00\x00'
        self.siaddr = b'\x00\x00\x00\x00'
        self.giaddr = b'\x00\x00\x00\x00'
        self.chaddr = bytes('C3:D2:70:8A:8A:DC', 'ascii') + b'\x00' * 10
        self.sname = b'\x00' * 64
        self.file = b'\x00' * 128
        self.magic_cookie = b'\x63\x82\x53\x63'

        message = bytes("I want to configure my parameters", 'ASCII')
        message_len = len(message)

        message_type_option = OP_MESSAGE_TYPE + b'\x01' + TYPE_DISCOVER
        message_option = OP_MESSAGE + message_len.to_bytes(1, 'big') + message
        #message_ci = OP_CLIENT_IDENTIFIER + b'\x07' + self.htype + bytes('C3:D2:70:8A:8A:DC', 'ascii')
        message_parameters = OP_PARAMETER_REQUEST_LIST + b'\x02' + OP_SUBNET_MASK + OP_DNS
        
        self.options = message_type_option + message_option + message_parameters + OP_END

    def dhcp_offer(self):
        self.op = b'\x02'
        self.htype = b'\x01'
        self.hlen = b'\x06'
        self.hops = b'\x00'
        self.xid = b'\x00'
        self.secs = b'\x00'
        self.flags = b'\x80\x00'
        self.ciaddr = b'\x00\x00\x00\x00'
        self.yiaddr = b'\x00\x00\x00\x00'
        self.siaddr = b'\x00\x00\x00\x00'
        self.giaddr = b'\x00\x00\x00\x00'
        self.chaddr = bytes('C3:D2:70:8A:8A:DC', 'ASCII') + b'\x00' * 10
        self.sname = b'\x00' * 64
        self.file = b'\x00' * 128
        self.magic_cookie = b'\x63\x82\x53\x63'

        message = bytes("Hi client, this is my offer for you", 'ASCII')
        message_len = len(message)

        message_type_option = OP_MESSAGE_TYPE + b'\x01' + TYPE_OFFER
        message_option = OP_MESSAGE + message_len.to_bytes(1, 'big') + message

        self.options = message_type_option + message_option + OP_END

        # self.options.lease_time = '0:01:00'

    def dhcp_request(self):
        # broadcast
        self.op = b'\x01'
        self.htype = b'\x01'
        self.hlen = b'\x06'
        self.hops = b'\x00'
        self.xid = random.randbytes(4)
        self.secs = b'\x00'
        self.flags = b'\x80\x00'
        self.ciaddr = b'\x00\x00\x00\x00'
        self.yiaddr = b'\x00\x00\x00\x00'
        self.siaddr = b'\x00\x00\x00\x00'
        self.giaddr = b'\x00\x00\x00\x00'
        self.chaddr = bytes('C3:D2:70:8A:8A:DC', 'ASCII') + b'\x00' * 10
        self.sname = b'\x00' * 64
        self.file = b'\x00' * 128
        self.magic_cookie = b'\x63\x82\x53\x63'

        message = bytes("Yes! I accept the offer, give me the address", 'ASCII')
        message_len = len(message)

        message_type_option = OP_MESSAGE_TYPE + b'\x01' + TYPE_REQUEST
        message_option = OP_MESSAGE + message_len.to_bytes(1, 'big') + message
       # message_ci = OP_CLIENT_IDENTIFIER + b'\x07' + self.htype + bytes('C3:D2:70:8A:8A:DC', 'ascii')
        message_parameters = OP_PARAMETER_REQUEST_LIST + b'\x02' + OP_SUBNET_MASK + OP_DNS
        
        self.options = message_type_option + message_option + message_parameters + OP_END

    def dhcp_ack(self):
        self.op = b'\x02'
        self.htype = b'\x01'
        self.hlen = b'\x06'
        self.hops = b'\x00'
        self.xid = b'\x00'
        self.secs = b'\x00'
        self.flags = b'\x00\x00'
        self.ciaddr = b'\x00\x00\x00\x00'
        self.yiaddr = b'\x00\x00\x00\x00'
        self.siaddr = b'\x00\x00\x00\x00'
        self.giaddr = b'\x00\x00\x00\x00'
        self.chaddr = bytes('C3:D2:70:8A:8A:DC', 'ASCII') + b'\x00' * 10
        self.sname = b'\x00' * 64
        self.file = b'\x00' * 128
        self.magic_cookie = b'\x63\x82\x53\x63'

        message = bytes("The dynamic configuration was successful", 'ASCII')
        message_len = len(message)

        message_type_option = OP_MESSAGE_TYPE + b'\x01' + TYPE_ACK
        message_option = OP_MESSAGE + message_len.to_bytes(1, 'big') + message

        self.options = message_type_option + message_option + OP_END

    def dhcp_nack(self):
        self.op = b'\x02'
        self.htype = b'\x01'
        self.hlen = b'\x06'
        self.hops = b'\x00'
        self.xid = b'\x00'
        self.secs = b'\x00'
        self.flags = b'\x00\x00'
        self.ciaddr = b'\x00\x00\x00\x00'
        self.yiaddr = b'\x00\x00\x00\x00'
        self.siaddr = b'\x00\x00\x00\x00'
        self.giaddr = b'\x00\x00\x00\x00'
        self.chaddr = bytes('C3:D2:70:8A:8A:DC', 'ASCII') + b'\x00' * 10
        self.sname = b'\x00' * 64
        self.file = b'\x00' * 128
        self.magic_cookie = b'\x63\x82\x53\x63'

        message = bytes("The dynamic configuration failed", 'ASCII')
        message_len = len(message)

        message_type_option = OP_MESSAGE_TYPE + b'\x01' + TYPE_NACK
        message_option = OP_MESSAGE + message_len.to_bytes(1, 'big') + message

        self.options = message_type_option + message_option + OP_END

    def dhcp_release(self):
        self.op = b'\x01'
        self.htype = b'\x01'
        self.hlen = b'\x06'
        self.hops = b'\x00'
        self.xid = random.randbytes(4)
        self.secs = b'\x00'
        self.flags = b'\x80\x00'
        self.ciaddr = b'\x00\x00\x00\x00'
        self.yiaddr = b'\x00\x00\x00\x00'
        self.siaddr = b'\x00\x00\x00\x00'
        self.giaddr = b'\x00\x00\x00\x00'
        self.chaddr = bytes('C3:D2:70:8A:8A:DC', 'ascii') + b'\x00' * 10
        self.sname = b'\x00' * 64
        self.file = b'\x00' * 128
        self.magic_cookie = b'\x63\x82\x53\x63'

        message = bytes("I want to cut the connection", 'ASCII')
        message_len = len(message)

        message_type_option = OP_MESSAGE_TYPE + b'\x01' + TYPE_RELEASE
        message_option = OP_MESSAGE + message_len.to_bytes(1, 'big') + message

        self.options = message_type_option + message_option + OP_END

    def set_mac(self, mac_text):
        self.chaddr = bytes(mac_text, 'ascii') + b'\x00' * 10

    def dhcp_configuration(self, configuration):
        length = len(configuration) - 240
        pformat = 'cccc4s2s2s4s4s4s4s16s64s128s4s' + str(length) + 's'
        unpacked = unpack(pformat, configuration)
        # res = json.loads(configuration)
        self.op = unpacked[0]
        self.htype = unpacked[1]
        self.hlen = unpacked[2]
        self.hops = unpacked[3]
        self.xid = unpacked[4]
        self.secs = unpacked[5]
        self.flags = unpacked[6]
        self.ciaddr = unpacked[7]
        self.yiaddr = unpacked[8]
        self.siaddr = unpacked[9]
        self.giaddr = unpacked[10]
        self.chaddr = unpacked[11]
        self.sname = unpacked[12]
        self.file = unpacked[13]
        self.magic_cookie = unpacked[14]
        a = Options(unpacked[15])
        self.options = a

    def get_bytes_package(self):
        # a = {key: value.__str__() for key, value in self.__dict__.items()}
        # b = json.dumps(a)

        options_len = len(self.options)  # .__len__()
        pformat = 'cccc4s2s2s4s4s4s4s16s64s128s4s' + str(options_len) + 's'
        package = pack(pformat,
                       self.op,
                       self.htype,
                       self.hlen,
                       self.hops,
                       self.xid,
                       self.secs,
                       self.flags,
                       self.ciaddr,
                       self.yiaddr,
                       self.siaddr,
                       self.giaddr,
                       self.chaddr,
                       self.sname,
                       self.file,
                       self.magic_cookie,
                       # bytes(self.options.getDictionaryString(), 'ascii'))
                       self.options)
        return package

    def __str__(self):
        text = ''
        a = {key: value for key, value in self.__dict__.items()}
        for item in a.items():
            text += item[0] + ":" + item[1].__str__() + "\n"
        return text

    def getDictionaryString(self):
        a = {key: str(value) for key, value in self.__dict__.items()}
        b = json.dumps(a)
        return b.__str__()
    
    #* Option si length trebuie sa fie de tip int iar data de tip bytes
    def add_option(self, option, length, data):
        option = int(option).to_bytes(1, "big") + \
                 int(length).to_bytes(1, "big") + \
                 data
        self.options += option

def ipToBytes( ip):
    server_ip_bytes = b''
    ip_list = ip.split('.')
    if len(ip_list) == 4 and all(0 <= int(part) < 256 for part in ip_list):
        for number in ip_list:
            server_ip_bytes += int(number).to_bytes(1, 'big')
        return server_ip_bytes

def bytesToIp( byte):
    s_list = list(byte)
    return f'{s_list[0]}.{s_list[1]}.{s_list[2]}.{s_list[3]}'