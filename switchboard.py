import os
import pudb
import bitarray
from collections import namedtuple

outfile = namedtuple('destination', 'fobj length')


def build_dirs(files):
    for i in files:
        if len(i['path']) > 1:
            addpath = os.path.join(*i['path'][:-1])
            if addpath and addpath not in os.listdir(os.getcwd()):
                os.makedirs(addpath)
                print 'just made path', addpath


def get_want_file_pos(file_list):
    want_file_pos = []
    print '\nFiles contained:\n'
    for i in file_list:
        print(os.path.join(*i['path']))
    while 1:
        all_answer = raw_input('\nDo you want all these files? (y/n): ')
        if all_answer in ('y', 'n'):
            break
    if all_answer == 'y':
        want_file_pos = range(len(file_list))
        return want_file_pos
    if all_answer == 'n':
        for j, tfile in enumerate(file_list):
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
            print os.path.join(*file_list[k]['path'])
        return want_file_pos


def get_file_starts(file_list):
    starts = []
    total = 0
    for i in file_list:
        starts.append(total)
        total += i['length']
    print starts
    return starts


def get_write_file(index=0, file_starts=[0], files=[], outfiles=[]):
    i = 1
    while i <= len(file_starts) + 1:
        start = file_starts[-i]
        if start <= index:
            tfile = files[-i]
            break
        else:
            i += 1
    j = 1
    while j <= len(outfiles) + 1:
        pudb.set_trace()
        if outfiles[-j].fobj.name == os.path.join(*tfile['path']):
            return outfiles[-j]
        else:
            j += 1
    else:
        raise Exception("Shit isn't matching")


def get_file_start(index=0, file_starts=[]):
    i = 1
    while i <= len(file_starts) + 1:
        if index >= file_starts[-i]:
            return file_starts[-i]
        else:
            i += 1


def get_interested(files=[], want_file_pos=[]):
    piece_indices = bitarray.bitarray()
    next_index = 0
    file_index = 0
    j = 0
    while j < len(files):
        if file_index in want_file_pos:
            piece_indices.extend(b'1'*files[file_index]['length'])
            next_index += files[file_index]['length']
            file_index += 1
        else:
            piece_indices.extend(b'0'*files[file_index]['length'])
            next_index += files[file_index]['length']
            file_index += 1
        j += 1
    return piece_indices


class switchboard():
    def __init__(self, dirname, file_list):
        self.dirname = dirname
        self.file_list = file_list[:]
        self.file_starts = get_file_starts(file_list)
        self.want_file_pos = get_want_file_pos(self.file_list)
        self.outfiles = []
        self.index = 0
        os.mkdir(self.dirname)
        print 'making directory', self.dirname
        os.chdir(os.path.join(os.getcwd(), self.dirname))
        build_dirs(self.file_list[index] for index in self.want_file_pos)
        for i in self.want_file_pos:
            thisfile = outfile(fobj=open(os.path.join(*self.file_list[i]
                                         ['path']), 'w'),
                               length=self.file_list[i]['length'])
            self.outfiles.append(thisfile)
        self.interested_indices = get_interested(files=self.file_list,
                                                 want_file_pos=
                                                 self.want_file_pos)
        # file_list still OK after init. Who touches switchboard next?

    def seek(self, index):
        self.index = index

    def write(self, block):
        while block:
            pudb.set_trace()
            file_start = get_file_start(index=self.index,
                                        file_starts=self.file_starts)
            write_file = get_write_file(index=self.index,
                                        files=self.file_list,
                                        file_starts=self.file_starts,
                                        outfiles=self.outfiles)
            file_index = self.index - file_start
            write_file.seek(file_index)
            file_end = (self.file_starts
                        [self.file_starts.index(file_start) + 1] - 1)

            bytes_writable = file_end - file_index
            if bytes_writable < len(block):
                write_file.write(block[:bytes_writable])

                # This will take us to the next index value in file_starts
                next_index = self.outfiles.index(write_file) + 1
                next_start = self.file_starts[next_index]
                self.index = next_start
                # Moving ahead by the difference
                if block[next_start-file_end]:
                    block = block[next_start-file_end:]
                else:
                    block = None

    def close(self):
        for i in self.outfiles:
            i.fobj.close()
