import time
import threading

stop_flag = threading.Event()


class timer:
    def __init__(self, lease, T1, T2, owner) -> None:
        self.lease = lease
        self.T1 = T1
        self.T2 = T2
        self.owner = owner
        self.reset = False
        
    def start_timer(self):
        start_time = time.time()
        current_time = start_time
        stop_flag.clear()
        while current_time - start_time <= self.lease and not stop_flag.is_set():
            time_elapsed = round(current_time - start_time)
            print(f'time_elapsed:{time_elapsed}')
            self.owner.ct = time_elapsed
            self.owner.interface.set_current_lease_time(str(self.lease - time_elapsed))
            if self.T1 < time_elapsed <= self.T2 and self.T1 :
                self.owner.T1_flag = True
            if time_elapsed > self.T2:
                self.owner.T2_flag = True
            if self.reset:
                start_time = time.time()
                current_time = time.time()
                self.reset = False
                self.owner.T1_flag = False
                self.owner.T2_flag = False
            time.sleep(1)
            current_time = time.time()
                
    def reset(self):
        self.reset = True
    
    def stop(self):
        stop_flag.set()
        



    