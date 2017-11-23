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


def open_connection(domain_record, query):
    ip, port = split(":", domain_record.value)
    s = socket(AF_INET, SOCK_DGRAM)
    s.sendto(query, (ip, int(port)))
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
        self.cache.add_static_record(Record(".", "A", sys.argv[4], -1))

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
                self.socket.sendto("$ " + record.to_json(), query_sender_info)
            except NameError:
                print "record isn't in cache"
                sub_domain_record = self.find_sub_domain_record(domain_name)
                if self.resolver:
                    self.resolver_function(sub_domain_record, query, query_sender_info)
                else:
                    self.socket.sendto("% " + sub_domain_record.to_json(), query_sender_info)

    def find_sub_domain_record(self, domain_name):
        index = domain_name.find(".")
        sub_domain = domain_name[index + 1:]
        while not self.cache.is_exist(sub_domain, "NS") and len(sub_domain) > 0 and index > 0:
            index = sub_domain.find(".")
            sub_domain = sub_domain[index + 1:]
        if index < 0:
            sub_domain = "."  # root domain
        return self.cache.get_record(sub_domain, "NS")

    def resolver_function(self, record, query, query_sender_info):
        while True:
            data = open_connection(record, query)
            json_record = data[2:]
            data_record = Record.from_json(json_record)
            self.cache.add_dynamic_record(data_record)

            if data.startswith("%"):
                record = data_record
                continue

            elif data.startswith("$"):
                self.socket.sendto(data, query_sender_info)
                break


if __name__ == "__main__":
    Server().run_server()
