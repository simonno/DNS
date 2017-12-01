import json


# record class  - represent a dns record.
class Record:
    def __init__(self, name, record_type, value, ttl):
        self.TTL = ttl
        self.value = value
        self.type = record_type
        self.name = name

    def to_string(self):
        return self.name + "," + self.value + "," + self.type + "," + str(self.TTL)

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    @staticmethod
    def from_json(json_string):
        dictionary = json.loads(json_string.decode("utf-8"))
        name = str(dictionary["name"])
        record_type = str(dictionary["type"])
        value = str(dictionary["value"])
        ttl = int(dictionary["TTL"])
        return Record(name, record_type, value, ttl)
