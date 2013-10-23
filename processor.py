import Queue


class processor():
    def __init__(self):
        self.queue = Queue.Queue()

    def enqueue(self, clos):
        self.queue.put(clos)

    def run_all(self):
        for i in range(self.queue.qsize()):
            a = self.queue.get()
            a()
