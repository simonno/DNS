from socket import socket, AF_INET, SOCK_DGRAM
import sys
from Cache import Cache
from Record import Record
from re import split



def main():
    # initialize the socket.
    socket_info = sys.argv[1]
    local_server_ip, port = socket_info.split(":")
    port = int(port)
    s = socket(AF_INET, SOCK_DGRAM)
    # create cache
    cache = Cache()
    cache.start_timer(4)

    # start reading query and send them to the local server.
    while True:
        query = raw_input("Enter query: ")
        if query == "stop":
            break

        _, domain_name, record_type, _ = split("[[,\]]", query)

        try:  # try to find the record in the cache.
            record = cache.get_record(domain_name, record_type)
            print "Server sent: ", record.to_json()

        except NameError:  # case didn't find:
            s.sendto(query, (local_server_ip, port))
            data, _ = s.recvfrom(2048)
            if data.startswith("Not found"):  # case the record not found.
                print "Server sent: domain not found"

            elif data.startswith("$"):  # record found.
                json_record = data[2:]
                record = Record.from_json(json_record)
                cache.add_dynamic_record(record)  # add record to cache.
                print "Server sent: ", json_record

    s.close()
    cache.stop = True


if __name__ == "__main__":
    main()
