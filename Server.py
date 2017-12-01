from socket import socket, AF_INET, SOCK_DGRAM
from Cache import Cache
from Record import Record
from re import split
import sys


# initialize the sockets of the sever.
def initialize_socket(ip, port):
    s = socket(AF_INET, SOCK_DGRAM)
    source_ip = ip
    source_port = port
    s.bind((source_ip, source_port))
    return s


# open connection with another server and send him a query, return the data that has been sent back.
def open_connection(ip, port, query):
    s = socket(AF_INET, SOCK_DGRAM)
    s.sendto(query, (ip, port))
    data, sender_info = s.recvfrom(2048)
    s.close()
    return data


# create a ca cache for the server and add the record from the file.
def create_cache(records_file_name):
    cache = Cache()
    records_table = open(records_file_name, "r")
    for line in records_table:
        cache.add_static_record(Record.from_json(line))
    records_table.close()
    return cache


class Server:
    def __init__(self):
        socket_info = sys.argv[1]
        ip, port = split(":", socket_info)

        self.resolver = bool(int(sys.argv[2]))
        self.cache = create_cache(sys.argv[3])
        self.socket = initialize_socket(ip, int(port))
        self.cache.add_static_record(Record(".", "A", sys.argv[4], 4000))

    # run the server function.
    def run_server(self):
        self.cache.start_timer(4)
        while True:
            # get query
            query, query_sender_info = self.socket.recvfrom(2048)
            _, domain_name, record_type, _ = split("[[,\]]", query)
            print domain_name + " " + record_type

            try:  # try to find the record in the cache.
                record = self.cache.get_record(domain_name, record_type)
                print "record is in cache"
                self.socket.sendto("$+" + record.to_json(), query_sender_info)
            except NameError:  # case didn't find:
                print "record isn't in cache"
                ns_record, a_record = self.find_sub_domain_record(domain_name)

                if self.resolver:
                    self.resolver_function(a_record, query, query_sender_info)
                else:
                    json_ns_record = "Not found"
                    if ns_record is not None:
                        json_ns_record = ns_record.to_json()

                    self.socket.sendto("%+" + json_ns_record + "+" + a_record.to_json(), query_sender_info)

    # find the sub domain of the needed record.
    def find_sub_domain_record(self, domain_name):
        index = domain_name.find(".")
        sub_domain = domain_name[index + 1:]
        while not self.cache.is_exist(sub_domain, "NS") and len(sub_domain) > 0 and index > 0:
            index = sub_domain.find(".")
            sub_domain = sub_domain[index + 1:]
        if index < 0:
            return None, self.cache.get_record(".", "A")  # root domain

        else:
            ns_record = self.cache.get_record(sub_domain, "NS")
            a_record = self.cache.get_record(ns_record.value, "A")
            return ns_record, a_record

    # run the resolver function
    def resolver_function(self, record, query, query_sender_info):
        while True:
            ip, port = split(":", record.value)
            data = open_connection(ip, int(port), query)
            args = data.split("+")

            if args[0] is "%":
                if args[1] == "Not found":  # case the record didnt found sent - "Not found".
                    self.socket.sendto("Not found", query_sender_info)
                    return
                else:
                    # add glue records to the cache and keep searching.
                    record = Record.from_json(args[1])
                    self.cache.add_dynamic_record(record)
                    record = Record.from_json(args[2])
                    self.cache.add_dynamic_record(record)
                    continue

            elif args[0] is "$": # found the record -  send to the client.
                self.cache.add_dynamic_record(Record.from_json(args[1]))
                self.socket.sendto(data, query_sender_info)
                return


if __name__ == "__main__":
    Server().run_server()
