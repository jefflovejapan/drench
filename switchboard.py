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


def get_next_want_file(byte_index=0, want_file_pos=[],
                       file_starts=[0], files=[], block=''):
    while block:
        rightmost = get_rightmost_file(byte_index=byte_index,
                                       file_starts=file_starts,
                                       files=files)
        if files.index(rightmost) in want_file_pos:
            return os.path.join(*rightmost['path'])
        else:
            byte_index = byte_index + rightmost['length']
            if len(block) > rightmost['length']:
                block = block[rightmost['length']:]
            else:
                block = ''
    else:
        return None


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
        # file_start is the byte offset of the rightmost file whose
        # offset is less than index. It's the offset of the file that
        # the block starting at byte_index should begin writing to.
        file_start = get_file_start(byte_index=self.byte_index,
                                    file_starts=self.file_starts)

        # write_path is the file path that we ought to be writing to.
        write_path = get_next_want_file(byte_index=self.byte_index,
                                        files=self.file_list,
                                        file_starts=self.file_starts,
                                        block=block,
                                        want_file_pos=self.want_file_pos)

        if not write_path:
            return

        i = 0
        while i < len(self.outfiles):
            if self.outfiles[i].name == write_path:
                write_file = self.outfiles[i]
                break
            else:
                i += 1
        else:
            pudb.set_trace()
            raise Exception('Nothing matches')

        file_internal_index = self.byte_index - file_start
        write_file.seek(file_internal_index)
        file_end = (self.file_starts
                    [self.file_starts.index(file_start) + 1])

        bytes_writable = file_end - file_internal_index
        if bytes_writable < len(block):
            write_file.write(block[:bytes_writable])
            block = block[bytes_writable:]

            # The next index in the entire torrent
            j = self.file_starts.index(file_start) + 1

            # If we still want a higher index
            if j < self.want_file_pos[-1]:

                # Index of current file among all files in torrent
                current_file_index = self.file_starts.index(file_start)

                # Index of that index inside want_file_pos
                inner_want_index = self.want_file_pos.index(current_file_index)

                # The index of the next file we want among all files in torent
                next_file_index = self.want_file_pos[inner_want_index + 1]

                # The starting byte value of that file
                self.byte_index = self.file_starts[next_file_index]

                # If there's enough block to make it there
                if len(block) > self.byte_index - file_start:
                    block = block[self.byte_index - file_start]

                    # Start writing again
                    self.write(block)

            else:
                return

        else:
            write_file.write(block)
            block = None

    def mark_off(self, index):
        self.bitfield[index] = False

    @property
    def complete(self):
        if any(self.bitfield):
            return False
        else:
            return True

    def close(self):
        for i in self.outfiles:
            i.close()


# def test_get_write_file():
#     file_starts = [0, 483023, 944949, 4157426, 18877975, 36667180, 51499115,
#                    70003240, 84992746, 93577236, 109611431, 127573045,
#                    139208428, 151130741, 166870702, 180550961, 188662949,
#                    197822552, 214302710, 225269360, 236530253, 242925892,
#                    254454279, 265898029, 273484016, 273485312]

#     files = [{'path': ['Content', '174-h.htm'], 'length': 483023},
#              {'path': ['Content', '174.txt'], 'length': 461926},
#              {'path': ['Content', 'pictureofdoriangray_00_wilde_64kb.mp3'], 'length': 3212477},
#              {'path': ['Content', 'pictureofdoriangray_01_wilde_64kb.mp3'], 'length': 14720549},
#              {'path': ['Content', 'pictureofdoriangray_02_wilde_64kb.mp3'], 'length': 17789205},
#              {'path': ['Content', 'pictureofdoriangray_03_wilde_64kb.mp3'], 'length': 14831935},
#              {'path': ['Content', 'pictureofdoriangray_04_wilde_64kb.mp3'], 'length': 18504125},
#              {'path': ['Content', 'pictureofdoriangray_05_wilde_64kb.mp3'], 'length': 14989506},
#              {'path': ['Content', 'pictureofdoriangray_06_wilde_64kb.mp3'], 'length': 8584490},
#              {'path': ['Content', 'pictureofdoriangray_07_wilde_64kb.mp3'], 'length': 16034195},
#              {'path': ['Content', 'pictureofdoriangray_08_wilde_64kb.mp3'], 'length': 17961614}, 
#              {'path': ['Content', 'pictureofdoriangray_09_wilde_64kb.mp3'], 'length': 11635383}, 
#              {'path': ['Content', 'pictureofdoriangray_10_wilde_64kb.mp3'], 'length': 11922313}, 
#              {'path': ['Content', 'pictureofdoriangray_11a_wilde_64kb.mp3'], 'length': 15739961}, 
#              {'path': ['Content', 'pictureofdoriangray_11b_wilde_64kb.mp3'], 'length': 13680259}, 
#              {'path': ['Content', 'pictureofdoriangray_12_wilde_64kb.mp3'], 'length': 8111988}, 
#              {'path': ['Content', 'pictureofdoriangray_13_wilde_64kb.mp3'], 'length': 9159603}, 
#              {'path': ['Content', 'pictureofdoriangray_14_wilde_64kb.mp3'], 'length': 16480158}, 
#              {'path': ['Content', 'pictureofdoriangray_15_wilde_64kb.mp3'], 'length': 10966650}, 
#              {'path': ['Content', 'pictureofdoriangray_16_wilde_64kb.mp3'], 'length': 11260893}, 
#              {'path': ['Content', 'pictureofdoriangray_17_wilde_64kb.mp3'], 'length': 6395639}, 
#              {'path': ['Content', 'pictureofdoriangray_18_wilde_64kb.mp3'], 'length': 11528387}, 
#              {'path': ['Content', 'pictureofdoriangray_19_wilde_64kb.mp3'], 'length': 11443750}, 
#              {'path': ['Content', 'pictureofdoriangray_20_wilde_64kb.mp3'], 'length': 7585987}, 
#              {'path': ['Description.txt'], 'length': 1296}, 
#              {'path': ['License.txt'], 'length': 51}]

#     pudb.set_trace()
#     piece_length = 131072
#     want_files = [0,2]

#     for j in range(32):
#         # Want to find the rightmost file that begins at or before byte_index
#         write_file = get_next_want_file(byte_index=j*piece_length,
#                                         file_starts=file_starts,
#                                         files=files,
#                                         want_file_pos=want_files,
#                                         block='0'*piece_length)

#         print('piece {} starts at byte {} '
#               'and maps to {}'.format(j, j * piece_length, write_file))


# All the pieces for the first three files:
#
# piece 0 starts at byte 0 and maps to somefile(name='Content/174-h.htm')
# piece 1 starts at byte 131072 and maps to somefile(name='Content/174-h.htm')
# piece 2 starts at byte 262144 and maps to somefile(name='Content/174-h.htm')
# piece 3 starts at byte 393216 and maps to somefile(name='Content/174-h.htm')
# piece 4 starts at byte 524288 and maps to somefile(name='Content/174.txt')
# piece 5 starts at byte 655360 and maps to somefile(name='Content/174.txt')
# piece 6 starts at byte 786432 and maps to somefile(name='Content/174.txt')
# piece 7 starts at byte 917504 and maps to somefile(name='Content/174.txt')
# piece 8 starts at byte 1048576 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 9 starts at byte 1179648 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 10 starts at byte 1310720 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 11 starts at byte 1441792 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 12 starts at byte 1572864 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 13 starts at byte 1703936 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 14 starts at byte 1835008 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 15 starts at byte 1966080 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 16 starts at byte 2097152 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 17 starts at byte 2228224 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 18 starts at byte 2359296 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 19 starts at byte 2490368 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 20 starts at byte 2621440 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 21 starts at byte 2752512 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 22 starts at byte 2883584 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 23 starts at byte 3014656 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 24 starts at byte 3145728 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 25 starts at byte 3276800 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 26 starts at byte 3407872 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 27 starts at byte 3538944 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 28 starts at byte 3670016 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 29 starts at byte 3801088 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 30 starts at byte 3932160 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')
# piece 31 starts at byte 4063232 and maps to somefile(name='Content/pictureofdoriangray_00_wilde_64kb.mp3')


# if __name__ == '__main__':
#     test_get_write_file()
