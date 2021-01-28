# See sd_run.py for status and copyright release information

import time
import mwparserfromhell
from pywikibot.data import api

from shortdesc_generator import *


# FUNCTIONS

# Check to see if page matches the criteria. Returns (True, '') or (False, reason)
def check_criteria(page, lead_text):
    # We need to match on *everything* specified in the criteria
    # Returns (True, '') or (False, reason)

    if lead_text == '':
        return False, 'Could not create lead (unpaired delimiters)'
    if required_words:  # Skip if required_words == []
        for required in required_words:
            if required not in lead_text:
                return False, 'Required word missing - ' + required
    if excluded_words:
        for excluded in excluded_words:
            if excluded in lead_text:
                return False, 'Excluded word present - ' + excluded
    none_found = True
    if some_words:
        for some_word in some_words:
            if some_word in lead_text:
                none_found = False
                break
        if none_found:
            return False, 'None of the some_words are present'

    if text_regex_tf:
        result = text_regex.match(lead_text)  # Returns object if a match, or None
        if result is None:
            return False, 'Lead does not match regex'
    if title_regex_tf:
        result = title_regex.match(page.title())  # Returns object if a match, or None
        if result is None:
            return False, 'Title does not match regex'

    return True, ''


# Are we interested in this page at all?  Returns (True, '') or (False, reason)
def check_page(page):
    has_infobox = False
    # Ignore articles entitled "List of ..."
    if 'list of' in page.title().lower():
        return False, 'Is a list article'
    # Check for existing short description, where relevant
    existing_type = existing_shortdesc(page)[1]
    if not override_manual and existing_type == 'manual':
        return False, 'Already has manual short description'
    if not override_embedded and existing_type == 'embedded':
        return False, 'Already has embedded short description'
    # Ignore redirects
    if '#REDIRECT' in page.text:
        return False, 'Is a redirect'
    # Check for required infobox(es)
    if require_infobox:
        for item in infobox_strings:  # Check through the various strings that identify an infobox
            if item.lower() in page.text.lower():
                has_infobox = True
        if not has_infobox:
            return False, 'Does not have infobox'
        if sole_infobox:
            if count_infoboxes(page) > 1:
                return False, 'Has multiple infoboxes'

    return True, ''


# Check for existing sd. Return (sd, 'manual') if standard sd template, or (sd, 'embedded) if created eg via an infobox
def existing_shortdesc(page):
    description = ''
    pageinfo = get_pageinfo(wikipedia, page)
    for item in pageinfo['query']['pages']:
        try:
            description = pageinfo['query']['pages'][item]['pageprops']['wikibase-shortdesc']
        except:
            pass
    if '{{short description' in page.text or '{{Short description' in page.text:
        sdtype = 'manual'
    else:
        sdtype = 'embedded'
    if len(description) > 0:
        return description, sdtype
    return '', None


# Get the description from Wikidata
def get_wikidata_desc(page):
    try:
        wd_item = pywikibot.ItemPage.fromPage(page, wikipedia)
        item_dict = wd_item.get()
        qid = wd_item.title()
    except:
        print('WIKIDATA ERROR: No QID recovered')
        return ''
    try:
        return item_dict['descriptions']['en']
    except:
        return ''


# Create dictionary of paired parenthetical characters
# Based on code by Baltasarq CC BY-SA 3.0
# https://stackoverflow.com/questions/29991917/indices-of-matching-parentheses-in-python
def find_parens(s, op, cl):  # (Note: op and cl must be single characters)
    return_dict = {}
    pstack = []

    for i, c in enumerate(s):
        if c == op:
            pstack.append(i)
        elif c == cl:
            if len(pstack) == 0:
                raise IndexError("No matching closing parens at: " + str(i))
            return_dict[pstack.pop()] = i

    if len(pstack) > 0:
        raise IndexError("No matching opening parens at: " + str(pstack.pop()))

    return return_dict


# Remove and clean up unwanted characters in textstr (close_up works for both bold and italic wikicode)
def clean_text(textstr):
    close_up = ["`", "'''", "''", "[", "]", "{", "}", "__NOTOC__"]
    convert_space = ["\t", "\n", "  ", "&nbsp;"]
    for item in close_up:
        textstr = textstr.replace(item, "")
    for item in convert_space:
        textstr = textstr.replace(item, " ")
    textstr = textstr.replace("&ndash;", "–")
    textstr = textstr.replace("&mdash;", "—")

    return textstr


# Get the first 150 chars of the lead
def get_lead(page):
    sections = pywikibot.textlib.extract_sections(page.text, wikipedia)
    lead = sections[0]

    # Remove any templates: {{ ... }}
    # First, replace template double braces with single so that we can use find_parens
    lead = lead.replace("{{", "{")
    lead = lead.replace("}}", "}")
    try:
        result = find_parens(lead, '{', '}')  # Get start and end indexes for all templates
    except IndexError:
        return ''
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
        return ''
    # Go through results and replace wikicode representing images with ` strings of same length
    for key in result:
        start = key
        end = result[key]
        strstart = lead[start + 1:start + 7]
        if 'File:' in strstart or 'Image:' in strstart:
            length = end - start + 1
            lead = lead.replace(lead[start:end + 1], "`" * length)

    # Deal with redirected wikilinks: replace [xxx|yyy] with [yyy]
    lead = re.sub(r"\[([^\]\[|]*)\|", "[", lead, re.MULTILINE)

    # Remove any references: <ref ... /ref> (can't deal with raw HTML such as <small> ... </small>)
    lead = re.sub(r"<.*?>", "", lead, re.MULTILINE)

    # Delete the temporary ` strings and clean up
    lead = clean_text(lead)
    # Reduce length to 150, and chop out everything after the last full stop, if there is one
    lead = lead[:150].strip()

    return lead


# Count the number of infoboxes
def count_infoboxes(page):
    count = 0
    templates = pywikibot.textlib.extract_templates_and_params(page.text)
    for template in templates:
        if 'infobox' in template[0].lower():
            count += 1
    return count


# Fetch the page
def get_pageinfo(site, itemtitle):
    params = {'action': 'query',
              'format': 'json',
              'prop': 'pageprops',
              'titles': itemtitle}
    request = api.Request(site=site, parameters=params)
    return request.submit()


# Bots template exclusion compliance. Code from https://en.wikipedia.org/wiki/Template:Bots#Python
# Released under CC BY-SA 3.0, page editors.
def allow_bots(text, user):
    user = user.lower().strip()
    text = mwparserfromhell.parse(text)
    for tl in text.filter_templates():
        if tl.name.matches(['bots', 'nobots']):
            break
    else:
        return True
    for param in tl.params:
        bots = [x.lower().strip() for x in param.value.split(",")]
        if param.name == 'allow':
            if ''.join(bots) == 'none': return False
            for bot in bots:
                if bot in (user, 'all'):
                    return True
        elif param.name == 'deny':
            if ''.join(bots) == 'none': return True
            for bot in bots:
                if bot in (user, 'all'):
                    return False
    if tl.name.matches('nobots') and len(tl.params) == 0:
        return False
    return True


# Stop when c exceeds a non-zero value of max. If max = 0, don't stop at all
def stop_now(max, c):
    if not max:
        return False
    elif c < max:
        return False
    return True


# Require a 'y' input to process the page. Assisted mode is assumed
def confirm_edit(tit, ex_desc, ex_type, desc):
    if ex_type is None:
        key_input = input(
            f'Add "{desc}" \nto https://en.wikipedia.org/wiki/{tit.replace(" ", "_")} "? [y]es/[s]top ')
        return key_input
    if ex_type == 'manual' or 'embedded':
        key_input = input(
            f'Replace {ex_type} description "{ex_desc}" with "{desc}" \nin'
            f' https://en.wikipedia.org/wiki/{tit.replace(" ", "_")} "? [y]es/[s]top ')
        return key_input

    print('ERROR in confirm_edit')
    return 'n'

