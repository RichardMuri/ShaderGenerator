from astor.source_repr import split_lines


def long_pretty_source(source):
    """ Prettify the source.
    """

    return ''.join(split_lines(source, maxline=20000))
