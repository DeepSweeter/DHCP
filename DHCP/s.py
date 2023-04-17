import json
import random
import socket
import core
import math
import sys
import threading
from s_interface import mainPanel

POOL_FREE = "free"
POOL_USED = "used"

SUCCESS_THRESHOLD = 1

BUFFER_SIZE = 1024

lock = threading.Lock()

def random_chance():
    random_number = random.randint(0, 100)
    if random_number > SUCCESS_THRESHOLD:
        return True
    return False


def get_free_address(pool):
    try:
        for item in pool.items():
            if item[1][0] == POOL_FREE:
                numbers = str(item[0]).split('.')
                address = bytearray([int(numbers[0]), int(numbers[1]), int(numbers[2]), int(numbers[3])])
                return bytes(address)
        return b'\x00\x00\x00\x00'
    except:
        print("No free addresses!")


def check_address_availability(pool, address):
    if address in pool.keys():
        if pool[address][0] == POOL_FREE:
            return True
        return False

def check_if_reserved(pool, address):
    if pool[address][0] == POOL_USED:
        return True
    return False

def count_clients(pool):
    count = 0
    for item in pool.items():
        if item[1][0] == POOL_USED:
            count += 1
    return count


def set_address_used(pool, address, mac, lease):
    pool.__setitem__(address, (POOL_USED, mac, lease))


def free_address(pool, address):
    current_Mac = pool[address][1]
    last_lease_time = pool[address][2]
    pool.__setitem__(address, ("free", current_Mac, last_lease_time))


class server():
    def __init__(self, interface: mainPanel):
        self.interface = interface
        self.ip = 0
        self.port = 67
        self.buffersize = BUFFER_SIZE
        self.address_pool = {}
        self.active_offers = {}
        self.serv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bytesAddressPair = 0
        self.dns = b'\xC0\xA8\x00\x01'
        
    def init_server(self, ip, mask, lease):
        address_numbers = ip.split('.')
        self.ip = ip
        self.port = 67
        self.mask = mask
        self.default_lease = lease
        self.lease = None
        self.address_pool = {f"{address_numbers[0]}.{address_numbers[1]}.{int(address_numbers[2])+1}.{x}": ("free", "noMAC") for x in
                             range(1, int(address_numbers[3]) + self.procces_mask())}

        self.serv.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serv.bind((self.ip, self.port))
        
    def start_server(self):
        print("Starting server...")
        self.thread = threading.Thread(target=self.client_process)
        self.thread.start()

    def client_process(self, foreach=None):
        while True:
            # Listen for incoming datagrams
            try:

                self.bytesAddressPair = self.serv.recvfrom(self.buffersize)

                message = self.bytesAddressPair[0]

                received_package = core.Packet(dhcp_type=core.CONFIGURATION, configuration=message)
                print("I RECEIVED A PACKAGE!")
                print(received_package)

                client_address = self.bytesAddressPair[1]
                # Afisez adresa clientului, care a trimis mesajul, pentru debug
                # print(f"Client IP Address: {client_address}")

                for option in received_package.options.options:
                    if option[0] == int.from_bytes(core.OP_MESSAGE_TYPE, "big"):
                        message_type = option[2]
                        break
                #TODO indicatii pentru generarea pachetelor custom atunci cand exista optiunea 50 si 51
                #* creeaza o variabila noua de lease, daca ai optiunea 51 fa self.lease = lease din option altfel self.lease = self.default_lease
                
                
                self.lease = self.default_lease
                '''
                # EXPLICATII
                # De exemplu vrem sa luam din pachetul primit mesajul din optiuni
                # Cautam optiunea care are codul 56
                # Si luam valoarea
                # O optiune e o tupla cu 3 elemente, primul este codul, al doilea este lungimea si ultimul este valoarea
                received_message_option = ''
                for option in received_package.options.options:
                    if option[0] == 56:
                        received_message_option = option[2]
                        break
                '''

                self.interface.expand_text(
                    "I RECEIVED A PACKAGE OF TYPE: " + str(int.from_bytes(message_type, "big")) + "\n")
                self.interface.expand_text(received_package.__str__())

                match message_type:
                    case core.TYPE_DISCOVER:

                        # Iau adresa ceruta, optiunea 50
                        req_address = ''
                        for option in received_package.options.options:
                            if option[0] == 50:
                                req_address = core.bytesToIp(option[2])
                                break

                        # Daca clientul cere o anumita adresa
                        if req_address != '':
                            address_approved = False
                            # Caut adresa ceruta
                            if req_address in self.address_pool.keys():
                                # In cazul in care exista ii verific disponibilitatea
                                if check_address_availability(self.address_pool, req_address) is True:
                                    req_offered_address = req_address
                                    address_approved = True

                            if address_approved is True:
                                offered_address = core.ipToBytes(req_offered_address)
                            else:
                                offered_address = get_free_address(self.address_pool)
                        else:
                            # Daca nu este ceruta nicio adresa ip specifica
                            # Gasesc prima adresa disponibila pentru oferta
                            offered_address = get_free_address(self.address_pool)

                        # Creez pachetul pentru oferta
                        offer_package = core.Packet(dhcp_type=core.DHCPOFFER, configuration=message)
                        
                        # Acum incepem sa modificam pachetul de baza de tip OFFER

                        # Din pachetul precedent preiau codul tranzactiei si il copiez in cel nou
                        offer_package.xid = received_package.xid

                        # Creez un sir de biti cu adresa serverului
                        #** Se sterge la finalizare proiectului
                        # server_ip_bytes = b''
                        # ip_list = self.ip.split('.')
                        # for number in ip_list:
                        #     server_ip_bytes += int(number).to_bytes(1, "big")
                            
                        # server_mask_bytes = b''
                        # mask_list = self.mask.split('.')
                        # for number in mask_list:
                        #     server_mask_bytes += int(number).to_bytes(1, "big")
                        #**
                        #*Pentru versiunea finala a se folosi varianta de mai jos pentru ip si masca
                        server_ip_bytes = self.interface.getIpAsBytes(self.interface.entry_ip)
                        server_mask_bytes = self.interface.getIpAsBytes(self.interface.entry_mask)  
                                                  
                        # In pachetul nou setez oferata de adresa
                        offer_package.yiaddr = offered_address
                        # Modific si siaddr corespunzator cu adresa serverului
                        offer_package.siaddr = server_ip_bytes

                        # Adaugam optiuni pe langa cele default
                        # Sterg terminatorul de sir
                        offer_package.options = offer_package.options[:-1]

                        

                        
                        #* functie din clasa packet pentru a adauga o optiune
                        offer_package.add_option(54, 4, server_ip_bytes)
                        
                        offer_package.add_option(1, 4, server_mask_bytes)
                        offer_package.add_option(6, 4, self.dns)

                        req_lease = self.lease
                        for option in received_package.options.options:
                            if option[0] == 51:
                                req_lease = int.from_bytes(option[2], "big")
                                break

                        if req_lease != 0:
                            offer_package.add_option(51, 4, int(req_lease).to_bytes(4, 'big'))
                            offer_package.add_option(58, 4, int(req_lease / 2).to_bytes(4, 'big'))
                            offer_package.add_option(59, 4, int(0.875 * req_lease).to_bytes(4,'big'))

                        # Dupa ce terminam de adaugat optiunile, NU uitam de terminator
                        offer_package.options += b'\xff'

                        # Trimit pachetul, raspunsul de tip OFFER
                        #self.serv.sendto(offer_package.get_bytes_package(), client_address)
                        self.serv.sendto(offer_package.get_bytes_package(), ('<broadcast>', 68))



                        # Marchez ca am trimis o oferta respectivei adrese
                        self.active_offers[client_address[0]] = (core.bytesToIp(offered_address), req_lease)
                    case core.TYPE_REQUEST:
                        mac_client = received_package.chaddr
                        # Verific daca am o oferta activa pentru client
                        if client_address[0] in self.active_offers:
                            # Iau oferta pe care am oferit-o pentru client
                            offered_address = self.active_offers.get(client_address[0])[0]
                            req_lease = self.active_offers.get(client_address[0])[1]

                            # Sterg din ofertele active oferta
                            self.active_offers.pop(client_address[0])

                            # Daca nu este ceruta nicio adresa ip specifica
                            # Setez adresa ip oferita ca fiind folosita
                            offered_address_string = offered_address

                            set_address_used(self.address_pool, offered_address_string, mac_client, req_lease)

                            # Creez pachetul de tip ACK
                            ack_package = core.Packet(dhcp_type=core.DHCPACK, configuration=message)

                            # Din pachetul precedent preiau codul tranzactiei si il copiez in cel nou
                            ack_package.xid = received_package.xid
                            
                            ack_package.yiaddr = core.ipToBytes(offered_address)
                            ack_package.siaddr = server_ip_bytes
                            
                            ack_package.options = ack_package.options[:-1]
                            
                            ack_package.add_option(54, 4, server_ip_bytes)
                            ack_package.add_option(1, 4, server_mask_bytes)
                            ack_package.add_option(6, 4, self.dns)

                            if req_lease != 0:
                                ack_package.add_option(51, 4, int(req_lease).to_bytes(4, 'big'))
                                ack_package.add_option(58, 4, int(req_lease / 2).to_bytes(4, 'big'))
                                ack_package.add_option(59, 4, int(0.875 * req_lease).to_bytes(4,'big'))
                                
                            ack_package.options += b'\xff'

                            # Trimit pachetul, raspunsul de tip ACK
                            self.serv.sendto(ack_package.get_bytes_package(), client_address)

                            # panel.reserve_address(offered_address)
                        else:
                            found = ''
                            for item in self.address_pool.items():
                                if item[1][1] == mac_client:
                                    found = item[0]
                                    break

                            if found != '':
                                # Creez pachetul de tip ACK
                                ack_package = core.Packet(dhcp_type=core.DHCPACK, configuration=message)

                                ack_package.xid = received_package.xid

                                ack_package.yiaddr = core.ipToBytes(offered_address)
                                ack_package.siaddr = server_ip_bytes

                                ack_package.options = ack_package.options[:-1]

                                req_lease = self.lease
                                if offered_address_string in self.address_pool.keys():
                                    req_lease = (self.address_pool[offered_address_string])[2]

                                ack_package.add_option(54, 4, server_ip_bytes)
                                ack_package.add_option(1, 4, server_mask_bytes)
                                ack_package.add_option(6, 4, self.dns)
                                ack_package.add_option(51, 4, int(req_lease).to_bytes(4, 'big'))
                                ack_package.add_option(58, 4, int(round(req_lease/2)).to_bytes(4, 'big'))
                                ack_package.add_option(59, 4, int(round(0.875 * req_lease)).to_bytes(4, 'big'))
                                ack_package.options += b'\xff'

                                # self.active_offers[offered_address] = (core.bytesToIp(offered_address), req_lease)
                                set_address_used(self.address_pool, offered_address_string, mac_client, req_lease)

                                # Trimit pachetul, raspunsul de tip ACK
                                self.serv.sendto(ack_package.get_bytes_package(), client_address)
                                self.interface

                            else:
                                nack_package = core.Packet(dhcp_type=core.DHCPNACK, configuration=message)
                                nack_package.options.message = "From Server: I received a wrong REQUEST message"
                                #! Trimit pachetul, raspunsul de tip NACK
                                self.serv.sendto(nack_package.get_bytes_package(), client_address)

                    case core.TYPE_ACK:
                        pass

                    case core.TYPE_RELEASE:
                        mac_client = received_package.chaddr
                        found = ''
                        for item in self.address_pool.items():
                            if item[1][1] == mac_client:
                                found = item[0]
                                break

                        if found != '':
                            free_address(self.address_pool, found)
                            
                            self.interface.expand_text(f"Address {found} was released!")
                #!Prototip de schimbare culoare la table in functie de adresele ocupate, necesita modificari  
                tree_list = self.interface.table.get_children()
                for elem in tree_list:
                    a = self.interface.table.item(elem)
                    if check_if_reserved(self.address_pool, a['values'][0]):
                        a['values'][1] = self.address_pool[a['values'][0]][2]
                        self.interface.table.item(elem, tags=('reserved',), values=a['values'])
                       
                    else:
                        a['values'][1] = '0'
                        self.interface.table.item(elem, tags=('free',), values=a['values'])
                        
                        
                
                self.interface.table.tag_configure("reserved", background='green')
                self.interface.table.tag_configure('free', background='white')
                
                         
                self.interface.activeClients.set(str(count_clients(self.address_pool)))

            except KeyboardInterrupt:
                break

        self.serv.close()
    
    def procces_mask(self):
        parts = self.mask.split('.')
        return 254-int(parts[3])
            
        


