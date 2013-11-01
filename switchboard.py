import os
from collections import namedtuple
import pudb


class switchboard():
    def __init__(self, dirname, filelist):
        self.dirname = dirname
        self.filelist = filelist[:]
        os.mkdir(self.dirname)
        os.chdir(os.getcwd() + '/' + self.dirname)
        outfile = namedtuple('destination', 'path length')
        # Need the 0 index here because ['path'] is a 1-element list
        self.outfiles = [outfile(open(i['path'][0], 'w'), i['length']) for i in
                         self.filelist]
        print self.outfiles
        self.index = 0

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
                    if file_end <= self.index + len(block):
                        self.outfiles[-j].path.close()
                    block = block[bytes_writable:]
                    self.index = self.index + bytes_writable
                    j -= 1
                    break
                else:
                    j += 1
            else:
                raise Exception('some wacky shit happened trying to'
                                'write to files')


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


if __name__ == '__main__':
    main()
