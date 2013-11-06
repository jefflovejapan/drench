import os
import pudb
import bitarray
from collections import namedtuple

outfile = namedtuple('destination', 'fobj length')
start_end_pair = namedtuple('start_end_pair', 'start end')


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


def get_heads_tails(want_file_pos=[], file_starts=[], num_pieces=0,
                    piece_length=0):
    heads_tails = []
    for i in want_file_pos:
        head_tail = get_head_tail(want_index=i, file_starts=file_starts,
                                  num_pieces=num_pieces,
                                  piece_length=piece_length)
        heads_tails.append(head_tail)
    return heads_tails


def get_head_tail(want_index=0, file_starts=[], num_pieces=0,
                  piece_length=0):

    # Find the byte value where the file starts
    byte_start = file_starts[want_index]

    # The firt piece we care about is at the point where the combined length
    # is *just* less than or equal to byte_start
    first_piece = byte_start // piece_length

    # We want it in a separate variable so we can iterate
    piece_pos = first_piece

    # Find if we want the last file in the torrent
    if want_index == len(file_starts) - 1:
        last_piece = num_pieces - 1

    # Otherwise we want a different piece
    elif want_index < len(file_starts) - 1:
        next_file_start = file_starts[want_index + 1]
        while piece_pos * piece_length < next_file_start:
            piece_pos += 1
        last_piece = piece_pos - 1

    # Or we blew it
    else:
        raise Exception('You blew it in get_head_tail')

    return start_end_pair(start=first_piece, end=last_piece)


# def get_interested(files=[], want_file_pos=[], file_starts=[],
#                    piece_length=0, num_pieces=0):
#     print files, want_file_pos, file_starts, piece_length, num_pieces
#     interested_bitfield = bitarray.bitarray()
#     want_index = 0
#     j = 0
#     while j < num_pieces:
#         piece_start = j * piece_length
#         piece_end = piece_start + piece_length
#         if want_index >= len(want_file_pos):

#             # Hack. If our want index goes out of range it means
#             # we're not interested in anything else. But we still need to
#             # finish filling out the bitfield
#             file_start = num_pieces * piece_length + 1  # hack
#             file_end = file_start

#         else:
#             file_start = file_starts[want_file_pos[want_index]]
#             file_end = file_start + files[want_file_pos[want_index]]
#                        ['length']

#         if piece_end < file_start:
#             interested_bitfield.append(0)
#             j += 1
#         elif piece_end > file_start and piece_end <= file_end:
#             interested_bitfield.append(1)
#             j += 1
#         elif piece_start >= file_start and piece_start < file_end:
#             interested_bitfield.append(1)
#             j += 1
#         elif piece_start >= file_end:
#             want_index += 1
#         else:
#             raise Exception('You fucked up')
#     print interested_bitfield
#     return interested_bitfield


class switchboard():
    def __init__(self, dirname='', file_list=[], piece_length=0, num_pieces=0):
        self.dirname = dirname
        self.file_list = file_list[:]
        self.piece_length = piece_length
        self.num_pieces = num_pieces
        self.file_starts = get_file_starts(self.file_list)
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
        self.heads_and_tails = get_heads_tails

    def seek(self, index):
        self.index = index

    def write(self, block):
        while block:
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


def main():
    pudb.set_trace()
    files = [{'length': 3}, {'length': 3}, {'length': 3}, {'length': 3},
             {'length': 3}]
    want_file_pos = [1, 3]
    piece_length = 4
    file_length = 3
    file_starts = [i * file_length for i in range(len(files))]
    num_pieces = 4
    print 'case 1'
    print get_heads_tails(want_file_pos=want_file_pos, file_starts=file_starts,
                          num_pieces=num_pieces, piece_length=piece_length)

    files = [{'length': 4}, {'length': 4}, {'length': 4}, {'length': 4},
             {'length': 4}]
    want_file_pos = [1]
    piece_length = 3
    file_length = 4
    file_starts = [i * file_length for i in range(len(files))]
    num_pieces = 4
    print 'case 2'
    print get_heads_tails(want_file_pos=want_file_pos, file_starts=file_starts,
                          num_pieces=num_pieces, piece_length=piece_length)


if __name__ == '__main__':
    main()
