from collections import defaultdict
import select
from collections import namedtuple
from listener import Listener
import pudb


select_response = namedtuple('select_response',
                             'readable writable exceptional')


class Reactor(object):
    def __init__(self):
        self.subscribed = defaultdict(list)
        self.vis_listener = Listener(port=7000)
        self.peer_listener = Listener(port=8000)

        # Adding server socket to select_list to check for new connections
        # in same call to select inside event loop
        self.select_list = [self.vis_listener, self.peer_listener]
        self.out_sock = None

    def subscribe(self, callback, event):
        self.subscribed[event].append(callback)  # Add our callbacks here

    def trigger(self, event):
        for callback in self.subscribed[event]:  # They get executed when
            callback()                           # their trigger(event)
                                                 # happens
        self.subscribed[event] = []              # Zero everything out

    def event_loop(self):
        while 1:
            doable_lists = select_response(*select.select(self.select_list,
                                                          [], [], 1))

            for i in doable_lists.readable:  # Doesn't require if test
                if i == self.vis_listener:
                    # TODO -- expand this into creating new peers
                    self.vis_socket = self.vis_listener.grab()
                    self.select_list.append(self.vis_socket)
                elif i == self.peer_listener:
                    new_socket = self.peer_listener.grab()
                    self.select_list.append(new_socket)
                else:
                    i.read()  # read only returns for Listener

                wclos = i.write
                self.subscribed['write'].append(wclos)
                cclos = i.cleanup
                self.subscribed['cleanup'].append(cclos)

            self.trigger('logic')
            self.trigger('write')
            self.trigger('cleanup')


def main():
    reactor = Reactor()
    reactor.event_loop()

if __name__ == '__main__':
    main()
