import tkinter as tk
from tkinter import ttk, StringVar
from tkinter.messagebox import showinfo
import s

debug = False

class mainPanel:
    def __init__(self):
        self.root = tk.Tk()
        
        self.root.geometry("1000x640")
        self.root.title("Server")
        self.state = False

        
        self.server = s.server(self)
        
        #Variable Strings
        self.string_OnOff = StringVar()
        self.lease_var = StringVar()
        self.activeClients = StringVar()
        self.activeClients.set('0')
        self.string_OnOff.set("OFF")
        self.lease_var.set('20')
        
        #Labels
        self.label_ip = tk.Label(self.root, text = "IP" , font = ('Arial',14), justify="center" )
        self.label_mask = tk.Label(self.root, text = "Mask", font = ('Arial',14), justify = "center")
        
        self.label_ip.place(x=30, y=50, width=56, height=28)
        self.label_mask.place(x=30, y= 80, width=56, height=28)
        
        self.label_NoOfClients = tk.Label(self.root, font=('Arial', 10), justify='center', text="Number of\nactive clients").place(x=10, y = 110, width=120, height=40)
        self.label_ActiveClients = tk.Label(self.root, font=('Arial', 12), justify='center', textvariable=self.activeClients)
        self.label_ActiveClients.place(x=130,y=105, width=50, height=50)
        
        self.label_OnOff = tk.Label(self.root,textvariable=self.string_OnOff, font=('Arial', 10), justify='center').place(x=50,y=550,width=55,height=15)
        
        self.label_messages = tk.Label(self.root, text="Messages", font=('Arial', 10), justify='left').place(x = 30, y = 160, width=80, height=30)
        
        self.label_AddrPool = tk.Label(self.root, text = "Address pool", justify="center", font=('Arial', 10)).place(x=750, y = 10, width=100, height=35)
        
        self.label_lease = tk.Label(self.root, text='Default Lease Time', justify='center', font=('Arial', 10)).place(x= 140, y=550, width=140, height=15)
        
        #Entries
        
        self.entry_ip = tk.Entry(self.root, font=('Arial', 12))
        self.entry_mask = tk.Entry(self.root, font=('Arial', 12))
        self.entry_lease = tk.Entry(self.root, font=('Arial', 12), textvariable=self.lease_var)
        
        self.entry_ip.place(x=130, y=50, width=160, height=22)
        self.entry_mask.place(x=130, y=80, width=160, height=22)
        self.entry_lease.place(x=140,y=580, width=100, height=30)  

        #Buttons
        self.button_OnOff = tk.Button(self.root, text='Start/Stop', command=self.start_server).place(x=30,y=580,width=100,height=30)
        self.button_close = tk.Button(self.root, text="Close", command=self.close_all).place(x=790,y=550,width=180,height=70)
        #Table
        
        self.table = self.create_table()
        
        #Text
        self.text_messages = tk.Text(self.root)
        self.text_messages.place(x=30, y=190, width=400, height=350)
        
        
        #Loop
        self.root.mainloop()
        
    
    def start_server(self):
        #Server starting. Probably there will be an instance of server in init
        #Populating the Table with addresses based on the mask
        if debug is True:
            ip = '127.0.0.1'
            mask = '255.255.255.127'
        else:
            ip = self.entry_ip.get()
            mask = self.entry_mask.get()

        parts = ip.split('.')
        if not self.state:
            if len(ip)!=0 and len(parts) == 4 and all(0<=int(part)<256 for part in parts):
                parts = mask.split('.')
                if len(mask)!=0 and len(parts) == 4 and all(0<= int(part) < 256 for part in parts):
                    #Start server
                    self.state = True
                    self.string_OnOff.set("ON")
                    self.server.init_server(ip, mask, int(self.lease_var.get()))
                    self.server.start_server()
                    entries = []
                    
                    #populating table
                    for addr in self.server.address_pool:
                        entries.append((f'{addr}', f'0'))

                    for entry in entries:
                        self.table.insert('',tk.END, values= entry)
                           

                else:
                    showinfo(title="Error", message="Mask invalid")
            else:
                showinfo(title="Error", message="IP invalid")
        
        else:
            self.state = False
            self.string_OnOff.set("OFF")
            
    
    def create_table(self):
        columns = ('ip','lease_time')
        tree = ttk.Treeview(self.root, columns=columns, show='headings')
        
        tree.heading('ip', text='IP')
        tree.heading('lease_time', text='Lease Time')
        
        tree.grid(row=0, column=0, sticky='news')
        
        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=0, sticky='ns')
        
        tree.place(x=550, y = 40, width=370, height=490)
        scrollbar.place(x=920,y=40,height=490)
        
        return tree
    
    def close_all(self):
        self.root.destroy()
        try:
            self.server.serv.close()
        except Exception:
            print("Server not opened")
        
    def expand_text(self, text):
        self.text_messages.insert(tk.END, text)
    
    #* Merge cum trebuie, doar ca nu in modul debug codat
    def getIpAsBytes(self, entry = tk.Entry):
        server_ip_bytes  = b''
        ip_list = entry.get().split('.')
        if len(ip_list) == 4 and all(0<=int(part)<256 for part in ip_list):
            for number in ip_list:
                server_ip_bytes += int(number).to_bytes(1, 'big')
            return server_ip_bytes


if __name__ == "__main__":
    panel = mainPanel()
