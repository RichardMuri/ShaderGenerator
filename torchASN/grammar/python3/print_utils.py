import ast
from astor import SourceGenerator
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


# class ClassDefSingleLineSourceGenerator(SourceGenerator):
#
#     def __init__(self, indent_with, add_line_information=False,
#                  pretty_string=double_quote_pretty_string,
#                  # constants
#                  len=len, isinstance=isinstance, callable=callable):
#         self.result = []
#         self.indent_with = indent_with
#         self.add_line_information = add_line_information
#         self.indentation = 0  # Current indentation level
#         self.new_lines = 0  # Number of lines to insert before next code
#         self.colinfo = 0, 0  # index in result of string containing linefeed, and
#                              # position of last linefeed in that string
#         self.pretty_string = pretty_string
#         AST = ast.AST
#
#         visit = self.visit
#         result = self.result
#         append = result.append
#
#         def write(*params):
#             """ self.write is a closure for performance (to reduce the number
#                 of attribute lookups).
#             """
#             for item in params:
#                 if isinstance(item, AST):
#                     visit(item)
#                 elif callable(item):
#                     item()
#                 else:
#                     if self.new_lines:
#                         if not self.indentation:
#                             self.new_lines -= 1
#                         append('\n' * self.new_lines)
#                         self.colinfo = len(result), 0
#                         append(self.indent_with * self.indentation)
#                         self.new_lines = 0
#                     if item:
#                         append(item)
#
#         self.write = write

    # def visit_ClassDef(self, node):
    #     have_args = []
    #
    #     def paren_or_comma():
    #         if have_args:
    #             self.write(', ')
    #         else:
    #             have_args.append(True)
    #             self.write('(')
    #
    #     self.decorators(node, 2)
    #     self.statement(node, 'class %s' % node.name)
    #     for base in node.bases:
    #         self.write(paren_or_comma, base)
    #     # keywords not available in early version
    #     for keyword in self.get_keywords(node):
    #         self.write(paren_or_comma, keyword.arg or '',
    #                    '=' if keyword.arg else '**', keyword.value)
    #     self.conditional_write(paren_or_comma, '*', self.get_starargs(node))
    #     self.conditional_write(paren_or_comma, '**', self.get_kwargs(node))
    #     self.write(have_args and '):' or ':')
    #     self.body(node.body)
    #     # if not self.indentation:
    #     #     self.newline(extra=2)
    #
    # def visit_FunctionDef(self, node, is_async=False):
    #     prefix = 'async ' if is_async else ''
    #     # self.decorators(node, 1 if self.indentation else 2)
    #     self.decorators(node, 1)
    #     self.statement(node, '%sdef %s' % (prefix, node.name), '(')
    #     self.visit_arguments(node.args)
    #     self.write(')')
    #     self.conditional_write(' -> ', self.get_returns(node))
    #     self.write(':')
    #     self.body(node.body)
    #     # if not self.indentation:
    #     #     self.newline(extra=2)
