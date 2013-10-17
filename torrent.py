# Simple torrent class. Creates attributes from a dictionary of kwargs
# Preprocessing of the .torrent performed with bencode


class torrent():

    def __init__(self, *args, **kwargs):
        while kwargs:
            item = kwargs.popitem()
            key = str(item[0]).replace(' ', '_')
            setattr(self, key, item[1])
