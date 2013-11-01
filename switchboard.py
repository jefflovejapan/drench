import os
from collections import namedtuple
import pudb


class switchboard():
    def __init__(self, dirname, filelist):
        self.dirname = dirname
        self.filelist = filelist[:]
        self.outfiles = []
        self.index = 0
        os.mkdir(self.dirname)
        os.chdir(os.getcwd() + '/' + self.dirname)
        outfile = namedtuple('destination', 'path length')

        for i in filelist:
            addpath = '/'.join(i['path'][:-1])
            if addpath:
                if addpath not in os.listdir(os.getcwd()):
                    os.makedirs(addpath)
                thisfile = outfile(path=open('/'.join((addpath, i['path']
                                             [-1])), 'w'), length=i['length'])
            else:
                thisfile = outfile(path=open(i['path'][-1], 'w'),
                                   length=i['length'])
            self.outfiles.append(thisfile)
        print self.outfiles

    def seek(self, index):
        self.index = index

    def write(self, block):
        abs_end = sum([i.length for i in self.outfiles])
        j = 1
        while block:
            while j <= len(self.outfiles):
                file_start = abs_end - sum(k.length for k in
                                           self.outfiles[-j:])
                file_end = file_start + self.outfiles[-j].length
                if self.index >= file_start:
                    bytes_writable = file_end - self.index
                    self.outfiles[-j].path.seek(self.index - file_start)
                    self.outfiles[-j].path.write(block[:bytes_writable])
                    print ('just wrote {} bytes to '
                           '{}').format(len(block[:bytes_writable]),
                                        self.outfiles[-j].path)
                    block = block[bytes_writable:]
                    self.index = self.index + bytes_writable
                    j -= 1
                    break
                else:
                    j += 1
            else:
                raise Exception('some wacky shit happened trying to'
                                'write to files')

    def close(self):
        for i in self.outfiles:
            i.path.close()


def main():
    mylist = [{'path': ['biz.pdf'], 'length': 300},
              {'path': ['baz.txt'], 'length': 100},
              {'path': ['ziz'], 'length': 250}]
    myswitchboard = switchboard('testing', mylist)
    myswitchboard.seek(350)
    myswitchboard.write(chr(0)*80)
    os.chdir('/Users/jeffblagdon/Developer/torrents')
    myswitchboard2 = switchboard('testing2', mylist)
    myswitchboard2.seek(240)
    myswitchboard2.write(chr(0)*180)
    myswitchboard.close()
    myswitchboard2.close()


if __name__ == '__main__':
    main()
