import os


class switchboard():
    def __init__(self, dirname, filelist):
        self.dirname = dirname + '/'
        self.filelist = filelist[:]
        os.mkdir(self.dirname)
        self.outfile = open(os.getcwd() + '/' + self.dirname + 'muff.txt', 'w')
        self.outfile.write('o hai')
        self.outfile.close()
        print 'created switchboard'
