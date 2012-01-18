class BaseParser(object):
    def __init__(self, fileobj):
        if hasattr(fileobj, 'seek'):
            # Some files have Byte-order marks inserted at the start
            possible_BOM = fileobj.read(3)
            if possible_BOM != '\xef\xbb\xbf':
                fileobj.seek(0)
        self.fileobj = fileobj