import thread
import time


class Cache:
    def __init__(self):
        self.recordsDictionary = {}
        self.recordsTTL = {}
        self.stop = True

    def add_static_record(self, record):
        self.recordsDictionary[record.name] = record

    def add_dynamic_record(self, record):
        self.add_static_record(record)
        self.recordsTTL[record.name] = record.TTL

    def erase_record(self, record_name):
        del self.recordsDictionary[record_name]

    def get_record(self, record_name, record_type):
        if self.is_exist(record_name, record_type):
            return self.recordsDictionary[record_name]
        else:
            raise NameError("record not found")

    def is_exist(self, record_name, record_type):
        if record_name in self.recordsDictionary and self.recordsDictionary[record_name].type == record_type:
            return True
        else:
            return False

    def start_timer(self, delay):
        self.stop = False
        # Create two threads as follows
        thread.start_new_thread(self.ttl_timer, (delay,))

    # Define a function for the thread
    def ttl_timer(self, delay):
        while not self.stop:
            time.sleep(delay)
            for record_name in self.recordsTTL.keys():
                self.recordsTTL[record_name] -= delay
                if self.recordsTTL[record_name] <= 0:
                    self.erase_record(record_name)
                    del self.recordsTTL[record_name]
