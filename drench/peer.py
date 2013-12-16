from bitarray import bitarray
from piece import Piece
import struct
import random
import hashlib
import pudb
from math import ceil


# Maximum request size according to
# https://wiki.theory.org/BitTorrentSpecification
REQUEST_SIZE = 2 ** 14


class Peer(object):
    # Can't initialize without a dictionary. Handshake
    # takes place using socket before peer init
    def __init__(self, sock, reactor, torrent, in_location):
        print 'inside peer.__init__'
        self.sock = sock
        self.sock.setblocking(True)
        self.reactor = reactor
        self.torrent = torrent

        # What am I trying to do?
        # I only want self.location to include keys and vals
        # if val for key in in_location
        loc_list = ['city', 'region_name', 'country_name']
        self.location = {key: in_location[key] for key in loc_list
                         if key in in_location and in_location[key]}

        self.valid_indices = []
        self.bitfield = None
        self.max_size = 16 * 1024
        self.states = {'reading_length': 0, 'reading_id': 1,
                       'reading_message': 2}
        self.save_state = {'state': self.states['reading_length'],
                           'length': 0, 'message_id': None,
                           'message': '', 'remainder': ''}
        self.message_codes = ['choke', 'unchoke', 'interested',
                              'not interested', 'have', 'bitfield', 'request',
                              'piece', 'cancel', 'port']
        self.ischoking = True
        self.isinterested = False
        self.unchoke()  # Testing to see if this makes a difference
        activate_dict = {'kind': 'activate', 'address': self.getpeername(),
                         'location': self.location}
        self.torrent.switchboard.try_vis_handoff(activate_dict)

    def fileno(self):
        return self.sock.fileno()

    def getpeername(self):
        return self.sock.getpeername()

    def read(self):
        try:
            bytes = self.sock.recv(self.max_size)
        except:
            self.torrent.kill_peer(self)
            return
        '''
        Chain of events:
            - process_input
            - check save_state and read length, id, and message accordingly
                - if we have a piece (really a block), we piece.save it out
                  inside call to ppiece
                    - If we've completed a piece we:
                        - Tell the switchboard to write it out
                        - init a new piece
        '''
        if len(bytes) == 0:
            print 'Got 0 bytes from fileno {}.'.format(self.fileno())
            self.torrent.kill_peer(self)
        self.process_input(bytes)

    def process_input(self, bytes):
        while bytes:
            if self.save_state['state'] == self.states['reading_length']:
                bytes = self.get_message_length(bytes)
            elif self.save_state['state'] == self.states['reading_id']:
                bytes = self.get_message_id(bytes)
            elif self.save_state['state'] == self.states['reading_message']:
                bytes = self.get_message(bytes)

    def get_message_length(self, instr):

            # If we already have a partial message, start with that
            if self.save_state['remainder']:
                instr = self.save_state['remainder'] + instr
                self.save_state['remainder'] = ''

            # If we have four bytes we can at least read the length
            if len(instr) >= 4:

                # Need 0 index because struct.unpack returns tuple
                # save_state['length'] is based on what the peer *says*, not
                # on the length of the actual message
                self.save_state['length'] = struct.unpack('!i', instr[0:4])[0]
                if self.save_state['length'] == 0:
                    self.keep_alive()
                    self.save_state['state'] = self.states['reading_length']
                    return instr[4:]
                else:
                    self.save_state['state'] = self.states['reading_id']
                    return instr[4:]

            # Less than four bytes and we save + wait for next read
            # Increeedibly unlikely to happen
            else:
                self.save_state['remainder'] = instr
                return ''

    def get_message_id(self, instr):
        self.save_state['message_id'] = struct.unpack('b', instr[0])[0]
        self.save_state['state'] = self.states['reading_message']
        return instr[1:]

    def get_message(self, instr):
        # Since one byte is getting used up for the message_id
        length_after_id = self.save_state['length'] - 1
        if length_after_id == 0:
            self.save_state['state'] = self.states['reading_length']
            self.save_state['message_id'] = None
            self.save_state['message'] = ''
            return instr

        if self.save_state['remainder']:
            instr = self.save_state['remainder'] + instr

        # If we have more than what we need we act on the full message and
        # return the rest
        if len(instr) >= length_after_id:

            self.save_state['message'] = instr[:length_after_id]

            # If we hit handle_message we know that we have a FULL MESSAGE
            # All the stateful stuff can go in the garbage
            self.handle_message()
            self.reset_state()
            return instr[length_after_id:]

        # Otherwise we stash what we have and keep things the way they are
        else:
            self.save_state['remainder'] = instr
            return None

    def reset_state(self):
        self.save_state['state'] = self.states['reading_length']
        self.save_state['length'] = 0
        self.save_state['message_id'] = None
        self.save_state['message'] = ''
        self.save_state['remainder'] = ''

    # This is only getting called when I have a complete message
    def handle_message(self):
        if self.save_state['message_id'] == 0:
            self.pchoke()
        elif self.save_state['message_id'] == 1:
            self.punchoke()
        elif self.save_state['message_id'] == 2:
            self.pinterested()
        elif self.save_state['message_id'] == 3:
            self.pnotinterested()
        elif self.save_state['message_id'] == 4:
            self.phave()
        elif self.save_state['message_id'] == 5:
            self.pbitfield()
        elif self.save_state['message_id'] == 6:
            self.prequest()
        elif self.save_state['message_id'] == 7:
            self.ppiece(self.save_state['message'])
        elif self.save_state['message_id'] == 8:
            self.pcancel()
        elif self.save_state['message_id'] == 9:
            pass

    def pchoke(self):
        print 'choke'
        self.ischoking = True

    def punchoke(self):
        print 'unchoke'
        self.ischoking = False

    def pinterested(self):
        print 'pinterested'

    def pnotinterested(self):
        print 'pnotinterested'

    def phave(self):
        print 'phave from', self.fileno()
        index = struct.unpack('>i', self.save_state['message'])[0]
        self.bitfield[index] = True

    def pbitfield(self):
        print 'pbitfield from', self.fileno()
        self.bitfield = bitarray()
        self.bitfield.frombytes(self.save_state['message'])
        self.interested()
        self.unchoke()
        self.piece = self.init_piece()
        self.request_all()

    def prequest(self):
        print 'prequest'

    def ppiece(self, content):
        '''
        Process a piece that we've received from a peer, writing it out to
        one or more files
        '''
        piece_index, byte_begin = struct.unpack('!ii', content[0:8])

        # TODO -- figure out a better way to catch this error.
        # How is piece_index getting swapped out from under me?
        if piece_index != self.piece.index:
            return

        assert byte_begin % REQUEST_SIZE == 0
        block_begin = byte_begin / REQUEST_SIZE
        block = content[8:]
        self.piece.save(index=block_begin, bytes=block)
        if self.piece.complete:
            piece_bytes = self.piece.get_bytes()
            if self.piece.index == self.torrent.last_piece:
                piece_bytes = piece_bytes[:self.torrent.last_piece_length]
            if hashlib.sha1(piece_bytes).digest() == (self.torrent.torrent_dict
                                                      ['info']['pieces']
                                                      [20 * piece_index:20 *
                                                       piece_index + 20]):

                print 'hash matches'

                # Take care of visualizer stuff
                piece_dict = {'kind': 'piece', 'peer': self.sock.getpeername(),
                              'piece_index': piece_index}
                self.torrent.switchboard.try_vis_handoff(piece_dict)

                print ('writing piece {}. Length is '
                       '{}').format(repr(piece_bytes)[:10] + '...',
                                    len(piece_bytes))

                # Write out
                byte_index = piece_index * self.torrent.piece_length
                self.piece = self.init_piece()
                self.request_all()
                self.torrent.switchboard.write(byte_index, piece_bytes)
                self.torrent.switchboard.mark_off(piece_index)
                print self.torrent.switchboard.bitfield
                if self.torrent.switchboard.complete:
                    print '\nDownload complete\n'
                    self.reactor.is_running = False
            else:
                print "Bad data -- hash doesn't match. Discarding piece."
                self.piece = self.init_piece()
                self.request_all()

    def pcancel(self):
        print 'pcancel'

    def read_timeout(self):
        print 'Timeout on read attempt. Re-requesting piece.'
        self.request_all()

    def interested(self):
        packet = ''.join(struct.pack('!ib', 1, 2))
        self.sock.send(packet)

    def unchoke(self):
        packet = struct.pack('!ib', 1, 1)
        self.sock.send(packet)

    def keep_alive(self):
        print 'inside keep_alive'

    def write(self):
        pass

    def get_piece_length(self, index):
        if index == self.torrent.last_piece:
            return self.torrent.last_piece_length
        else:
            return self.torrent.piece_length

    def init_piece(self):
        valid_indices = []
        for i in range(self.torrent.num_pieces):
            assert self.bitfield
            if (self.torrent.switchboard.bitfield[i] is True
                    and self.bitfield[i] is True):
                valid_indices.append(i)
        if not valid_indices:
            return
        else:
            index = random.choice(valid_indices)
        length = self.get_piece_length(index)
        if index is self.torrent.last_piece:
            num_blocks = int(ceil(float(length) / REQUEST_SIZE))
        else:
            num_blocks = int(ceil(float(length) / REQUEST_SIZE))
        return Piece(index=index, num_blocks=num_blocks,
                     request_size=REQUEST_SIZE)

    def request_all(self):
        if not self.piece:
            return
        for i in xrange(self.piece.num_blocks):
            self.request_block(i)
        request_dict = {'kind': 'request',
                        'peer': self.sock.getpeername(),
                        'piece': self.piece.index}
        self.torrent.switchboard.try_vis_handoff(request_dict)
        print 'next request:', request_dict

    def get_last_block_size(self):
        return self.torrent.last_piece_length % REQUEST_SIZE

    def request_block(self, block_index):
        byte_index = block_index * REQUEST_SIZE
        if (self.piece.index == self.torrent.last_piece and
                byte_index == self.piece.last_block):
            request_size = self.get_last_block_size()
        else:
            request_size = REQUEST_SIZE
        packet = ''.join(struct.pack('!ibiii', 13, 6, self.piece.index,
                                     byte_index, request_size))
        bytes = self.sock.send(packet)
        if bytes != len(packet):
            raise Exception('couldnt send request')
