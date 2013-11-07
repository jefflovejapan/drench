import os
import pudb
import bitarray
import copy
from collections import namedtuple

start_end_pair = namedtuple('start_end_pair', 'start end')


def build_dirs(files):
    '''
    Build necessary directories based on a list of file paths
    '''

    for i in files:
        if len(i['path']) > 1:
            addpath = os.path.join(*i['path'][:-1])
            if addpath and addpath not in os.listdir(os.getcwd()):
                os.makedirs(addpath)
                print 'just made path', addpath


def get_want_file_pos(file_list):
    '''
    Ask the user which files in file_list he or she is interested in.
    Return indices for the files inside file_list
    '''
    want_file_pos = []
    print '\nFiles contained:\n'
    for i in file_list:
        print(os.path.join(*i['path']))
    while 1:
        all_answer = raw_input('\nDo you want all these files? (y/n): ')
        if all_answer in ('y', 'n'):
            break
    if all_answer == 'y':
        # TODO -- Can have something simpler here when user wants everything
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
    '''
    Return the starting position (in bytes) of a list of files by
    iteratively summing their lengths
    '''
    starts = []
    total = 0
    for i in file_list:
        starts.append(total)
        total += i['length']
    print starts
    return starts


def get_write_file(byte_index=0, file_starts=[0], files=[], outfiles=[]):
    '''
    Retrieve the actual file that the current block of data should be
    written to.
    '''
    i = 1
    while i <= len(file_starts) + 1:
        start = file_starts[-i]
        if start <= byte_index:
            tfile = files[-i]
            break
        else:
            i += 1
    j = 1
    while j <= len(outfiles) + 1:
        if outfiles[-j].name == os.path.join(*tfile['path']):
            return outfiles[-j]
        else:
            j += 1
    else:
        raise Exception("Shit isn't matching")


def get_file_start(byte_index=0, file_starts=[]):
    '''
    Find the starting position of the earliest file that I want to write to
    '''
    # Seems like I should be counting forward through these. Find the first
    # file whose starting position is <= index?
    i = 1
    while i <= len(file_starts) + 1:
        if byte_index >= file_starts[-i]:
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

        # We want the piece *before* the first one after the next file starts
        last_piece = piece_pos - 1

    return start_end_pair(start=first_piece, end=last_piece)


def build_bitfield(heads_and_tails=[], num_pieces=0):
    this_bitfield = bitarray.bitarray('0' * num_pieces)
    for i in heads_and_tails:
        for j in range(i.start, i.end + 1):
            this_bitfield[j] = True
    return this_bitfield


class switchboard(object):
    def __init__(self, dirname='', file_list=[], piece_length=0, num_pieces=0):
        self.dirname = dirname
        self.file_list = copy.deepcopy(file_list)
        self.piece_length = piece_length
        self.num_pieces = num_pieces
        self.file_starts = get_file_starts(self.file_list)
        self.want_file_pos = get_want_file_pos(self.file_list)
        self.outfiles = []
        self.byte_index = 0
        os.mkdir(self.dirname)
        os.chdir(os.path.join(os.getcwd(), self.dirname))
        want_files = [self.file_list[index] for index in self.want_file_pos]
        build_dirs(want_files)
        for i in self.want_file_pos:
            thisfile = open(os.path.join(*self.file_list[i]
                                         ['path']), 'w')
            self.outfiles.append(thisfile)
        heads_and_tails = get_heads_tails(want_file_pos=self.want_file_pos,
                                          file_starts=self.file_starts,
                                          num_pieces=self.num_pieces,
                                          piece_length=self.piece_length)
        self.bitfield = build_bitfield(heads_and_tails,
                                       num_pieces=self.num_pieces)

    def seek(self, index):
        '''
        Set how far to advance (bytewise) in file list
        '''
        self.byte_index = index

    def write(self, block):
        while block:

            # file_start is the byte offset of the rightmost file whose
            # offset is less than index. It's the offset of the file that
            # the block starting at index should begin writing to.
            file_start = get_file_start(byte_index=self.byte_index,
                                        file_starts=self.file_starts)

            # write_file is the actual file that we ought to be writing to.
            # It's... I dunno
            write_file = get_write_file(byte_index=self.byte_index,
                                        files=self.file_list,
                                        file_starts=self.file_starts,
                                        outfiles=self.outfiles)

            file_index = self.byte_index - file_start
            write_file.seek(file_index)
            file_end = (self.file_starts
                        [self.file_starts.index(file_start) + 1])

            bytes_writable = file_end - file_index
            if bytes_writable < len(block):
                write_file.write(block[:bytes_writable])

                # This will take us to the next index value in file_starts
                next_index = self.outfiles.index(write_file) + 1
                next_start = self.file_starts[next_index]
                self.byte_index = next_start
                # Moving ahead by the difference
                if block[next_start-file_end]:
                    block = block[next_start-file_end:]
                else:
                    block = None
            else:
                write_file.write(block)
                block = None

    def mark_off(self, index):
        self.bitfield[index] = False

    @property
    def complete(self):
        if any(self.bitfield):
            return True
        else:
            return False

    def close(self):
        for i in self.outfiles:
            i.close()


# def test_heads_tails():
#     files = [{'length': 3}, {'length': 3}, {'length': 3}, {'length': 3},
#              {'length': 3}]
#     want_file_pos = [1, 3]
#     piece_length = 4
#     file_length = 3
#     file_starts = [i * file_length for i in range(len(files))]
#     num_pieces = 4
#     print 'case 1'
#     heads_tails = get_heads_tails(want_file_pos=want_file_pos,
#                                   file_starts=file_starts,
#                                   num_pieces=num_pieces,
#                                   piece_length=piece_length)
#     assert build_bitfield(heads_tails, num_pieces) == bitarray.bitarray('1110')

#     files = [{'length': 4}, {'length': 4}, {'length': 4}, {'length': 4},
#              {'length': 4}]
#     want_file_pos = [1]
#     piece_length = 3
#     file_length = 4
#     file_starts = [i * file_length for i in range(len(files))]
#     num_pieces = 4
#     heads_tails = get_heads_tails(want_file_pos=want_file_pos,
#                                   file_starts=file_starts,
#                                   num_pieces=num_pieces,
#                                   piece_length=piece_length)
#     assert build_bitfield(heads_tails, num_pieces) == bitarray.bitarray('0110')


# if __name__ == '__main__':
#     test_heads_tails()
