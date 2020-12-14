# Code for ShortDescBot, task 1 - moths
#
# Michael Maggs, released under the GNU General Public License v3
# Incorporates code by Mike Peel as at 28 November 2020:
# https://bitbucket.org/mikepeel/wikicode/src/master/shortdesc_run.py and
# https://bitbucket.org/mikepeel/wikicode/src/master/shortdesc_functions.py
# also released under the GNU General Public License v3.
# Latest update 6 December 2020

import re
import time

import pywikibot
from pywikibot import pagegenerators
from pywikibot.data import api

# Mode of operation:
# 'stage': write to staging file and/or examples to userspace
# 'edit':  read from staging file and write live edits to namespace
mode_flag = 'edit'

# Category to work on
targetcat = 'Category:Moths of China'

# Define the pages that that we are interested in. Others will be skipped without comment
require_infobox = False
infobox_strings = ['infobox']  # Add additional elements for various infobox types
sole_infobox = True  # Skip pages that have more than one infobox (applies only if require_infobox = True)

# Define test criteria. Pages that fail any of these will be recorded
required_words = ['moth']
excluded_words = ['blah ']
test_regex_tf = True
test_regex = re.compile(r'', re.IGNORECASE)
title_regex_tf = True
title_regex = re.compile(r'^((?!list).)*$', re.IGNORECASE)  # Fail any article that's entitled 'List ...'

#  *** For each task the code in shortdesc_generator also needs to be hand-crafted ***

# Maximum number of articles to look through
max_arts = 10000

# Set to 'True' to run live editing in assisted mode (step though and confirm every amendment in advance)
# Run from normal account, not bot account, if before bot approval
debug = True

# Set partial=True to enable processing between startpoint and endpoint. Set as False and '' to process all pages
partial = False
startpoint = 'Hyperoptica ptilocentra'
endpoint = 'Hyposidra aquilaria'

# Stage to file?
stage_to_file = False
max_stage = 10000
success_file = 'Moths.txt'
failure_file = 'Moths_failures.txt'

# Write examples to my wp userspace?
wp_examples = False
max_examples = 200
success_examples_wp = 'User:MichaelMaggs/Moths'
failure_examples_wp = 'User:MichaelMaggs/Moths_failures'

# Set a minimum wait time between live wp edits. Time in seconds.
# IS THIS NEEDED?
wait_time = 1.0

# Initialise the site
wikipedia = pywikibot.Site('en', 'wikipedia')


# FUNCTIONS

# Check to see if page matches the criteria. Returns (True, '') or (False, reason)
def check_criteria(page, lead_text, required_words, excluded_words, test_regex_tf, test_regex,
                   title_regex_tf, title_regex):
    # We need to match on *everything* specified in the criteria -
    # Returns (True, '') or (False, reason)
    for required in required_words:
        if required not in lead_text:
            # print(page.title() + ' Does not mention ' + required)
            return False, 'Required word missing - ' + required
    for excluded in excluded_words:
        if excluded in lead_text:
            # print(page.title() + ' - mentions ' + excluded)
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
def check_page(page, lead_text, require_infobox, infobox_strings, sole_infobox):
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


# Does a description already exist?
def shortdesc_exists(page):
    global wikipedia
    sections = pywikibot.textlib.extract_sections(page.text, wikipedia)
    text = sections[0]
    if re.search('{{short description', text, re.IGNORECASE):
        return True
    else:
        return False


# Generate the draft sd. Called by shortdesc_stage. Returns (True, description) for good result, or (False, errortext)
# *** For each task, the code here needs to be hand-crafted ***
def shortdesc_generator(page, lead_text):
    global wikipedia
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
def shortdesc_stage(targetcat, max_arts, max_stage, max_examples, required_words, excluded_words,
                    test_regex_tf, test_regex, title_regex_tf, title_regex, require_infobox, infobox_strings,
                    sole_infobox, success_file, failure_file, partial, startpoint, endpoint):
    global wikipedia
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

    # Get pages in the enwp category
    cat = pywikibot.Category(wikipedia, targetcat)

    # Loop over pages
    for page in pagegenerators.CategorizedPageGenerator(cat, recurse=False):

        # If partial is True, skip over initial pages until we reach the startpoint
        if partial and not tripped:
            at_startpoint = startpoint in page.title()
            tripped = at_startpoint
            if not at_startpoint:
                continue

        # Get info related to this page, on enwp and from Wikidata
        lead_text = get_lead(page)
        wikidata_sd = get_wikidata_desc(page)
        print('\nPROCESSING NEW PAGE IN SHORTDESC_STAGE')
        print('lead_text: ', lead_text)

        # Do we want this page? Check against page definition
        result_page = check_page(page, lead_text, require_infobox, infobox_strings, sole_infobox)

        # Should we skip this page? (not recorded in the list of failures)
        if not result_page[0]:
            skip_text = result_page[1]
            print(page.title() + ' - Skipped: ' + skip_text)
            continue

        # We have a page to work with. Check whether it matches or fails the criteria
        result_criteria = check_criteria(page, lead_text, required_words, excluded_words, test_regex_tf, test_regex,
                                         title_regex_tf, title_regex)

        # If the page fails the criteria, note as such and write a new line to failure_str, for staging later

        if not result_criteria[0]:
            errortext = result_criteria[1]
            print(page.title() + ' - FAILED: ' + errortext)
            if count_failure <= max_stage:
                count_failure += 1
                failure_str += page.title() + ' | ' + errortext + ' | ' + wikidata_sd + ' | ' + lead_text + '\n'

            # If needed, also build up failure_examples_str ready to write to userspace
            if wp_examples and (count_failure_examples <= max_examples):
                count_failure_examples += 1
                failure_examples_str += '|-\n'
                failure_examples_str += '| [[' + page.title() + ']] || ' + errortext + ' || ' + wikidata_sd + ' || ' \
                                        + lead_text + '\n'

            count_arts += 1
            if count_arts >= max_arts:
                break

            continue

        # The page matches the criteria, and we now need to work out the new sd
        result_gen = shortdesc_generator(page, lead_text)

        #  Failed to create a usable short description. Treat as if it were a page failure and write to failure_str
        if not result_gen[0]:
            errortext2 = result_gen[1]
            print(page.title() + errortext2)
            if count_failure <= max_stage:
                count_failure += 1
                failure_str += page.title() + ' | ' + errortext2 + ' | ' + wikidata_sd + ' | ' + lead_text + '\n'

            # If needed, also build up failure_examples_str ready to write to userspace
            if wp_examples and (count_failure_examples <= max_examples):
                count_failure_examples += 1
                failure_examples_str += '|-\n'
                failure_examples_str += '| [[' + page.title() + ']] || ' + errortext2 + ' || ' + wikidata_sd + ' || ' \
                                        + lead_text + '\n'

            count_arts += 1
            if count_arts >= max_arts:
                break

            continue

        # We have a good draft description!
        description = result_gen[1]
        print(str(count_arts + 1) + ': ' + page.title() + ' - STAGING NEW SD: ' + description)

        # Build up success_str string ready to save to local file
        if count_success <= max_stage:
            count_success += 1
            success_str += page.title() + ' | ' + description + ' | ' + wikidata_sd + ' | ' + lead_text + '\n'

        #  If needed, also build up success_examples_str string ready to write to userspace
        if wp_examples and (count_success_examples <= max_examples):
            count_success_examples += 1
            success_examples_str += '|-\n'
            success_examples_str += '| [[' + page.title() + ']] || ' + description + ' || ''' + wikidata_sd + ' || ' \
                                    + lead_text + '\n'

        count_arts += 1
        if count_arts >= max_arts:
            break

        # If partial is True, stop when we reach the endpoint
        if partial and tripped:
            at_endpoint = endpoint in page.title()
            if at_endpoint:
                break

    # Finished creating the strings
    # Now stage the successes to success_file
    with open(success_file, 'w') as f1:
        f1.write(success_str)

    # Write examples to my userspace
    if wp_examples:
        page = pywikibot.Page(wikipedia, success_examples_wp)
        header_text = "\n|+\nShortDescBot proposed short descriptions\n!Article\n!Proposed SD\n!(Wikidata " \
                      "SD)\n!Opening words of the lead\n"
        page.text = 'The bot does not use Wikidata\'s short description in any way. It is listed here for reference ' \
                    'only\n{| class="wikitable"' + header_text + success_examples_str + "|}"

        # page.text = '{| class="wikitable"' + success_str + "\n|}"  #MP

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
                      "of the lead\n"
        page.text = 'The bot does not use Wikidata\'s short description in any way. It is listed here for reference ' \
                    'only' \
                    ' \n{| class="wikitable"' + header_text + failure_examples_str + "|}"
        page.save("Save a sample of ShortDescBot failed pages")
        print('Failures are at https://en.wikipedia.org/wiki/' + failure_examples_wp.replace(' ', '_'))

    print('\nThe draft short descriptions are staged in ' + success_file + ', with failures in ' + failure_file)

    # All done!
    return


# Main function for 'edit' mode. Write the descriptions to mainspace, reading in from local success_file
def shortdesc_add(debug, success_file, wait_time):
    global wikipedia
    count = 0

    # Get the list of articles and the draft short descriptions from local file
    with open(success_file) as f:
        data = f.read()
        todo = data.splitlines()

    # Work through them one by one
    for line in todo:
        # Only if we don't have a table header
        if '{|' not in line and '|}' not in line and line.strip() != '':
            values = line.split('|')
            page = pywikibot.Page(wikipedia, values[0].strip())
            print('\n')
            # Check again that page still has no existing description
            if shortdesc_exists(page):
                print(page.title() + ' - NO EDIT MADE: Page now has an existing description')
                continue
            print(values)
            description = values[1].strip()
            test = 'y'
            if debug:
                test = 'n'
                test = input(
                    'Add "' + description + '"" to https://en.wikipedia.org/wiki/' + values[0].strip().replace(
                        ' ', '_') + "? (Type 'y' to apply)")
            if test == 'y':
                count += 1
                page.text = '{{Short description|' + description + '}}\n' + page.text
                page.save('Adding short description "' + description + '"', minor=False)

            time.sleep(wait_time)

    print("\nDONE! Added short descriptions to " + str(count) + " articles ")
    return


# Get the description from Wikidata
def get_wikidata_desc(page):
    global wikipedia
    try:
        wd_item = pywikibot.ItemPage.fromPage(page, wikipedia)
        item_dict = wd_item.get()
        qid = wd_item.title()
    except:
        print('Huh - no page found')
        return ''

    # Get the description from Wikidata to make sure it's empty   WHAT IS THIS ??
    wikidata_description = ''
    try:
        return item_dict['descriptions']['en']
    except:
        return ''


# Get the first sentence or sentences (up to 120 chars) of the lead
def get_lead(page):
    global wikipedia
    parse_debug = False

    sections = pywikibot.textlib.extract_sections(page.text, wikipedia)
    text = sections[0]
    if parse_debug: print("1: ", text)
    text = re.sub(r"{{.*?}}", "", text)
    if parse_debug: print("2: ", text)
    text = re.sub(r"\[\[([^\]\[|]*)\|", "[[", text, re.MULTILINE)
    if parse_debug: print("3: ", text)
    if "}}" in text:
        text = text.split("}}")[-1]
    if parse_debug: print("4: ", text)
    text = re.sub(r"<ref.*?</ref>", "", text, re.MULTILINE)
    if parse_debug: print("5: ", text)
    text = re.sub(r"&nbsp;", " ", text, re.MULTILINE)
    if parse_debug: print("6: ", text)
    text = re.sub(r"[\[\]]+", "", text, re.MULTILINE)
    if parse_debug: print("7: ", text)
    text = re.sub(r"[^A-Za-z0-9,\.;:\- ]+", "", text, re.MULTILINE)
    if parse_debug: print("8: ", text)
    text = text[0:120].strip()
    if parse_debug: print("9: ", text)
    if '.' in text:
        text = text.rpartition('.')[0] + '.'  # Chop out everything after the last full stop, if there is one
        if parse_debug: print("10: ", text)
    return text


# Count the number of infoboxes
def count_infoboxes(page):
    global wikipedia
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


# MAIN CODE

# Run staging code
if mode_flag == 'stage':
    # input('***** Ready to stage. Press return to continue')
    shortdesc_stage(targetcat, max_arts, max_stage, max_examples, required_words, excluded_words,
                    test_regex_tf, test_regex, title_regex_tf, title_regex, require_infobox, infobox_strings,
                    sole_infobox, success_file, failure_file, partial, startpoint, endpoint)

# Run live editing code
if mode_flag == 'edit':
    if debug:
        run_type = 'assisted'
    else:
        run_type = 'automatic'
    input('***** READY TO WRITE LIVE EDITS in ' + run_type + ' mode. Press return to continue')
    shortdesc_add(debug, success_file, wait_time)
