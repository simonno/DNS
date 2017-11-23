from socket import socket, AF_INET, SOCK_DGRAM
from Cache import Cache
from Record import Record
from re import split
import sys


def initialize_socket(ip, port):
    s = socket(AF_INET, SOCK_DGRAM)
    source_ip = ip
    source_port = port
    s.bind((source_ip, source_port))
    return s


def open_connection(ip, port, query):
    s = socket(AF_INET, SOCK_DGRAM)
    s.sendto(query, (ip, port))
    data, sender_info = s.recvfrom(2048)
    s.close()
    return data


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

    def run_server(self):
        self.cache.start_timer(4)
        while True:
            # get query
            query, query_sender_info = self.socket.recvfrom(2048)
            _, domain_name, record_type, _ = split("[[,\]]", query)
            print domain_name + " " + record_type

            try:
                record = self.cache.get_record(domain_name, record_type)
                print "record is in cache"
                self.socket.sendto("$+" + record.to_json(), query_sender_info)
            except NameError:
                print "record isn't in cache"
                ns_record, a_record = self.find_sub_domain_record(domain_name)

                if self.resolver:
                    self.resolver_function(a_record, query, query_sender_info)
                else:
                    self.socket.sendto("%+" + ns_record.to_json() + "+" + a_record.to_json(), query_sender_info)

    def find_sub_domain_record(self, domain_name):
        index = domain_name.find(".")
        sub_domain = domain_name[index + 1:]
        while not self.cache.is_exist(sub_domain, "NS") and len(sub_domain) > 0 and index > 0:
            index = sub_domain.find(".")
            sub_domain = sub_domain[index + 1:]
        if index < 0:
            sub_domain = "."  # root domain
            return None, self.cache.get_record(sub_domain, "A")

        else:
            ns_record = self.cache.get_record(sub_domain, "NS")
            a_record = self.cache.get_record(ns_record.value, "A")
            return ns_record, a_record

    def resolver_function(self, record, query, query_sender_info):
        while True:
            ip, port = split(":", record.value)
            data = open_connection(ip, int(port), query)
            args = data.split("+")

            if args[0] is "%":
                self.cache.add_dynamic_record(Record.from_json(args[1]))
                record = Record.from_json(args[2])
                self.cache.add_dynamic_record(record)
                continue

            elif args[0] is "$":
                self.cache.add_dynamic_record(Record.from_json(args[1]))
                self.socket.sendto(data, query_sender_info)
                break


if __name__ == "__main__":
    Server().run_server()
