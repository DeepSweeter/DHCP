import random
import core
import socket
import sys
import threading
import time
import timer
import select


bufferSize = 1000

#*States

INIT = 'init'
SELECTING = 'selecting'
REQUESTING = 'requesting'
BOUND = 'bound'
RENEWING = 'renewing'
REBOUNDING = 'rebounding'
INIT_REBOOT = 'init_reboot'
REBOOTING = 'rebooting'
NONE_INIT= 'none_init'

# GLock = threading.Lock()
tflag = threading.Event()
connectionflag = threading.Event()

# random MAC address
MAC = f'C{random.randint(0,9)}:D{random.randint(0,9)}:{random.randint(12,90)}:8A:8A:DC'

class client:
    def __init__(self, interface):
        self.interface = interface
        self.ip_server = "<broadcast>"
        self.port_server = 67
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.go = True
        self.initial_address = random.randrange(1, 100)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ip_address = None
        self.mask = None
        self.state = None
        self.T1 = None
        self.T2 = None
        self.lease = None
        self.T1_flag = False
        self.T2_flag = False
        self.ct = None
        self.timer_thread = None
        self.timer = None
        
        #*Possible Solution: close the current socket and start a new one when rebinding the address.
        self.sock.bind((f'127.0.2.{self.initial_address}', 68))
        #self.sock.bind(('', 68))
        

    def start_client(self):
        thread = threading.Thread(target=self.server_process)
        thread.start()

    def server_process(self):
        while True:
            try:
                if tflag.is_set():

                    #!Debug aici. 
                    #?Ca sa reproduci porneste serverul dupa da connect din client. In consola e un timer
                    #?Inainte ca timerul sa ajunga la 10 apasa disconnect in client si ar trebuii sa intre aici
                    #?Fara debug nu ajunge aici pentru un oarecare motiv
                    self.timer.stop()
                    self.timer_thread.join()
                    self.timer = None
                    release_package = core.Packet(dhcp_type=core.DHCPRELEASE)
                    release_package.ciaddr = core.ipToBytes(self.ip_address)
                    release_package.siaddr = core.ipToBytes(self.ip_server)
                    print(release_package.__str__())
                    release_package.set_mac(MAC)
                    release_package.options = release_package.options[:-1]

                    release_package.add_option(54, 4, core.ipToBytes(self.ip_server))
                    release_package.options += b'\xff'

                    self.sock.sendto(release_package.get_bytes_package(), server_address)
                    
                    while connectionflag.is_set():
                        try:
                            pass
                        except KeyboardInterrupt:
                            self.sock.close()
                            break
                    tflag.clear()
                    self.state= INIT_REBOOT
                    
                
                
                if self.state == None and self.ip_address == None:    
                    self.state = INIT
                    


                #*Init
                if self.state == INIT:
                    #* Creare pachet tip DISCOVER
                    packet = core.Packet(dhcp_type=core.DHCPDISCOVER, configuration='')
                    
                    packet.options = packet.options[:-1]
                    
                    if self.interface.vari_ip.get():
                        req_ip = self.interface.entry_reqIP.get()
                        packet.add_option(50, 4, core.ipToBytes(req_ip))
                    
                    if self.interface.vari_lease.get():
                        req_lease = self.interface.entry_reqLease.get()
                        packet.add_option(51, 4, int(req_lease).to_bytes(4, 'big'))
                        
                    packet.options += b'\xff'
                    
                    
                    bytesToSend = packet.get_bytes_package()
                    server_addr_port = (self.ip_server, self.port_server)
                    self.sock.sendto(bytesToSend, ('<broadcast>', 67))
                    print("I JUST SENT AN DHCP DISCOVER PACKAGE!")
                    print(packet.__str__())

                    self.state = SELECTING

                elif self.state == SELECTING:
                    msgFromServer = self.sock.recvfrom(bufferSize)
                    message = msgFromServer[0]
                    received_package = core.Packet(dhcp_type=core.CONFIGURATION, configuration=message)
                    server_address = msgFromServer[1]
                    # Caut optiunea cu codul pentru Message Type
                    for option in received_package.options.options:
                        if option[0] == int.from_bytes(core.OP_MESSAGE_TYPE, "big"):
                            message_type = option[2]
                            break

                     # Verific daca pachetul e de la altcineva in afara de client
                    if server_address[0] != f'127.0.1.{self.initial_address}':
                        self.interface.expand_text("I RECEIVED A PACKAGE OF TYPE: " + str(int.from_bytes(message_type, "big")) + "\n")
                        self.interface.expand_text(received_package.__str__())
                    self.state = REQUESTING

                elif self.state == REQUESTING:
                    # Creez pachetul pentru cerere
                    request_package = core.Packet(dhcp_type=core.DHCPREQUEST, configuration='')

                    print(request_package.__str__())

                    # Din pachetul precedent preiau codul tranzactiei si il copiez in cel nou
                    request_package.options = request_package.options[:-1]
                    request_package.add_option(54, 4, received_package.siaddr)
                    request_package.options += b'\xff'
                    request_package.set_mac(MAC)

                    # Trimit pachetul, raspunsul de tip REQUEST
                    self.sock.sendto(request_package.get_bytes_package(), ('<broadcast>', 67))

                    msgFromServer = self.sock.recvfrom(bufferSize)
                    message = msgFromServer[0]
                    received_package = core.Packet(dhcp_type=core.CONFIGURATION, configuration=message)
                    server_address = msgFromServer[1]

                    # Caut optiunea cu codul pentru Message Type
                    for option in received_package.options.options:
                        if option[0] == int.from_bytes(core.OP_MESSAGE_TYPE, "big"):
                            message_type = option[2]
                            break

                    # Verific daca pachetul e de la altcineva in afara de client
                    if server_address[0] != f'127.0.1.{self.initial_address}':
                        self.interface.expand_text("I RECEIVED A PACKAGE OF TYPE: " + str(int.from_bytes(message_type, "big")) + "\n")
                        self.interface.expand_text(received_package.__str__())

                    match message_type:
                        case core.TYPE_ACK:
                            # Totul e in regula, putem sa ne insusim adresa IP din oferta serverului
                            print("Am primit pachet de tip ACK")
                            print(received_package.__str__())
                            options = received_package.options.options
                            for option in options:
                                if option[0] == 51:
                                    self.lease = int.from_bytes(option[2], 'big')
                                if option[0] == 58:
                                    self.T1 = int.from_bytes(option[2], 'big')
                                if option[0] == 59:
                                    self.T2 = int.from_bytes(option[2], 'big')
                                if option[0] == 54:
                                    self.ip_server = core.bytesToIp(option[2])
                                if option[0] == 1:
                                    self.mask = core.bytesToIp(option[2])
                            self.ip_address = core.bytesToIp(received_package.yiaddr)
                            self.interface.set_current_ip(self.ip_address)
                            self.interface.set_current_mask(self.mask)
                            #TODO clientul isi schimba adrea cu cea primita. sock.close, sock.bind(new address), sock.setopt
                            self.sock.close()
                            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            #!!valoare de testare, trebuie pusa adresa primita de la server. 
                            self.sock.bind((core.bytesToIp(received_package.yiaddr), 68))
                            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            
                            
                            self.state = BOUND
                            
                        case core.TYPE_NACK:
                            # Nu am primit confirmare din partea serverului
                            print("Am primit pachet de tip NACK")
                            print(received_package.__str__())
                            self.state = INIT
                        
                        case _:
                            time.sleep(1)
                            

                elif self.state == BOUND:
                    #TODO trebuie inchis vechiul socket si facut unul nou cu adresa salvata in self.ip_address
                    if self.timer == None:
                        self.timer = timer.timer(self.lease, self.T1, self.T2, self)
                        self.timer_thread = threading.Thread(target=self.timer.start_timer)
                        self.timer_thread.start()
                        self.T1_flag = False
                    if self.T1_flag == True:
                        self.state = RENEWING

                elif self.state == RENEWING:
                    # Creez pachetul pentru cerere
                    request_rn_package = core.Packet(dhcp_type=core.DHCPREQUEST)
                    print(request_rn_package.__str__())
                    request_rn_package.flags = b'\x00\x00'
                    request_rn_package.ciaddr = core.ipToBytes(self.ip_address)
                    request_rn_package.set_mac(MAC)

                    # Din pachetul precedent preiau codul tranzactiei si il copiez in cel nou
                    #TODO trebuie adaugata optiunea server identifier
                    request_rn_package.options = request_rn_package.options[:-1]
                    
                    request_rn_package.add_option(54, 4, core.ipToBytes(self.ip_server))
                    
                    request_rn_package.options += b'\xff'

                    # Trimit pachetul, raspunsul de tip REQUEST
                    #!Unicast
                    self.sock.sendto(request_rn_package.get_bytes_package(), server_address)
                    
                    r, _, _ = select.select([self.sock], [], [], self.T2-self.T1)
                    if not r:
                        #*poate fi afisat si in interfata
                        print('Fara raspuns de la server...')
                    else:
                        msgFromServer = self.sock.recvfrom(bufferSize)
                        message = msgFromServer[0]
                        received_package = core.Packet(dhcp_type=core.CONFIGURATION, configuration=message)
                        server_address = msgFromServer[1]

                        # Caut optiunea cu codul pentru Message Type
                        for option in received_package.options.options:
                            if option[0] == int.from_bytes(core.OP_MESSAGE_TYPE, "big"):
                                message_type = option[2]
                                break

                        # Verific daca pachetul e de la altcineva in afara de client
                        if server_address[0] != f'127.0.1.{self.initial_address}':
                            self.interface.expand_text("I RECEIVED A PACKAGE OF TYPE: " + str(int.from_bytes(message_type, "big")) + "\n")
                            self.interface.expand_text(received_package.__str__())

                        match message_type:
                            case core.TYPE_ACK:
                                #* Totul e in regula, putem sa ne insusim adresa IP din oferta serverului
                                print("Am primit pachet de tip ACK")
                                print(received_package.__str__())
                                options = received_package.options.options
                                for option in options:
                                    if option[0] == 51:
                                        self.lease = int.from_bytes(option[2],'big')
                                    if option[0] == 58:
                                        self.T1 = int.from_bytes(option[2], 'big')
                                    if option[0] == 59:
                                        self.T2 = int.from_bytes(option[2], 'big')
                                    if option[0] == 54:    
                                        self.ip_server = core.bytesToIp(option[2])

                                self.timer.stop()

                                self.timer_thread.join()
                                self.timer = None
                                self.state = BOUND
                                
                            case core.TYPE_NACK:
                                #* Nu am primit confirmare din partea serverului

                                self.timer.stop()

                                self.timer_thread.join()
                                self.timer =None
                                self.ip_address = None
                                print("Am primit pachet de tip NACK")
                                print(received_package.__str__())
                                self.state = INIT
                    
                    if self.T2_flag:
                        self.state = REBOUNDING

                elif self.state == REBOUNDING:
                    # Creez pachetul pentru cerere
                    request_rb_package = core.Packet(dhcp_type=core.DHCPREQUEST)
                    print(request_rb_package.__str__())
                    request_rb_package.ciaddr = core.ipToBytes(self.ip_address)
                    request_rb_package.set_mac(MAC)

                    # Trimit pachetul, raspunsul de tip REQUEST 
                    #!Broadcast
                    self.sock.sendto(request_rb_package.get_bytes_package(), ('<broadcast>', 67))
                    
                    r, _, _ = select.select([self.sock], [], [], self.lease-self.T2)
                    if not r:
                        #*poate fi afisat si in interfata
                        print('Fara raspuns de la server')
                        self.timer.stop()
                        self.timer_thread.join()
                        self.timer=None
                        #self.state=INIT #Init e varianta corecta dar nu vreau sa reia procesul la infinit
                        self.state = INIT
                    else:
                        msgFromServer = self.sock.recvfrom(bufferSize)
                        message = msgFromServer[0]
                        received_package = core.Packet(dhcp_type=core.CONFIGURATION, configuration=message)
                        server_address = msgFromServer[1]

                        # Caut optiunea cu codul pentru Message Type
                        for option in received_package.options.options:
                            if option[0] == int.from_bytes(core.OP_MESSAGE_TYPE, "big"):
                                message_type = option[2]
                                break

                        # Verific daca pachetul e de la altcineva in afara de client
                        if server_address[0] != f'127.0.1.{self.initial_address}':
                            self.interface.expand_text("I RECEIVED A PACKAGE OF TYPE: " + str(int.from_bytes(message_type, "big")) + "\n")
                            self.interface.expand_text(received_package.__str__())

                        match message_type:
                            case core.TYPE_ACK:
                                # Totul e in regula, putem sa ne insusim adresa IP din oferta serverului
                                #TODO Trece in state-ul bound, incepe timer-ul de lease
                                print("Am primit pachet de tip ACK")
                                print(received_package.__str__())
                                options = received_package.options.options
                                for option in options:
                                    if option[0] == 51:
                                        self.lease = int.from_bytes(option[2],'big')
                                    if option[0] == 58:
                                        self.T1 = int.from_bytes(option[2], 'big')
                                    if option[0] == 59:
                                        self.T2 = int.from_bytes(option[2],'big')
                                    if option[0] == 54:    
                                        self.ip_server = core.bytesToIp(option[2])
                                self.timer.stop()
                                self.timer_thread.join()
                                self.timer=None
                                self.state = BOUND
                                
                            case core.TYPE_NACK:
                                #* Nu am primit confirmare din partea serverului
                                self.timer.stop()
                                self.timer_thread.join()
                                self.timer =None
                                self.ip_address = None
                                print("Am primit pachet de tip NACK")
                                print(received_package.__str__())
                                self.state = INIT
                            
                            case _:
                                time.sleep(self.lease - self.T2)
                #* Stare suplimentara de asteptare a clientului si de trimitiere a mesajului release

                elif self.state == INIT_REBOOT:
                    request_ir_package = core.Packet(dhcp_type=core.DHCPREQUEST)
                    request_ir_package.set_mac(MAC)
                    print(request_ir_package.__str__())

                    request_ir_package.options = request_ir_package.options[:-1]
                    
                    request_ir_package.add_option(50, 4, core.ipToBytes(self.ip_address))
                    request_ir_package.options += b'\xff'

                    # Trimit pachetul, raspunsul de tip REQUEST 
                    # !Broadcast
                    self.sock.sendto(request_ir_package.get_bytes_package(), ('<broadcast>', 67))
                    
                    self.state = REBOOTING

                elif self.state == REBOOTING:
                    r, _ ,_ = select.select([self.sock], [], [], self.lease-self.T2)
                    if not r:
                        #*poate fi afisat si in interfata
                        print('Fara raspuns de la server')
                        self.timer.stop()
                        self.timer_thread.join()
                        self.timer=None
                        #self.state=INIT #Init e varianta corecta dar nu vreau sa reia procesul la infinit
                        self.state = NONE_INIT
                    else:
                        msgFromServer = self.sock.recvfrom(bufferSize)

                        message = msgFromServer[0]

                        received_package = core.Packet(dhcp_type=core.CONFIGURATION, configuration=message)

                        server_address = msgFromServer[1]


                        # Caut optiunea cu codul pentru Message Type
                        for option in received_package.options.options:
                            if option[0] == int.from_bytes(core.OP_MESSAGE_TYPE, "big"):
                                message_type = option[2]
                                break

                        #!! Verific daca pachetul e de la altcineva in afara de client
                        if server_address[0] != f'127.0.1.{self.initial_address}':
                            self.interface.expand_text("I RECEIVED A PACKAGE OF TYPE: " + str(int.from_bytes(message_type, "big")) + "\n")
                            self.interface.expand_text(received_package.__str__())


                        match message_type:
                            case core.TYPE_ACK:
                                #* Totul e in regula, putem sa ne insusim adresa IP din oferta serverului
                                print("Am primit pachet de tip ACK")
                                print(received_package.__str__())
                                options = received_package.options.options
                                for option in options:
                                    if option[0] == 51:
                                        self.lease = int.from_bytes(option[2],'big')
                                    if option[0] == 58:
                                        self.T1 = int.from_bytes(option[2], 'big')
                                    if option[0] == 59:
                                        self.T2 = int.from_bytes(option[2],'big')
                                    if option[0] == 54:
                                        self.ip_server = core.bytesToIp(option[2])
                                        
                                self.interface.set_current_ip(self.ip_address)
                                self.interface.set_current_mask(self.mask)
                                self.state = BOUND
                                
                            case core.TYPE_NACK:
                                # Nu am primit confirmare din partea serverului
                                #TODO trece in state-ul init, reincepe procesul
                                self.timer =None
                                self.ip_address = None
                                print("Am primit pachet de tip NACK")
                                print(received_package.__str__())
                                self.state = INIT

                            case _:
                                self.state = INIT
                
            except KeyboardInterrupt:
                break
        print('Am primit 2 requesturi, si am iesit :)')
        self.close_client()

    def close_client(self):
        tflag.set()
        self.sock.close()
    
    def disconnect(self):
        tflag.set()
        self.state = NONE_INIT
        # Daca ip address nu e setat pe None, state-ul se pune in INIT
        #self.ip_address = None
        connectionflag.set()
        
    def connect(self):
        connectionflag.clear()
           


