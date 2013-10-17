class tparser():

    def __init__(self, *args, **kwargs):
        self.infile = args[0]
        self.reader = self.readchar()  # instantiate the function

    # The generator that walks through the .torrent file
    def readchar(self):
        tor_str = self.infile.read()
        for char in tor_str:
            yield char
        else:
            self.infile.close()

    def get_val(self):
        i = self.reader.next()
        if i.isdigit():
            str_len = self.get_len(i)
            return self.get_str(str_len)
        if i == 'd':
            return self.get_dict()
        if i == 'l':
            return self.get_list()
        if i == 'i':
            return self.get_int()
        if i == 'e':
            return None

    def get_len(self, i=''):
        len_str = str(i)
        next_char = self.reader.next()
        if next_char == 'e':  # The line that collapses the dictionary
            return next_char
        while next_char is not ':':
            len_str += next_char
            next_char = self.reader.next()
        else:
            return int(len_str)

    def get_dict(self):
        this_dict = {}
        while 1:
            str_len = self.get_len()
            if str_len == 'e':  # This dict is done
                return this_dict
            key = self.get_str(str_len)
            val = self.get_val()
            this_dict[key] = val

    def get_int(self):
        int_str = ''
        i = self.reader.next()
        while i is not 'e':
            int_str += i
            i = self.reader.next()
        else:
            return int(int_str)

    def get_str(self, str_len):
        this_str = ''
        for i in range(str_len):
            this_str += self.reader.next()
        return this_str

    def get_list(self):
        this_list = []
        while 1:
            val = self.get_val()
            if not val:
                return this_list

    def decode(self):
        dict_repr = self.get_val()
        return dict_repr
