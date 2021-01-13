# Code for ShortDescBot, task 1 - moths
#
# Michael Maggs, released under GPL v3
# Incorporates code by Mike Peel, GPL v3, 28 November 2020:
# https://bitbucket.org/mikepeel/wikicode/src/master/shortdesc_run.py and
# https://bitbucket.org/mikepeel/wikicode/src/master/shortdesc_functions.py
# Latest update 13 January 2021.


import time

import mwparserfromhell
from pywikibot import pagegenerators
from pywikibot.data import api

from sd_config import *


# FUNCTIONS

# Check to see if page matches the criteria. Returns (True, '') or (False, reason)
def check_criteria(page, lead_text):
    # We need to match on *everything* specified in the criteria -
    # Returns (True, '') or (False, reason)
    for required in required_words:
        if required not in lead_text:
            return False, 'Required word missing - ' + required
    for excluded in excluded_words:
        if excluded in lead_text:
            return False, 'Excluded word present - ' + excluded

    if test_regex_tf:
        result = test_regex.match(lead_text)  # Returns object if a match, or None
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
    # Check for existing short description
    if shortdesc_exists(page):
        return False, 'Already has short description'
    # Ignore redirects
    if 'REDIRECT' in page.text:
        return False, 'Is a redirect'
    # Check for required infobox, and no more than one if specified
    if require_infobox:
        for option in infobox_strings:  # Check through the various strings that identify an infobox
            if option in page.text.lower():
                has_infobox = True
        if not has_infobox:
            return False, 'Does not have infobox'
        if sole_infobox:
            if count_infoboxes(page) > 1:
                return False, 'Has multiple infoboxes'

    return True, ''


# Does a description already exist? Check the page info rather just the lead in order to find cases where some
# template auto-includes it without using the short description template
def shortdesc_exists(page):
    description = ''
    test = get_pageinfo(wikipedia, page)
    for item in test['query']['pages']:
        try:
            description = test['query']['pages'][item]['pageprops']['wikibase-shortdesc']
        except:
            pass
    if len(description) > 0:
        return True
    return False


# Generate the draft sd. Called by shortdesc_stage. Returns (True, description) for good result, or (False, errortext)
# *** For each task, the code here needs to be hand-crafted ***
def shortdesc_generator(page):
    title = page.title()
    base_sd1 = 'Species of moth'
    base_sd2 = 'Genus of moths'

    title_nobra = re.sub(r'\(.+?\)', '', title).strip()
    title_nobra_len = len(title_nobra.split())

    if title_nobra_len == 2:
        return True, base_sd1
    if title_nobra_len == 1:
        return True, base_sd2

    return False, "Can't create description"


# Main function for 'stage' mode
# Calls check_page, check_criteria and shortdesc_generator
def shortdesc_stage():
    count_arts = 0
    count_success = 0
    count_success_examples = 0
    count_failure = 0
    count_failure_examples = 0
    success_str = ''
    success_examples_str = ''
    failure_str = ''
    failure_examples_str = ''
    tripped = False

    # Set up pages as iterable, from cat or from Petscan filer. Each item in pages must be created as a Pywikibot object
    if petscan_tf:  # Import a file of Petscan results
        pages = []
        with open(petscan_file) as f:
            data = f.read()
            todo = data.splitlines()
        for line in todo:
            values = line.split('\t')
            if values[0] == 'number':  # Ignore any header line
                continue
            title = values[1]
            page = pywikibot.Page(wikipedia, title)
            pages.append(page)

    else:  # Use articles in the Wikipedia category
        cat = pywikibot.Category(wikipedia, targetcat)
        pages = pagegenerators.CategorizedPageGenerator(cat, recurse=False, namespaces=[0])

    # Main loop
    for page in pages:
        print(page)

        # If partial is True, skip over initial pages until we reach the startpoint
        if partial and not tripped:
            at_startpoint = startpoint in page.title()
            tripped = at_startpoint
            if not at_startpoint:
                continue

        # Get info related to this page, on enWP and from Wikidata
        lead_text = get_lead(page)
        wikidata_sd = get_wikidata_desc(page)
        if verbose_stage:
            print('\nPROCESSING NEW PAGE IN SHORTDESC_STAGE')
            print('lead_text: ', lead_text)

        # Do we want this page? Check against page definition
        result_page = check_page(page)

        # Should we skip this page? (not recorded in the list of failures)
        if not result_page[0]:
            skip_text = result_page[1]
            print(page.title() + ' - Skipped: ' + skip_text)
            continue

        # We have a page to work with. Check whether it matches or fails the criteria
        result_criteria = check_criteria(page, lead_text)

        # If the page fails the criteria, note as such and write a new line to failure_str, for staging later
        if not result_criteria[0]:
            errortext = result_criteria[1]
            print(page.title() + ' - FAILED: ' + errortext)
            if not stop_now(max_stage, count_failure):
                count_failure += 1
                failure_str += page.title() + ' | ' + errortext + ' | ' + wikidata_sd + ' | ' + lead_text + '\n'

            # If needed, also build up failure_examples_str ready to write to userspace
            if wp_examples and count_failure_examples <= max_examples:
                count_failure_examples += 1
                failure_examples_str += '|-\n'
                failure_examples_str += '| [[' + page.title() + ']] || ' + errortext + ' || ' + wikidata_sd + ' || ' \
                                        + lead_text + '\n'

            count_arts += 1
            if stop_now(max_arts, count_arts):
                break

            continue

        # The page matches the criteria, and we now need to work out the new short description
        result_gen = shortdesc_generator(page)

        #  Failed to create a usable short description. Treat as if it were a page failure and write to failure_str
        if not result_gen[0]:
            errortext2 = result_gen[1]
            print(page.title() + ' - FAILED: ' + errortext2)

            if not stop_now(max_stage, count_failure):
                count_failure += 1
                failure_str += page.title() + ' | ' + errortext2 + ' | ' + wikidata_sd + ' | ' + lead_text + '\n'

            # If needed, also build up failure_examples_str ready to write to userspace
            if wp_examples and (count_failure_examples <= max_examples):
                count_failure_examples += 1
                failure_examples_str += '|-\n'
                failure_examples_str += '| [[' + page.title() + ']] || ' + errortext2 + ' || ' + wikidata_sd + ' || ' \
                                        + lead_text + '\n'

            count_arts += 1
            if stop_now(max_arts, count_arts):
                break

            continue

        # We have a good draft description!
        description = result_gen[1]
        print(str(count_arts + 1) + ': ' + page.title() + ' - STAGING NEW SD: ' + description)

        # Build up success_str string ready to save to local file
        if not stop_now(max_stage, count_success):
            count_success += 1
            success_str += page.title() + ' | ' + description + ' | ' + wikidata_sd + ' | ' + lead_text + '\n'

        #  If needed, also build up success_examples_str string ready to write to userspace
        if wp_examples and count_success_examples <= max_examples:
            count_success_examples += 1
            success_examples_str += '|-\n'
            success_examples_str += '| [[' + page.title() + ']] || ' + description + ' || ''' + wikidata_sd + ' || ' \
                                    + lead_text + '\n'

        count_arts += 1
        if stop_now(max_arts, count_arts):
            break
        if stop_now(max_stage, count_success):
            break

        # If partial is True, stop when we reach the endpoint
        if partial and tripped:
            at_endpoint = endpoint in page.title()
            if at_endpoint:
                break

    # Finished creating the strings. Now stage the successes to success_file
    with open(success_file, 'w') as f1:
        f1.write(success_str)

    # Write examples to my userspace
    if wp_examples:
        page = pywikibot.Page(wikipedia, success_examples_wp)
        header_text = "\n|+\nShortDescBot proposed short descriptions\n!Article\n!Proposed SD\n!(Wikidata " \
                      "SD)\n!Opening words of the lead\n"
        page.text = 'The bot does not use Wikidata\'s short description in any way. It is listed here for reference ' \
                    'only\n{| class="wikitable"' + header_text + success_examples_str + "|}"
        page.save("Saving a sample of ShortDescBot draft short descriptions")
        print('Examples are at https://en.wikipedia.org/wiki/' + success_examples_wp.replace(' ', '_'))

    #  Write the failures to failure_file
    with open(failure_file, 'w') as f2:
        f2.write(failure_str)

    # Write examples of failures to my userspace
    if wp_examples:
        page = pywikibot.Page(wikipedia, failure_examples_wp)
        header_text = "\n|+\nShortDescBot failed pages\n!Article\n!Reason for failure\n!(Wikidata SD)\n!Opening words " \
                      "" \
                      "" \
                      "" \
                      "" \
                      "" \
                      "" \
                      "" \
                      "of the lead\n"
        page.text = 'The bot does not use Wikidata\'s short description in any way. It is listed here for reference ' \
                    'only' \
                    ' \n{| class="wikitable"' + header_text + failure_examples_str + "|}"
        page.save("Save a sample of ShortDescBot failed pages")
        print('Failures are at https://en.wikipedia.org/wiki/' + failure_examples_wp.replace(' ', '_'))

    try:
        targets = count_failure + count_success
        succ_pc = round(100 * count_success / targets, 2)
        fail_pc = round(100 * count_failure / targets, 2)
        print(f'\nThe draft short descriptions are staged in {success_file}, with failures in {failure_file}')
        print(f'\nTARGETS: {targets}  SUCCESS: {count_success} ({succ_pc}%)  FAILURE: {count_failure} ({fail_pc}%)')
    except:
        print('\nNo target articles found.')
    return


# Main function for 'edit' mode. Write the descriptions to mainspace, reading in from local success_file
def shortdesc_add():
    # Check login and work out text for edit summaries
    if username == 'MichaelMaggs':
        edit_text = 'Adding short description'
    elif username == 'ShortDescBot':
        edit_text = '[[User:ShortDescBot|ShortDescBot]] adding short description'
    else:
        print('STOPPING - unexpected username: ', username)
        return

    count = 0
    # Get the list of articles and the draft short descriptions from local file
    with open(success_file) as f:
        data = f.read()
        todo = data.splitlines()

    # Work through them one by one
    for line in todo:
        values = line.split('\t')  # **** NOTE CHANGED ****
        page = pywikibot.Page(wikipedia, values[0].strip())
        if not page.exists():
            print(page.title() + ' -  PAGE DOES NOT EXIST')
            return
        description = values[1].strip()

        # Check for Bots template exclusion
        if not allow_bots(page.text, username):
            print(page.title() + ' - NO EDIT MADE: Bot is excluded via the Bots template')
            continue
        # Only if we don't have a table header
        if '{|' not in line and '|}' not in line and line.strip() != '':
            # Check again that page still has no existing description
            if shortdesc_exists(page):
                print(page.title() + ' - NO EDIT MADE: Page now has a description')
                continue
            test = 'y'
            if debug:
                test = 'n'
                test = input(
                    'Add "' + description + '" to https://en.wikipedia.org/wiki/' + values[0].strip().replace(
                        ' ', '_') + "? (Type 'y' to apply)")
            if test == 'y':
                count += 1
                print(str(count + 1) + ': ' + page.title() + ' - WRITING NEW SD: ' + description)
                page.text = '{{Short description|' + description + '}}\n' + page.text
                try:
                    page.save(edit_text + ' "' + description + '"', minor=False)
                except:
                    print(f"UNABLE TO EDIT {page.title()}. Will retry in 1 minute")
                    time.sleep(60)
                    try:
                        page.save(edit_text + ' "' + description + '"', minor=False)
                    except:
                        print(f"STILL UNABLE TO EDIT {page.title()}. Skipping this page")

            time.sleep(wait_time)

    print(f"\nDONE! Added short descriptions to {str(count)} articles ")
    return


# Get the description from Wikidata
def get_wikidata_desc(page):
    try:
        wd_item = pywikibot.ItemPage.fromPage(page, wikipedia)
        item_dict = wd_item.get()
        qid = wd_item.title()
    except:
        print('ERROR: No qid recovered from Wikidata')
        return ''
    try:
        return item_dict['descriptions']['en']
    except:
        return ''


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


# Get the first sentence or sentences (up to 120 chars) of the lead
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
    if '.' in lead:
        lead = lead.rpartition('.')[0] + '.'

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
