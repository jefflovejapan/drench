import os
from collections import namedtuple


class switchboard():
    def __init__(self, dirname, filelist):
        self.dirname = dirname + '/'
        self.filelist = filelist[:]
        os.mkdir(self.dirname)
        outfile = namedtuple('destination', 'path length')
        # Need the 0 index here because ['path'] is a 1-element list

        outfiles = [outfile(open(os.getcwd() + '/' + self.dirname +
                    i['path'][0], 'w'), i['length']) for i in self.filelist]
        print outfiles
