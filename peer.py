from bitarray import bitarray
import struct


class peer():
    # Can't initialize without a dictionary. Handshake
    # takes place using socket before peer init
    def __init__(self, sock, reactor, data):
        self.sock = sock
        self.sock.setblocking(False)
        self.reactor = reactor
        self.save_state = {'state': None, 'length': None, 'lbytes': None,
                           'message_id': None, 'message': None,
                           'remainder': None}
        self.states = {'reading_length': 0, 'reading_id': 1,
                       'reading_message': 2}

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

    # def recv(self, size):
    #     f = self.sock.recv(size)
    #     return f

    # def read(self):
    #     if not self.save_state['state']:
    #         pass
    #     elif self.save_state['state'] == self.states['reading_length']:
    #         length_stub = self.save_state['length']
    #         length = self.get_message_length(length_stub)
    #         if len(length) >= 4:
    #             self.save_state['length'] = struct.unpack('>i', length)[0]

    #     elif self.save_state['state'] == self.states['reading_id']:
    #         self.get_message_id()
    #     if any(self.save_state['length'], self.save_state['message']):
    #         length = self.save_state['length']
    #         message = self.save_state['message']
    #     length = self.get_message_length()
    #     message_id = self.get_message_id()
    #     message = self.get_message()
    #     if message is not None:
    #         self.handle_message()

    def read(self):
        instr = self.sock.recv(self.max_size)
        self.process_input(instr)

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
                self.save_state['length'] = struct.unpack('>i', instr[0:4])
                return instr[4:]

            # Less than four bytes and we save + wait for next read
            else:
                self.save_state['remainder'] = instr
                return None  # Will break out of process_input loop

    def get_message_id(self, instr):
        # No need to do the partial message check because
        # len(instr) is guaranteed to be >= 1B
        self.save_state['message_id'] = struct.unpack('b', instr[0])
        return instr[1:]

    def get_message(self, instr):
        # Since one byte is getting used up for the message_id
        message_length = self.save_state['message_length'] - 1
        if self.save_state['remainder']:
            instr = self.save_state['remainder'] + instr
        if len(instr) >= message_length:
            self.save_state['message'] = instr[:message_length]
            instr = instr[message_length:]

            # When we get a whole message we handle it, then
            # zero out all our state variables
            self.handle_message()
            self.save_state['message'] = None
            self.save_state['message_id'] = None
            return instr
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

    def save_state(self, psocket, message, length):
        def save_clos(self, psocket, message, length):
            print 'save_state'
        return save_clos

    def unchoke(self, psocket):
        def unchoke_clos(self, psocket):
            message = struct.pack('>ib', 1, 1)
            print ('sending unchoke message'
                   '{}').format(message.encode('latin-1'))
            psocket.send(message)
        return unchoke_clos

    def interested(self, psocket):
        def interested_clos(self, psocket):
            message = struct.pack('>ib', 1, 2)
            print ('sending interested message'
                   '{}').format(message.encode('latin-1'))
        return interested_clos

    def request(self, psocket):
        def request_clos(self, psocket):
            message = struct.pack('ibiii', 13, 6, 0, 0,
                                  self.tdict['info']['piece length'])
            psocket.send(message)
        return request_clos
