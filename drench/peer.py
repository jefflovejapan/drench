from bitarray import bitarray
import struct
import random
import hashlib
import pudb

# Number of simultaneous requests made to "prime the pump" after handshake
SIM_REQUESTS = 20


class Peer(object):
    # Can't initialize without a dictionary. Handshake
    # takes place using socket before peer init
    def __init__(self, sock, reactor, torrent):
        self.sock = sock
        self.sock.setblocking(True)
        self.reactor = reactor
        self.torrent = torrent
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

    def fileno(self):
        return self.sock.fileno()

    def getpeername(self):
        return self.sock.getpeername()

    def read(self):
        bytes = self.sock.recv(self.max_size)
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
                print 'We have a remainder at the top of get_message_length'
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
        index = struct.unpack('>i', self.save_state['message'])[0]
        self.bitfield[index] = True

    def pbitfield(self):
        self.bitfield = bitarray()
        self.bitfield.frombytes(self.save_state['message'])
        self.interested()
        self.unchoke()
        self.mad_requests()

    def prequest(self):
        print 'prequest'

    def ppiece(self, content):
        '''
        Process a piece that we've received from a peer, writing it out to
        one or more files
        '''
        piece_index, block_begin = struct.unpack('!ii', content[0:8])
        piece_dict = {'kind': 'piece', 'peer': self.sock.getpeername(),
                      'piece_index': piece_index}
        self.torrent.switchboard.try_vis_handoff(piece_dict)
        block = content[8:]
        if hashlib.sha1(block).digest() == (self.torrent.torrent_dict['info']
                                            ['pieces']
                                            [20 * piece_index:20 * piece_index
                                             + 20]):
            print 'hash matches'
            print ('writing piece {}. Length is '
                   '{}').format(repr(block)[:10] + '...', len(block))
            byte_index = piece_index * self.torrent.piece_length
            self.torrent.switchboard.write(byte_index, block)
            self.torrent.switchboard.mark_off(piece_index)
            print self.torrent.switchboard.bitfield
            if self.torrent.switchboard.complete:
                print '\nDownload complete\n'
                self.reactor.is_running = False
        else:
            raise Exception("hash of piece doesn't"
                            "match hash in torrent_dict")
        self.request_piece()

    def pcancel(self):
        print 'pcancel'

    def read_timeout(self):
        self.mad_requests()

    def mad_requests(self):
        for i in xrange(SIM_REQUESTS):
            self.request_piece()
            print ('Just made {}th consecutive request'
                   'to {}'.format(i, self.fileno()))

    def request_piece(self):
        if not self.valid_indices:
            # We want a list of all indices where:
            #   - We're interested in the piece
            #     (i.e., it's in torrent.outfile.bitfield)
            #   - The peer has the piece (it's available)
            for i in range(self.torrent.num_pieces):
                if (self.torrent.switchboard.bitfield[i] is True
                        and self.bitfield[i] is True):
                    self.valid_indices.append(i)
            if not self.valid_indices:
                return
            else:
                random.shuffle(self.valid_indices)
        self.request(self.valid_indices.pop())

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

    def request(self, want_piece):
        if want_piece == self.torrent.num_pieces - 1:
            piece_length = self.torrent.last_piece_length
        else:
            piece_length = self.torrent.piece_length
        packet = ''.join(struct.pack('!ibiii', 13, 6, want_piece, 0,
                         piece_length))
        bytes = self.sock.send(packet)
        request_dict = {'kind': 'request',
                        'peer': self.sock.getpeername(),
                        'piece': want_piece}
        self.torrent.switchboard.try_vis_handoff(request_dict)
        print 'next request:', request_dict
        if bytes != len(packet):
            raise Exception('couldnt send request')
