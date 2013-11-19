names = ['Mary', 'Isla', 'Sam']


def code_name(input_names):
    return map(lambda x: hash(x), input_names)


def main():
    code_names = code_name(names)
    print code_names

if __name__ == '__main__':
    main()

