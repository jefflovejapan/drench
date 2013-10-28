from collections import defaultdict
import socket
import select
import time
import pudb
import cPickle
from bitarray import bitarray


class Reactor(object):
    def __init__(self):
        self.subscribed = defaultdict(list)
        self.sock = socket.socket()

        # Tells OS we want to use this socket again
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.sock.bind(('127.0.0.1', 7005))

        # Adding server socket to select_list to check for new connections
        # in same call to select inside event loop
        self.select_list = [self.sock]
        self.sock.listen(5)
        print 'Listening on 127.0.0.1:7005'

    def subscribe(self, callback, event):
        self.subscribed[event].append(callback)  # Add our callbacks here

    def trigger(self, event):
        for callback in self.subscribed[event]:  # They get executed when
            callback()                           # their trigger(event)
                                                 # happens

    def read(self, obj):
        def read_clos():
            print obj.getsockname()
            obj.read()
            self.subscribed['read'].remove(read_clos)
            print self.subscribed['read']
        read_clos.__name__ = "closure that reads on {}".format(repr(obj))
        return read_clos

    def event_loop(self):
        counter = 0
        while 1:
            if counter >= 20:
                return
            rrlist, _, _ = select.select(self.select_list, [], [], 0)
            for i in rrlist:  # Doesn't require if test
                if i == self.sock:
                    # TODO -- expand this into creating new peers
                    newsocket, addr = self.sock.accept()
                    self.select_list.append(newsocket)
                else:
                    clos = self.read(i)
                    self.subscribed['read'].append(clos)
            self.trigger('read')
            counter += 1

        '''
        You only want to call the callbacks if the events actually happened.
        Manage everything by timing / coordinating the callbacks.
        '''

        '''
        How to manage requests:
        - In the metainfo file is a list of ALL 20-byte SHA-1 hash values,
          one for each piece
        - Therefore, the total number of pieces is tdict['info']['pieces']/20
        - Length is the length of the *file* in bytes
        - In the trivial case, I can just fire off 80 requests

        How to store data:
        - Can't just store it all in memory
        - Once I complete a block, I can save it to disk
            - How do I retrieve it?
        '''

    def do_reads(self, rrlist):
        for i in rrlist:
            message_length = self.peerdict[i].get_message_length()
            message_id = self.peerdict[i].get_message_id()
            message = self.peerdict[i].get_message(i, message_length-1)
            self.handle_message(i, message_id, message)


def main():
    reactor = Reactor()
    reactor.event_loop()

if __name__ == '__main__':
    main()
