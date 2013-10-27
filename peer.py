from bitarray import bitarray


class peer():
    def __init__(self, sock, reactor, handshake=False):
        self.sock = sock
        self.handshake = handshake
        self.save_state = {'state': None, 'length': None, 'lbytes': None,
                           'message_id': None, 'message': None}
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

# TODO - decide what kinds of triggers I want to make available in reactor
# If sockets are ready to read -- 'read': peers
# When I know what pieces I want -- 'request': peers

# WAIT -- the idea is that I can cue up functions when the internal state
# reaches some threshold. For example:
#   - read from a socket until the message is complete, at which point you
#     sign up for corresponding events
#   - Reactor loop might look like:
#       - Do reads
#       - Add haves
#       - Handle exceptions
#       

    def fileno(self):
        return self.sock.fileno()

    def read(self):
        if not self.save_state['state']:
            pass
        elif self.save_state['state'] = self.states['reading_length']:
            length_stub = self.save_state['length']
            length = self.get_message_length(length_stub)
            if len(length) >= 4:
                self.save_state['length'] = struct.unpack('>i', length)[0]

        elif self.save_state['state'] = self.states['reading_id']:
            self.get_message_id()
        if any(self.save_state['length'], self.save_state['message']):
            length = self.save_state['length']
            message = self.save_state['message']
        length = self.get_message_length()
        message_id = self.get_message_id()
        message = self.get_message()
        if message is not None:
            self.handle_message()

    def try_to_grab(length):
    message = self.sock.recv(length)
    if len(message) == length:
        return message
    else:
        self.save_state = (length, message)

    # If we don't get the whole length we don't return
    def get_message_length(self):
            received = self.try_to_grab(4)
            if received:
                length = struct.unpack('>i', received)[0]
                return length

    # TODO - 
    def get_message(self, sock, length):
        message = sock.recv(length)
        if len(message) == length:
            return message
        else:
            self.save_state(sock, message, length)
            return None





    def get_message_id(self, sock):
        message_id = struct.unpack('b', sock.recv(1))[0]
        return message_id

    def handle_message(self, i, message_id, message):
        if message_id == 0:
            self.pchoke(i)
        elif message_id == 1:
            self.punchoke(i)
        elif message_id == 2:
            self.pinterested(i)
        elif message_id == 3:
            self.pnotinterested(i)
        elif message_id == 4:
            self.phave(i, message)
        elif message_id == 5:
            self.pbitfield(i, message)
        elif message_id == 6:
            self.prequest(i, message)
        elif message_id == 7:
            self.ppiece(i, message)
        elif message_id == 8:
            self.pcancel(i, message)
        elif message_id == 9:
            pass

    def save_state(self, psocket, message, length):
        def save_clos(self, psocket, message, length):
            print 'save_state'
        return save_closure

    def unchoke(self, psocket):
        def unchoke_clos(self, psocket):
            message = struct.pack('>ib', 1, 1)
            print 'sending unchoke message {}'.format(message.encode('latin-1'))
            psocket.send(message)
        return unchoke_clos

    def interested(self, psocket):
        def interested_clos(self, psocket):
            message = struct.pack('>ib', 1, 2)
            print 'sending interested message {}'.format(message.encode('latin-1'))
        return interested_clos

    def request(self, psocket):
        def request_clos(self, psocket):
            message = struct.pack('ibiii', 13, 6, 0, 0,
                                  self.tdict['info']['piece length'])
            psocket.send(message)
        return request_clos

