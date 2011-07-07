import json

class BibTex2BibJSON(object):

    def list2bibjson(self, btlist, location=None, collection=None):
        jsonObj = []
        
        has_meta = False
        meta = None
        
        for btrecord in btlist:            
            bibtype = btrecord.get('BIBTYPE')
            if bibtype == "COMMENT" and not has_meta:
                meta = self.get_meta(btrecord)
                meta['location'] = location
                meta['collection'] = collection
                has_meta = True
            else:
                bibjson = self.get_bibjson_object(btrecord)
                bibjson['location'] = location
                bibjson['collection'] = collection
                jsonObj.append(bibjson)
        
        if meta is not None:
            jsonObj = [meta] + jsonObj
        
        srlzd = json.dumps(self.jsonObj, indent=2)
        return srlzd

    def get_meta(self, btrecord):
        meta = {}
        meta["class"] = "metadata"
        for k, v in btrecord.iteritems():
            meta[k.lower()] = v
        return meta
        
    def get_bibjson_object(self, btrecord):
        bibjson = {}
        
        for k, v in btrecord.iteritems():
            bibjson[k.lower()] = v
        return bibjson

if __name__ == "__main__":
    from parsers.BibTexParser import BibTexParser
    f = open("test/bibserver.bib")
    instring = f.read()
    f.close()
    btp = BibTexParser()
    blist = btp.parse(instring)
    b2j = BibTex2BibJSON()
    j = b2j.list_to_bibjson(blist, "http://localhost/")
    f = open("test/bib.json", "w")
    f.write(j)
    f.close()
