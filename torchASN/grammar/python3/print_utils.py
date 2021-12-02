from astor.source_repr import split_lines
from astor.string_repr import special_unicode, basestring, _properly_indented, string_triplequote_repr


def long_pretty_source(source):
    """ Prettify the source.
    """

    return ''.join(split_lines(source, maxline=20000))


def double_quote_pretty_string(s, embedded, current_line, uni_lit=False,
                  min_trip_str=20, max_line=100):
    """There are a lot of reasons why we might not want to or
       be able to return a triple-quoted string.  We can always
       punt back to the default normal string.
    """

    default = '"{0}"'.format(s)

    # Punt on abnormal strings
    if (isinstance(s, special_unicode) or not isinstance(s, basestring)):
        return default
    if uni_lit and isinstance(s, bytes):
        return 'b' + default

    len_s = len(default)

    if current_line.strip():
        len_current = len(current_line)
        second_line_start = s.find('\n') + 1
        if embedded > 1 and not second_line_start:
            return default

        if len_s < min_trip_str:
            return default

        line_indent = len_current - len(current_line.lstrip())

        # Could be on a line by itself...
        if embedded and not second_line_start:
            return default

        total_len = len_current + len_s
        if total_len < max_line and not _properly_indented(s, line_indent):
            return default

    fancy = string_triplequote_repr(s)

    # Sometimes this doesn't work.  One reason is that
    # the AST has no understanding of whether \r\n was
    # entered that way in the string or was a cr/lf in the
    # file.  So we punt just so we can round-trip properly.

    try:
        if eval(fancy) == s and '\r' not in fancy:
            return fancy
    except Exception:
        pass
    return default
