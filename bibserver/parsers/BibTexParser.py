import string
import json

class BibTexParser(object):

    def __init__(self):
        self.string_dict = {}
        self.keys_dict = {}
        """ Dictionary of keys and their substitutions """
        self.keys_dict['KEYW'] = 'SUBJECTS'
        self.keys_dict['AUTHORS'] = 'AUTHOR'
        self.keys_dict['BIBTEX'] = 'URL_BIB'

    def parse(self, fileobj):
        instring = fileobj.read()
        d = self.read_bibstring(instring)
        j = self.list2bibjson(d)
        return j

    def read_bibstring(self, instring):  ###parses a bibtex string into a list of dictionaries
        """ Main function 
        Input is a string, interpreted as bibtex, output is a list of dictionaries.
        All text after '--BREAK--' is ignored. All keys are regularized to upper
        case, and according to substitutions in the keys_dict
        """
        dlist = []
        lines = []
        for line in string.split(instring,'\n'):
            if string.find(line,'--BREAK--') >= 0:    
                break
            else: lines = lines + [string.strip(line)]
        instring = string.join(lines,'\n')
        items = string.split('\n'+ instring,'\n@')
                #### must add the leading '\n' in case string starts with an '@'
        for item in items[1:]:
                d = self.read_bibitem(item)
                dlist = dlist + [d] 
        return dlist

    def read_bibitem(self, item):     ### returns a python dict
        d = {} 
        type_rest = string.split(item, '{' ,1)
        d['TYPE'] = string.upper(string.strip(type_rest[0]))
        try:
            rest = type_rest[1]
        except IndexError:
            d['ERROR'] = 'IndexError: nothing after first { in @' + item
            rest = ''
        if d['TYPE'] == 'STRING':
        ###### Example:   @string{AnnAP = "Ann. Appl. Probab."}
            try:
                key_val = string.split(rest,'=')
                key = string.strip(key_val[0])
                val = string.strip(key_val[1])
                val = string.strip(val[:-1])   ## strip the trailing '}'
                val = val[1:-1]                ## strip the outer quotes 
                self.string_dict[key] = val
                #print 'string_dict[', key, '] = ', val

            except IndexError:
                d['ERROR'] = 'IndexError: can\'t parse string definition in @' + item
                rest = ''
        
        else:
            comma_split = string.split(rest,',',1)
            d['CITEKEY'] = string.strip(comma_split[0])
            d['BIBTEX'] = '@' + item
            try:
                rest = comma_split[1]
            except IndexError:
                d['ERROR'] = 'IndexError: nothing after first comma in @' + item
                rest = ''
        
            count = 0
            current_field = ''
            
            # MM - this original safety net has been increased - but still applied
            # desired upper limit on number of records to parse from bibtex in one go?
            
            while count <= 100000:   ### just a safey net to avoid infinite looping if code breaks
                count = count + 1
                comma_split = string.split(rest,',',1)
                this_frag = comma_split[0]
                current_field = current_field + this_frag + ','
                (quote_count,br_count) = self.check_well_formed(current_field)
                if quote_count == 0 and br_count == 0:
                    key_val = string.split(current_field,'=',1)
                    key = key_val[0]                        
                    try:
                        val = key_val[1]
                        d[self.add_key(key)] = self.add_val(val)
                    except IndexError:
                        d[self.add_key(key)] = ''
                    current_field = ''
                elif quote_count == 0 and br_count < 0:    ###end of bibtex record
                    key_val = string.split(current_field,'=',1)
                    key = key_val[0]
                    try:
                        rest = comma_split[1]
                    except IndexError:
                        rest = ''
                    try:
                        val_comments  = string.split(key_val[1],'}')
                        val = val_comments[0] 
                        (quote_count,br_count) = test(val)
                        if br_count == 1: val = val + '}'  
                        else: val = val + ','  ## add comma to match format
                        #### problem is record can end with  either e.g.
                        #### year = 1997}
                        #### year = {1997}}
                        if string.find(key,'}') < 0:
                            d[self.add_key(key)] = self.add_val( val)
                        #d['ERROR'] = str( br_count )
                        ## putting error messages into d['ERROR'] is a good
                        ## trick for debugging
                        try:
                            comments = val_comments[1][:-1]
                            comments = string.strip(comments)
                            if comments != '':
                                d['BETWEEN_ENTRIES'] = self.add_val(comments + ',') + self.add_val(rest)
                        except: IndexError
                    except: IndexError
                    current_field = ''
                    break
                try:
                    rest = comma_split[1]
                except IndexError:
                    key_val = string.split(current_field,'=',1)
                    key = self.add_key( key_val[0] )
                    if key != '':
                        try:
                            d[key] = self.add_val( key_val[1])
                        except IndexError:
                            d[key] = ''
                    break
        ### impute year from Davis Fron to arxiv output:
        if d.has_key('EPRINT') and not d.has_key('YEAR'): 
            yy = '????'
            ss = string.split(d['EPRINT'],'/')
            if len(ss) == 2: yy = ss[1][0:2]
            if yy[0] in ['0']: d['YEAR'] = '20' + yy   ### year 2010 problem!!
            elif yy[0] in ['9']: d['YEAR'] = '19' + yy
        return d

    def check_well_formed(self, instring):  
        """Test to check if instring is well-formed value of a bibtex field:
        returns 
        ( number of double quotes mod 2, number of left braces - number right braces )
        """
        instring = string.replace(instring,'\\"','')
        quote_count = string.count(instring,'"')
        lb_count = string.count(instring,'{')
        rb_count = string.count(instring,'}')
        return (divmod(quote_count , 2)[1] ,lb_count - rb_count)

    def add_key(self, key):
        """ Add upper-cased key to keys dictionary """
        key = string.upper(string.strip(key))
        if key in self.keys_dict.keys():
            return unicode(self.keys_dict[key],'utf-8')
        else: return unicode(key,'utf-8')

    def strip_quotes(self, instring):
        """Strip double quotes enclosing string"""
        instring = string.strip(instring)
        if instring[0] == '"' and instring[-1] == '"':
            return instring[1:-1]
        else: return instring

    def strip_braces(self, instring):
        """Strip braces enclosing string"""
        instring = string.strip(instring)
        if instring[0] == '{' and instring[-1] == '}':
            return instring[1:-1]
        else: return instring

    def string_subst(self, instring):
        """ Substitute string definitions """
        for k in self.string_dict.keys():
            instring = string.replace(instring, k, self.string_dict[k])
        return instring

    def add_val(self, instring):
        """ Clean instring before adding to dictionary """
        if instring[-1] == ',': val = string.strip(instring)[:-1]  ###delete trailing ','
        else: val = instring
        val = self.strip_braces(val)
        val = self.strip_quotes(val)
        val = self.strip_braces(val)
        val = self.string_subst(val)
        return unicode(val,'utf-8')




    def list2bibjson(self, btlist):
        self.jsonObj = []
        
        has_meta = False
        meta = None
        
        for btrecord in btlist:            
            typ = btrecord.get('TYPE')
            if typ == "COMMENT" and not has_meta:
                meta = self.get_meta(btrecord)
                has_meta = True
            else:
                if typ != "STRING":
                    bibjson = self.get_bibjson_object(btrecord)
                    self.jsonObj.append(bibjson)
        
        if meta is not None:
            self.jsonObj = [meta] + self.jsonObj
        
        return self.jsonObj

    def get_meta(self, btrecord):
        meta = {}
        meta["class"] = "metadata"
        for k, v in btrecord.iteritems():
            meta[k.lower()] = v
        return meta

    def get_bibjson_object(self, btrecord):
        bibjson = {}
        
        # do any tidying required
        for k, v in btrecord.iteritems():
            if k.lower() == "author":
                if type(v) is not list:
                    v = [i.strip() for i in v.split("and")]
            if k.lower() == "editor":
                if type(v) is not list:
                    v = [i.strip() for i in v.split("and")]
            if k.lower() == "pages":
                if "-" in v:
                    p = [i.strip().strip('-') for i in v.split("-")]
                    v = p[0] + ' to ' + p[-1]
            if k.lower() == "type":
                v = v.lower()
            bibjson[k.lower()] = v
        return bibjson


