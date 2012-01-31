import cStringIO
import chardet

class BaseParser(object):
    def __init__(self, fileobj):
        data = fileobj.read()
        self.encoding = chardet.detect(data).get('encoding', 'ascii')

        # Some files have Byte-order marks inserted at the start
        if data[:3] == '\xef\xbb\xbf':
            data = data[3:]
        self.fileobj = cStringIO.StringIO(data)