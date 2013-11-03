from bitarray import bitarray
import struct
import pudb
import random
import socket
import hashlib
import time
import os


class peer():
    # Can't initialize without a dictionary. Handshake
    # takes place using socket before peer init
    def __init__(self, sock, reactor, torrent, data):
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
        self.next_request = None
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
        # try:
        bytes = self.sock.recv(self.max_size)
        print 'Just received', len(bytes), 'bytes'
        if len(bytes) == 0:
            print 'Got 0 bytes from fileno {}.'.format(self.fileno())
            self.torrent.kill_peer(self)
        self.process_input(bytes)

    def process_input(self, bytes):
        while bytes:
            if self.save_state['state'] == self.states['reading_length']:
                bytes = self.get_message_length(bytes)
            if self.save_state['state'] == self.states['reading_id']:
                bytes = self.get_message_id(bytes)
            if self.save_state['state'] == self.states['reading_message']:
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
                print ("Client says message is {} bytes "
                       "long").format(self.save_state['length'])
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
        print ('message_id is',
               self.message_codes[self.save_state['message_id']])
        self.save_state['state'] = self.states['reading_message']
        return instr[1:]

    # TODO - THE PROBLEM IS THAT THE SIZE KEEPS DOUBLING WHEN IT SHOULDN'T BE
    def get_message(self, instr):

        # Since one byte is getting used up for the message_id
        length_after_id = self.save_state['length'] - 1
        if length_after_id == 0:
            self.save_state['state'] = self.states['reading_length']
            self.save_state['message_id'] = None
            self.save_state['message'] = ''
            return instr

        if self.save_state['remainder']:
            print ("Inside get_message. The previous remainder was",
                   len(self.save_state['remainder']))
            print "The new contribution is", len(instr)
            instr = self.save_state['remainder'] + instr
            print 'total length of instr is', len(instr)

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
            print 'saving off', len(instr), 'bytes in remainder'
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
        # pudb.set_trace()
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
        print repr(self.bitfield)

    def pbitfield(self):
        self.bitfield = bitarray()
        self.bitfield.frombytes(self.save_state['message'])
        print "this is the peer's bitfield", self.bitfield
        self.interested()
        self.unchoke()
        self.reactor.subscribed['logic'].append(self.logic)
        # pudb.set_trace()

    def prequest(self):
        print 'prequest'

    def ppiece(self, content):
        index, begin = struct.unpack('!ii', content[0:8])
        block = content[8:]
        if hashlib.sha1(block).digest() == (self.torrent.torrent_dict['info']
                                            ['pieces'][20*index:20*index+20]):
            print 'hash matches'
            print ('writing piece {}. Length is '
                   '{}').format(repr(block)[:10] + '...', len(block))
            self.torrent.outfile.seek(index*self.torrent.piece_length)
            self.torrent.outfile.write(block)
        else:
            raise Exception("hash of piece doesn't"
                            "match hash in torrent_dict")

        # TODO -- add check for hash equality
        self.torrent.bitfield[index] = True
        # print 'My bitfield:', self.torrent.bitfield
        self.reactor.subscribed['logic'].append(self.logic)

    def pcancel(self):
        print 'pcancel'

    def logic(self):
        '''
        Figures out what needs to be done next
        '''
        print 'inside logic'
        # TODO -- Why do I need this check? Why would a responsive socket
        # not send me a bitfield?
        # pudb.set_trace()
        if self.bitfield:
            self.valid_indices = []

            for i in range(len(self.torrent.bitfield)):
                if (self.torrent.bitfield[i] is False
                        and self.bitfield[i] is True):

                    self.valid_indices.append(i)
            print len(self.valid_indices), 'more pieces to go'
            if not self.valid_indices:
                self.torrent.outfile.close()
                os.system(' '.join(('open', self.torrent.outfile.name)))
                return
            while 1:
                next_request = random.choice(self.valid_indices)
                if next_request not in self.torrent.queued_requests:
                    print 'Setting next_request = {}'.format(next_request)
                    self.torrent.queued_requests.append(next_request)
                    self.next_request = next_request
                    print ('Self.next_request is', self.next_request, 'from',
                           self.fileno())
                    self.reactor.subscribed['write'].append(self.request)
                    break

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

    def request(self):
        # pudb.set_trace()
        print 'inside request'
        # TODO -- global lookup for id/int conversion
        print ('self.next request:', self.next_request, '\n',
               'piece size:', self.torrent.piece_length, 'from', self.fileno())
        if self.next_request == self.torrent.num_pieces - 1:
            piece_length = self.torrent.last_piece_length
        else:
            piece_length = self.torrent.piece_length
        packet = ''.join(struct.pack('!ibiii', 13, 6, self.next_request, 0,
                         piece_length))
        bytes = self.sock.send(packet)
        if bytes != len(packet):
            raise Exception('couldnt send request')

    def cleanup(self):
        # print 'cleaning up'
        self.torrent.queued_requests = []
