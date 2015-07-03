import re
import jinja2
import pyparsing
import bleach
from .attachments import THUMB_PATTERN
from pyparsing import QuotedString, ParserElement, LineStart, LineEnd, SkipTo, OneOrMore, restOfLine
from .util import mime2thumb_ext

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

# TODO: Probably find a better way to sanitize only output without allowing users to use HTML postlinks directly
def post_smart_escape(s):
    allowed_tags = ['a']
    
    valid_postlink_href = re.compile(r'/[a-zA-Z0-9_]+/thread/[0-9]+/#post\-[0-9]+', re.IGNORECASE)
    valid_id = re.compile(r'[0-9]+')
    
    # Allows only postlinks
    def filter_link_attribute(name, value):
        if name not in ['href', 'class', 'data-post-id', 'data-thread-id']: return False
        if name == 'href' and not valid_postlink_href.match(value): return False
        if name == 'class' and value != 'postlink': return False
        if name in ['data-post-id', 'data-thread-id']:
            if not valid_id.match(value): return False
        return True
    
    allowed_attributes = {'a': filter_link_attribute}
    return jinja2.Markup( bleach.clean(s, tags=allowed_tags, attributes=allowed_attributes) )

def remove_miliseconds(s):
    return str(s).rsplit('.', 1)[0]

def thumb_link(attachment):
    filename = attachment.resource.rsplit('.', 1)[0]
    extension = mime2thumb_ext(attachment.type)
    
    return THUMB_PATTERN.format(name=filename, ext=extension)
    #return s.rsplit('.', 1)[0] + '_thumb.' + mime2thumb_ext(mimetype)

jinja2.filters.FILTERS['aib_markup'] = aib_markup
jinja2.filters.FILTERS['post_smart_escape'] = post_smart_escape
jinja2.filters.FILTERS['remove_miliseconds'] = remove_miliseconds
jinja2.filters.FILTERS['thumb_link'] = thumb_link

