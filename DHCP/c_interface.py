import tkinter as tk
from tkinter import StringVar, IntVar
from tkinter.messagebox import showinfo
import c


class mainPanel:
    def __init__(self):
        self.root = tk.Tk()
        
        self.root.geometry("1000x640")
        self.root.title("Client")
        self.client = c.client(self)
        
        #Variables 
        self.vars_ip = StringVar()
        self.vars_mask = StringVar()
        self.vars_lease = StringVar()
        self.vari_ip = IntVar()
        self.vari_lease = IntVar()
        
        self.vars_ip.set("")
        self.vars_mask.set("")
        self.vars_lease.set("")
        
        
        #Lables
        self.label_ip = tk.Label(self.root, text = "IP" , font = ('Arial',14), justify="center" ).place(x=30,y=30, width=56, height=28)
        self.label_mask = tk.Label(self.root, text="Mask", font=('Arial', 14), justify="center").place(x=30, y=85, width=56, height=28)
        self.label_leaseTime = tk.Label(self.root, text="Lease\nTime", font=("Arial", 14), justify="center").place(x=30, y=140, width=62, height=42)
        
        self.label_messages = tk.Label(self.root, text='Messages', font=('Arial', 12), justify='center')
        self.label_messages.place(x=710,y=20,width=100,height=30)
        
        #Entries
        self.entry_ip = tk.Entry(self.root, textvariable=self.vars_ip, font=('Arial', 12), state='readonly')
        self.entry_mask = tk.Entry(self.root,textvariable=self.vars_mask, font=('Arial', 12), state='readonly')
        self.entry_leaseTime= tk.Entry(self.root,textvariable=self.vars_lease, font=('Arial', 12), state='readonly')
        
        self.entry_ip.place(x=130, y=30, width=160, height=30)
        self.entry_mask.place(x=130, y=85, width=160, height=30)
        self.entry_leaseTime.place(x=130,y=140,width=160, height=30)
        
        self.entry_reqIP = tk.Entry(self.root, font=('Arial',12), state='disabled')
        self.entry_reqLease = tk.Entry(self.root, font=('Arial',12), state='disabled')
        
        self.entry_reqIP.place(x=190,y=375,width=170,height=30)
        self.entry_reqLease.place(x=190,y=445,width=170,height=30)
        
        #Buttons
        self.button_connect = tk.Button(self.root, text='Connect', command= self.start_client)
        self.button_disconnect = tk.Button(self.root, text = 'Disconnect', command= self.disconnect)
        self.button_reqIP = tk.Checkbutton(self.root, text="Request IP", variable=self.vari_ip, command=self.change_entryip, onvalue=1, offvalue=0)
        self.button_reqLease = tk.Checkbutton(self.root, text='Request\nLease Time', command=self.change_entrylease, variable=self.vari_lease)
        
        self.button_connect.place(x=580,y=510,width=180,height=70)
        self.button_disconnect.place(x=780,y=510,width=180,height=70)
        self.button_reqIP.place(x=30,y=360,width=150,height=60)
        self.button_reqLease.place(x=30,y=430,width=150,height=60)
        
        self.button_close = tk.Button(self.root, text='Close', command=self.close_all).place(x=30,y=550, width=70, height=30)
        
        #Text
        self.text_messages = tk.Text(self.root)
        self.text_messages.place(x=580,y=50,width=380,height=450)
        #mainLoop
        self.root.mainloop()
        
    def start_client(self):
        if c.connectionflag.is_set():
            self.client.connect()
        else:
            self.vars_ip.set("0.0.0.0")
            self.vars_mask.set("0.0.0.0")
            self.vars_lease.set("0")
            self.text_messages.insert(tk.END, "Starting Client...\n")
            if self.vari_ip.get():
                if self.vari_lease.get():
                    #Both Ip and lease are requested by the client
                    pass
                else:
                    #Ip is requested by the client
                    pass
                    
            else:
                if self.vari_lease.get():
                    #Lease is requested
                    pass
                else:
                    #Neither IP nor lease are requested
                    self.button_reqIP.configure(state='disabled')
                    self.button_reqLease.configure(state='disabled')
            self.client.start_client()
    
    def disconnect(self):
        self.button_reqIP.configure(state='normal')
        self.button_reqLease.configure(state='normal')
        self.client.disconnect()
        self.vars_ip.set("0.0.0.0")
        self.vars_mask.set("0.0.0.0")
        self.vars_lease.set("0")
    
    
    def close_all(self):
        self.root.destroy()
        try:
            self.client.sock.close()
        except Exception:
            print("Client not existing")
            
    def change_entryip(self):
        if self.vari_ip.get()==0:
            self.entry_reqIP.configure(state='disabled')
        else:
            self.entry_reqIP.configure(state='normal')
            
    def change_entrylease(self):
        if self.vari_lease.get() ==0:
            self.entry_reqLease.configure(state='disabled')
        else:
            self.entry_reqLease.configure(state='normal')
    
    def expand_text(self, text):
        self.text_messages.insert(tk.END, text)

    def set_current_ip(self, text):
        self.vars_ip.set(text)

    def set_current_mask(self, text):
        self.vars_mask.set(text)

    def set_current_lease_time(self, value):
        self.vars_lease.set(value)


if __name__ == "__main__":
    panel = mainPanel()