
import re
import time

import pywikibot
from pywikibot import pagegenerators
from pywikibot.data import api


wikipedia = pywikibot.Site('en', 'wikipedia')







def get_lead(page):
    global wikipedia
    sections = pywikibot.textlib.extract_sections(page.text, wikipedia)
    text = sections[0]
    text = re.sub(r"{{.*?}}", "", text)
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