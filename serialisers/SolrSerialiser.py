from lxml import etree

class SolrSerialiser(object):
    
    def add_field(self, doc, record, source_field, target_field, split_by=None, replace=None):
        if record.has_key(source_field) and record[source_field] != "":
            if split_by is None:
                value = self.sanitise(record[source_field], replace)
                self.add_child_element(doc, record, target_field, value)
            else:
                bits = record[source_field].split(split_by)
                for bit in bits:
                    value = self.sanitise(bit, replace)
                    self.add_child_element(doc, record, target_field, bit)

    def add_child_element(self, doc, record, target_field, value):
        child = etree.SubElement(doc, "field")
        child.set("name", target_field)
        child.text = value

    def sanitise(self, value, replace):
        if replace is None:
            return value
        for before, after in replace:
            value = value.replace(before, after)
        return value

    def serialise(self, bibdataset):
        add = etree.Element("add")
        d = bibdataset.datalist
        for record in d:
            doc = etree.SubElement(add, "doc")
            # VOLUME
            self.add_field(doc, record, "VOLUME", "volume")

            # ISSN
            self.add_field(doc, record, "ISSN", "issn")

            # TITLE
            self.add_field(doc, record, "TITLE", "title")

            # JOURNAL
            self.add_field(doc, record, "JOURNAL", "journal")

            # AUTHOR(S)
            self.add_field(doc, record, "AUTHOR", "author", split_by=" and ")

            # CITEKEY
            self.add_field(doc, record, "CITEKEY", "id", replace=[(".", "_"), ("/", "_")]) # blacklight hack, just for show

        return etree.tostring(add, pretty_print=True)
