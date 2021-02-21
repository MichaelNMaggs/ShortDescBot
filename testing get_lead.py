# Just some ad hoc tests. Not part of the codebase

import re

import pywikibot
from pywikibot.data import api

from sd_functions import clean_text, find_parens

article = 'Eremoneura'
wikipedia = pywikibot.Site('en', 'wikipedia')
page = pywikibot.Page(wikipedia, article)

if not page.exists():
    print(' PAGE DOES NOT EXIST')


def get_lead(page):
    sections = pywikibot.textlib.extract_sections(page.text, wikipedia)
    lead = sections[0]
    #print('\n' + "ORIGINAL" + '\n' + lead)

    # Remove any templates: {{ ... }}
    # First, replace template double braces with single so that we can use find_parens
    lead = lead.replace("{{", "{")
    lead = lead.replace("}}", "}")
    try:
        result = find_parens(lead, '{', '}')  # Get start and end indexes for all templates
    except IndexError:
        return None
    # Go through templates and replace with ` strings of same length, to avoid changing index positions
    for key in result:
        start = key
        end = result[key]
        length = end - start + 1
        lead = lead.replace(lead[start:end + 1], "`" * length)

    # Remove any images: [[File: ... ]] or [[Image: ... ]]
    # Replace double square brackets with single so that we can use find_parens
    lead = lead.replace("[[", "[")
    lead = lead.replace("]]", "]")
    try:
        result = find_parens(lead, '[', ']')  # Get start and end indexes for all square brackets
    except IndexError:
        return None
    # Go through results and replace wikicode representing images with ` strings of same length
    for key in result:
        start = key
        end = result[key]
        strstart = lead[start + 1:start + 7]
        #print(strstart)
        if 'File:' in strstart or 'Image:' in strstart:
            length = end - start + 1
            lead = lead.replace(lead[start:end + 1], "`" * length)

    # Deal with redirected wikilinks: replace [xxx|yyy] with [yyy]
    lead = re.sub(r"\[([^\]\[|]*)\|", "[", lead, re.MULTILINE)

#  ***********  REFS TO DO  *************

    # Remove any references: < ... > (can't deal with raw HTML tags such as <small> ... </small>)
    lead = re.sub(r"<.*?>", "", lead, re.MULTILINE)

    # Delete the temporary ` strings and clean up
    lead = clean_text(lead)
    lead = lead[:150].strip()

    return lead

print('\n')
print(get_lead(page))
