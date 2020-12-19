
import re
import pywikibot

article = 'Father Christmas'


wikipedia = pywikibot.Site('en', 'wikipedia')
page = pywikibot.Page(wikipedia, article)

def get_lead(page):
    global wikipedia
    sections = pywikibot.textlib.extract_sections(page.text, wikipedia)
    text = sections[0]
    print(text)
    text = re.sub(r"{{.*?}}", "", text)
    print(text)
    text = re.sub(r"^\[\[File:.*?\]\]$", "", text)
    print('1:', text)
    text = re.sub(r"\[\[([^\]\[|]*)\|", "[[", text, re.MULTILINE)
    if "}}" in text:
        text = text.split("}}")[-1]
    text = re.sub(r"<ref.*?</ref>", "", text, re.MULTILINE)
    text = re.sub(r"&nbsp;", " ", text, re.MULTILINE)
    text = re.sub(r"[\[\]]+", "", text, re.MULTILINE)
    text = re.sub(r"[^A-Za-z0-9,\.;:\- ]+", "", text, re.MULTILINE)
    text = text[0:120].strip()
    if '.' in text:
        text = text.rpartition('.')[0] + '.'  # Chop out everything after the last full stop, if there is one
    return text



print(get_lead(page))

#  Baltasarq CC BY-SA 3.0
# https://stackoverflow.com/questions/29991917/indices-of-matching-parentheses-in-python/29992065

def find_parens(s):
    toret = {}
    pstack = []

    for i, c in enumerate(s):
        if c == '(':
            pstack.append(i)
        elif c == ')':
            if len(pstack) == 0:
                raise IndexError("No matching closing parens at: " + str(i))
            toret[pstack.pop()] = i

    if len(pstack) > 0:
        raise IndexError("No matching opening parens at: " + str(pstack.pop()))

    return toret