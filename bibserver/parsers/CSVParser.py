import csv
from bibserver.parsers import BaseParser

class CSVParser(BaseParser):

    def parse(self):
        #dialect = csv.Sniffer().sniff(fileobj.read(1024))
        d = csv.DictReader(self.fileobj)
        data = []

        # do any required conversions
        for row in d:
            if "author" in row:
                row["author"] = row["author"].split(",")
            if "editor" in row:
                row["editor"] = row["editor"].split(",")
            data.append(row)
        return data, {}

