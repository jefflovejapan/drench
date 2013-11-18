import os
import bitarray
import copy
import json
import pudb
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


def get_rightmost_file(byte_index=0, file_starts=[0], files=[]):

    '''
    Retrieve the highest-indexed file that starts at or before byte_index.
    '''
    i = 1
    while i <= len(file_starts):
        start = file_starts[-i]
        if start <= byte_index:
            return files[-i]
        else:
            i += 1
    else:
        raise Exception('byte_index lower than all file_starts')


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


class Switchboard(object):
    def __init__(self, dirname='', file_list=[], piece_length=0, num_pieces=0,
                 visualizer=None):
        self.dirname = dirname
        self.file_list = copy.deepcopy(file_list)
        self.piece_length = piece_length
        self.num_pieces = num_pieces
        self.file_starts = get_file_starts(self.file_list)
        self.want_file_pos = get_want_file_pos(self.file_list)
        self.outfiles = []
        self.byte_index = 0
        self.block = ''
        # TODO -- possibly a problem when a visualizer signs on halfway
        self.visualizer = visualizer
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
        pass

    def get_next_want_file(self):
        '''
        Returns the leftmost file in the user's list of wanted files
        (want_file_pos). If the first file it finds isn't in the list,
        it will keep searching until the length of 'block' is exceeded.
        '''
        while self.block:
            rightmost = get_rightmost_file(byte_index=self.byte_index,
                                           file_starts=self.file_starts,
                                           files=self.file_list)
            if self.file_list.index(rightmost) in self.want_file_pos:
                return rightmost
            else:
                    file_start = (self.file_starts
                                  [self.file_list.index(rightmost)])
                    file_length = rightmost['length']
                    bytes_rem = file_start + file_length - self.byte_index
                    if len(self.block) > bytes_rem:
                        self.block = self.block[bytes_rem:]
                        self.byte_index = self.byte_index + bytes_rem
                    else:
                        self.block = ''
        else:
            return None

    def seek(self, index):
        '''
        Set how far to advance (bytewise) in file_list
        '''
        self.byte_index = index

    def set_block(self, block):
        self.block = block

    def write(self):
        write_file = self.get_next_want_file()

        if not write_file:
            return

        # Retrieve the file object whose name is described by write_file
        i = 0
        while i < len(self.outfiles):
            if self.outfiles[i].name == os.path.join(*write_file['path']):
                write_obj = self.outfiles[i]
                break
            else:
                i += 1
        else:
            raise Exception('Nothing matches')

        file_start = self.file_starts[self.file_list.index(write_file)]
        file_internal_index = self.byte_index - file_start
        write_obj.seek(file_internal_index)

        file_length = write_file['length']

        # How far till the end?
        bytes_writable = file_length - file_internal_index

        # If we can't write the entire block
        if bytes_writable < len(self.block):
            write_dict = {'kind': 'write', 'position': file_internal_index,
                          'length': bytes_writable}
            write_json = json.dumps(write_dict)
            self.visualize(write_json)
            write_obj.write(self.block[:bytes_writable])
            self.block = self.block[bytes_writable:]
            self.byte_index = self.byte_index + bytes_writable

            # Find the would-be next highest index (we could be on last file)
            j = self.file_starts.index(file_start) + 1

            # If we're not at the end, keep trying to write
            if j <= self.want_file_pos[-1]:
                self.write()

            else:
                return

        # If we can write the entire block
        else:
            write_dict = {'kind': 'write', 'position': file_internal_index,
                          'length': len(self.block)}
            write_json = json.dumps(write_dict)
            self.visualize(write_json)
            write_obj.write(self.block)
            self.block = ''

    def mark_off(self, index):
        self.bitfield[index] = False

    def visualize(self, data):
        if self.visualizer:
            self.visualizer.write(data)

    @property
    def complete(self):
        if any(self.bitfield):
            return False
        else:
            return True

    def close(self):
        for i in self.outfiles:
            i.close()
