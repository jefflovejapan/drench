def _readchar(bstring):
    for char in bstring:
        yield char


def bencode(canonical):
    '''
        Turns a dictionary into a bencoded str with alphabetized keys
        e.g., {'spam': 'eggs', 'cow': 'moo'} --> d3:cow3:moo4:spam4:eggse
    '''
    in_dict = dict(canonical)

    def encode_str(in_str):
        out_str = str(len(in_str)) + ':' + in_str
        return out_str

    def encode_int(in_int):
        out_str = str('i' + str(in_int) + 'e')
        return out_str

    def encode_list(in_list):
        out_str = 'l'
        for item in in_list:
            out_str += encode_item(item)
        else:
            out_str += 'e'
        return out_str

    def encode_dict(in_dict):
        out_str = 'd'
        keys = sorted(in_dict.keys())
        while in_dict:
            for key in keys:
                val = in_dict.pop(key)
                out_str = out_str + encode_item(key) + encode_item(val)
            else:
                out_str += 'e'
        return out_str

    def encode_item(x):
        if isinstance(x, str):
            return encode_str(x)
        elif isinstance(x, int):
            return encode_int(x)
        elif isinstance(x, list):
            return encode_list(x)
        elif isinstance(x, dict):
            return encode_dict(x)

    return encode_item(in_dict)


def bdecodes(bstring):
    '''
        Bdecodes a bencoded string
        e.g., d3:cow3:moo4:spam4:eggse -> {'cow': 'moo', 'spam': 'eggs'}
    '''

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

    reader = _readchar(bstring)
    dict_repr = get_val()
    return dict_repr


def bdecode(filename):
    '''
        Bdecodes a .torrent or other bencoded file
    '''
    with open(filename) as f:
        return bdecodes(f.read())
