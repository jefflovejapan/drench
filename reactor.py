from collections import defaultdict


class Reactor(object):
    def __init__(self):
        self.subscribed = defaultdict(list)
    def subscribe(self, callback, event):
        self.subscribed[event].append(callback)  # Add our callbacks here
    def trigger(self, event):
        for callback in self.subscribed[event]:  # They get executed when
            callback()                           # their trigger(event)
                                                 # happens