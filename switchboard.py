import os
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
        self.block = ''
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

        # Retrieve the file object whose name is write_path
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
        bytes_writable = file_length - file_internal_index
        if bytes_writable < len(self.block):
            write_obj.write(self.block[:bytes_writable])
            self.block = self.block[bytes_writable:]
            self.byte_index = self.byte_index + bytes_writable

            # The next index in the entire torrent
            j = self.file_starts.index(file_start) + 1

            # If we still want a higher index
            if j <= self.want_file_pos[-1]:
                self.write()

            else:
                return

        else:
            write_obj.write(self.block)
            self.block = ''

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

#     piece_length = 131072
#     want_files = [24,25]
#     last_piece = 69171

#     myswitchboard = switchboard(dirname='derp', file_list=files,
#                                 piece_length=piece_length,
#                                 num_pieces=2087)
#     myswitchboard.file_starts = file_starts
#     myswitchboard.seek(273416192)
#     myswitchboard.set_block('0'*last_piece)
#     myswitchboard.file_starts = file_starts
#     myswitchboard.write()

# if __name__ == '__main__':
#     test_get_write_file()
