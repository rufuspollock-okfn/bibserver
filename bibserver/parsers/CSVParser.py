import csv

class CSVParser(object):

    def __init__(self):
        pass
        
    def parse(self, fileobj):
        d = csv.DictReader(fileobj)
        data = []
        # do any required conversions
        for row in d:
            if "author" in row:
                row["author"] = row["author"].split(",")
            if "editor" in row:
                row["editor"] = row["editor"].split(",")
            data.append(row)
        return data

