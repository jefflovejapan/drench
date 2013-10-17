def readchar(filename):
    for char in open(filename).read():
        yield char


def tparse(filename):

    def get_val():
        i = reader.next()
        if i.isdigit():
            str_len = get_len(i)
            return get_str(str_len)
        if i == 'd':
            return get_dict()
        if i == 'l':
            return get_list()
        if i == 'i':
            return get_int()
        if i == 'e':
            return None

    def get_len(i=''):
        len_str = str(i)
        next_char = reader.next()
        if next_char == 'e':  # The line that collapses the dictionary
            return next_char
        while next_char is not ':':
            len_str += next_char
            next_char = reader.next()
        else:
            return int(len_str)

    def get_dict():
        this_dict = {}
        while 1:
            str_len = get_len()
            if str_len == 'e':  # This dict is done
                return this_dict
            key = get_str(str_len)
            val = get_val()
            this_dict[key] = val

    def get_int():
        int_str = ''
        i = reader.next()
        while i is not 'e':
            int_str += i
            i = reader.next()
        else:
            return int(int_str)

    def get_str(str_len):
        this_str = ''
        for i in range(str_len):
            this_str += reader.next()
        return this_str

    def get_list():
        this_list = []
        while 1:
            val = get_val()
            if not val:
                return this_list
            this_list.append(val)

    reader = readchar(filename)
    dict_repr = get_val()
    return dict_repr
