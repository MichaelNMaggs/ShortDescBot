import re

import pywikibot

article = 'Givira basiplagax'
wikipedia = pywikibot.Site('en', 'wikipedia')
page = pywikibot.Page(wikipedia, article)

if not page.exists():
    print(' PAGE DOES NOT EXIST')


def clean_text(textstr):
    # Remove and clean up unwanted characters in textstr (close_up works for both bold and italic wikicode)
    close_up = ["`", "'''", "''", "[", "]", "{", "}", "__NOTOC__"]
    convert_space = ["\t", "\n", "  ", "&nbsp;"]
    for item in close_up:
        textstr = textstr.replace(item, "")
    for item in convert_space:
        textstr = textstr.replace(item, " ")
    textstr = textstr.replace("&ndash;", "–")
    textstr = textstr.replace("&mdash;", "—")

    return textstr


# Create dictionary of paired parenthetical characters
# Based on code by Baltasarq CC BY-SA 3.0
# https://stackoverflow.com/questions/29991917/indices-of-matching-parentheses-in-python
def find_parens(s, op, cl):  # (Note: op and cl must be single characters)
    toret = {}
    pstack = []

    for i, c in enumerate(s):
        if c == op:
            pstack.append(i)
        elif c == cl:
            if len(pstack) == 0:
                raise IndexError("No matching closing parens at: " + str(i))
            toret[pstack.pop()] = i

    if len(pstack) > 0:
        raise IndexError("No matching opening parens at: " + str(pstack.pop()))

    return toret


def get_lead(page):
    sections = pywikibot.textlib.extract_sections(page.text, wikipedia)
    lead = sections[0]
    print('\n' + "ORIGINAL" + '\n' + lead)

    # Remove any templates: {{ ... }}
    # First, replace template double braces with single so that we can use find_parens
    lead = lead.replace("{{", "{")
    lead = lead.replace("}}", "}")
    try:
        result = find_parens(lead, '{', '}')  # Get start and end indexes for all templates
    except IndexError:
        return
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
        return
    # Go through results and replace wikicode representing images with ` strings of same length
    for key in result:
        start = key
        end = result[key]
        strstart = lead[start + 1:start + 7]
        print(strstart)
        if 'File:' in strstart or 'Image:' in strstart:
            length = end - start + 1
            lead = lead.replace(lead[start:end + 1], "`" * length)

    # Deal with redirected wikilinks: replace [xxx|yyy] with [yyy]
    lead = re.sub(r"\[([^\]\[|]*)\|", "[", lead, re.MULTILINE)

    # Remove any references: < ... > (can't deal with raw HTML tags such as <small> ... </small>)
    lead = re.sub(r"<.*?>", "", lead, re.MULTILINE)

    # Delete the temporary ` strings and clean up
    lead = clean_text(lead)
    # Reduce length to 120, and chop out everything after the last full stop, if there is one
    lead = lead[:120].strip()
    if '.' in lead:
        lead = lead.rpartition('.')[0] + '.'

    return lead


final = get_lead(page)
print('\nFINAL\n', final)
