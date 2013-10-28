from bitarray import bitarray
import struct
import pudb
import random
import socket


class peer():
    # Can't initialize without a dictionary. Handshake
    # takes place using socket before peer init
    def __init__(self, sock, reactor, torrent, data):
        self.sock = sock
        self.sock.setblocking(False)
        self.reactor = reactor
        self.torrent = torrent
        self.valid_indices = []
        self.bitfield = None
        self.states = {'reading_length': 0, 'reading_id': 1,
                       'reading_message': 2}
        self.save_state = {'state': self.states['reading_length'],
                           'length': None, 'message_id': None,
                           'message': None, 'remainder': None}

    '''
    Call select
    Try to read from socket
    Might get as little as *1 byte*
    Suppose it's a new message and we're expecting to get a length
        - Save state as 'reading length'
        - Save the partial length in lbytes
    We've gotten the length and we just got the id:
        - Save state as 'reading message'
        - Save the message_id as 'message_id'
    We've gotten the length and we're expecting a message
        - Keep state as 'reading message'
        - Record the partial message
    We hit the end of a message:
        - Return the message
        - Reset all fields of save_state to 0
    '''

    def fileno(self):
        return self.sock.fileno()

    def getsockname(self):
        return self.sock.getsockname()

    def read(self):
        print 'inside peer.read'
        try:
            instr = self.sock.recv(self.max_size)
            self.process_input(instr)
            self.reactor.subscribed['read'].remove(self.read)
        except socket.error as e:
            print e.message

    '''
    Want to read whatever's available on the socket
    - Check state
    - Base case is "reading length"
        - get_message_length (4 bytes)
            - if there's more message, get_message_id
            - else save state as 'reading_id'
        - get_message_id (1 byte)
            - if there's more message, get_message
            - else save state as 'reading_message'
        - get_message (message-length - 1 bytes)
            - if len(message) == message_length - 1:
                - respond to the message
                - zero out stateful stuff
            - elif len(message) < message_length -1:
                - save partial message
                - save state as 'reading message'
    '''

    def process_input(self, instr):
        # pudb.set_trace()
        while instr:
            if self.save_state['state'] == self.states['reading_length']:
                instr = self.get_message_length(instr)
            elif self.save_state['state'] == self.states['reading_id']:
                instr = self.get_message_id(instr)
            elif self.save_state['state'] == self.states['reading_message']:
                instr = self.get_message(instr)

    def get_message_length(self, instr):

            # If we already have a partial message, start with that
            if self.save_state['remainder']:
                instr = self.save_state['remainder'] + instr
                self.save_state['remainder'] = None

            # If we have four bytes we can at least read the length
            if len(instr) >= 4:
                # Need 0 index because struct.unpack returns tuple
                self.save_state['length'] = struct.unpack('>i', instr[0:4])[0]
                self.save_state['state'] = self.states['reading_id']
                return instr[4:]

            # Less than four bytes and we save + wait for next read
            else:
                self.save_state['remainder'] = instr
                return None  # Will break out of process_input loop

    def get_message_id(self, instr):
        # No need to do the partial message check because
        # len(instr) is guaranteed to be >= 1B
        self.save_state['message_id'] = struct.unpack('b', instr[0])[0]
        self.save_state['state'] = self.states['reading_message']
        return instr[1:]

    def get_message(self, instr):
        # Since one byte is getting used up for the message_id
        message_length = self.save_state['length'] - 1
        if self.save_state['remainder']:
            instr = self.save_state['remainder'] + instr
        if len(instr) >= message_length:
            self.save_state['message'] = instr[:message_length]

            # When we get a whole message we handle it, then
            # zero out all our state variables
            self.handle_message()
            self.save_state['message'] = None
            self.save_state['message_id'] = None
            self.save_state['state'] = self.states['reading_length']
            return instr[message_length:]
        else:
            self.save_state['remainder'] += instr
            return None

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
            self.ppiece()
        elif self.save_state['message_id'] == 8:
            self.pcancel()
        elif self.save_state['message_id'] == 9:
            pass

    def pchoke(self):
        pass

    def punchoke(self):
        pass

    def pinterested(self):
        pass

    def pnotinterested(self):
        pass

    def phave(self):
        index = struct.unpack('>i', self.save_state['message'])[0]
        self.bitfield[index] = True
        print repr(self.bitfield)

    def pbitfield(self):
        self.bitfield = bitarray()
        self.bitfield.frombytes(self.save_state['message'])
        print 'this is the bitfield', self.bitfield
        self.interested()

    def prequest(self):
        pass

    def ppiece(self):
        pass

    def pcancel(self):
        pass

    def logic(self):
        print 'inside logic'
        for i in range(len(self.bitfield)):
            if self.bitfield[i] == 1:
                self.valid_indices.append(i)
        print self.valid_indices
        while 1:
            next_request = random.choice(self.valid_indices)
            if next_request not in self.torrent.queued_requests:
                self.torrent.queued_requests.append(next_request)
                break
        self.request(next_request)

    def interested(self):
        print 'inside interested'
        packet = ''.join(struct.pack('>ib', 1, 2))
        self.sock.send(packet)

    def request(self, piece):
        print 'inside request'
        # TODO -- global lookup for id/int conversion
        packet = ''.join(struct.pack('>ibii', piece, 6, 0,
                         self.torrent.piece_length))
        self.sock.send(packet)

    def cleanup(self):
        print 'cleaning up'
        self.torrent.queued_requests = []
