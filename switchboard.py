import os
import pudb
from collections import namedtuple

outfile = namedtuple('destination', 'path length')


def build_dirs(files):
    for i in files:
        if len(i['path']) > 1:
            addpath = os.path.join(*i['path'][:-1])
            if addpath and addpath not in os.listdir(os.getcwd()):
                os.makedirs(addpath)
                print 'just made path', addpath


def get_want_file_pos(filelist):
    want_file_pos = []
    print '\nFiles contained:\n'
    for i in filelist:
        print(os.path.join(*i['path']))
    while 1:
        all_answer = raw_input('\nDo you want all these files? (y/n): ')
        if all_answer in ('y', 'n'):
            break
    if all_answer == 'y':
        want_file_pos = range(len(filelist))
        return want_file_pos
    if all_answer == 'n':
        for j, tfile in enumerate(filelist):
            while 1:
                file_answer = raw_input('Do you want {}? '
                                        '(y/n): '.format(os.path.join
                                                        (*tfile['path'])))

                if file_answer in ('y', 'n'):
                    break
            if file_answer == 'y':
                want_file_pos.append(j)
        print "Here are all the files you want:"
        for k in want_file_pos:
            print os.path.join(*filelist[k]['path'])
        return want_file_pos


def get_file_starts(filelist):
    starts = []
    total = 0
    for i in filelist:
        total += i['length']
        starts.append(total)
    return starts


class switchboard():
    def __init__(self, dirname, filelist):
        self.dirname = dirname
        self.filelist = filelist[:]
        self.filestarts = get_file_starts(filelist)
        self.want_file_pos = get_want_file_pos(self.filelist)

        # want_files is the list of files that i'm interested in. For any
        # index i, i can:
        #   - find out which file it belongs to using self.filestarts
        #   - find out if I'm interested in the file by:
        #       - getting the file from filelist
        #       - seeing if i'm interested by checking against wantfiles
        #
        # Alternatively, I could:
        #   - find out which file (really index) it belongs to using
        #     self.filestarts
        #   - find out if i'm interested by:
        #       - seeing if that index is in wantfiles

        self.outfiles = []
        self.index = 0
        os.mkdir(self.dirname)
        print 'making directory', self.dirname
        os.chdir(os.path.join(os.getcwd(), self.dirname))
        build_dirs(self.filelist[index] for index in self.want_file_pos)
        for i in self.want_file_pos:
            thisfile = outfile(path=open(os.path.join(*self.filelist[i]
                                         ['path']), 'w'),
                               length=self.filelist[i]['length'])
            self.outfiles.append(thisfile)

    def seek(self, index):
        self.index = index

# Write is taking a block
# We've already seeked to the relevant spot
# If we've got data left over after we write our block and we're NOT
# interested in the adjacent file, we can just throw it away.

# Right now I have:
#   self.index -- the current writing position
#   self.outfiles -- the list of file objects that I'm writing to
# What I need:
#   a list to keep track of only the files that I'm interested in.
#
# If self.index is not in interested_file_starts:
#   if len(block) > len(uninterested file)
#   block = block[len(uninterested file)]
#   self.index += len(uninterested file)
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
