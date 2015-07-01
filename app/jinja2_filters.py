import re
import jinja2
import pyparsing
from pyparsing import QuotedString, ParserElement, LineStart, LineEnd, SkipTo, OneOrMore, restOfLine

ParserElement.setDefaultWhitespaceChars(' \t')

EOL = LineEnd()
SOL = LineStart()

strong = QuotedString("**") | QuotedString(quoteChar="[b]", endQuoteChar="[/b]")
strong.setParseAction(lambda x: "<strong>%s</strong>" % x[0])

italic = QuotedString("*", escChar='\\') | QuotedString(quoteChar="[i]", endQuoteChar="[/i]")
italic.setParseAction(lambda x: "<i>%s</i>" % x[0])

underline = QuotedString("__") | QuotedString(quoteChar="[u]", endQuoteChar="[/u]")
underline.setParseAction(lambda x: "<u>%s</u>" % x[0])

strike = QuotedString(quoteChar="[s]", endQuoteChar="[/s]")
strike.setParseAction(lambda x: "<s>%s</s>" % x[0])

sup = QuotedString(quoteChar="[sup]", endQuoteChar="[/sup]")
sup.setParseAction(lambda x: "<sup>%s</sup>" % x[0])

sub = QuotedString(quoteChar="[sub]", endQuoteChar="[/sub]")
sub.setParseAction(lambda x: "<sub>%s</sub>" % x[0])

spoiler = QuotedString("%%") | QuotedString(quoteChar="[spoiler]", endQuoteChar="[/spoiler]")
spoiler.setParseAction(lambda x: "<span class=\"spoiler\">%s</span>" % x[0])

quote = SOL + "&gt;" + restOfLine
quote.setParseAction(lambda x: "<span class=\"quote\">%s</span>" % ''.join(x))

br = EOL
br.setParseAction(lambda x: "<br>")

tokens = strong | italic | underline | strike | sup | sub | spoiler | br | quote
grammar = OneOrMore(tokens)

def aib_markup(s):
    return grammar.transformString(s)

jinja2.filters.FILTERS['aib_markup'] = aib_markup