# Code for ShortDescBot, task 1 - moths
#
# Michael Maggs, released under the GNU General Public License v3
# Based on code by Mike Peel as at 28 November 2020:
# https://bitbucket.org/mikepeel/wikicode/src/master/shortdesc_run.py and
# https://bitbucket.org/mikepeel/wikicode/src/master/shortdesc_functions.py
# also released under the GNU General Public License v3.
# Latest update 4 December 2020

import re
import time

import dateparser
import pywikibot
from pywikibot import pagegenerators
from pywikibot.data import api

# Mode of operation:
# stage: write to staging file and/or examples to userspace
# edit:  read from staging file and write live edits to namespace
mode_flag = 'stage'

# Category to work on
targetcat = 'Category:Moths of Nepal'

# Define the types of article of interest: base texts for the SDs & the corresponding Regexes
sd_species = 'Species of moth'
trial_species = re.compile('^.*is\sa\s[\w\s]{0,20}moth\s')  # moth species
sd_genus = 'Genus of moths'
trial_genus = re.compile('^.*is\sa\s[\w\s]{0,20}genus\sof\smoths\s')  # genus of moths
# Make nested list to pass to functions
interests_list = [[trial_species, sd_species], [trial_genus, sd_genus]]

# Maximum number of articles to look through
max_arts = 100

# Set to 'True' to run live editing in assisted mode (step though and confirm every amendment in advance)
# Run from normal account, not bot account, if before bot approval
debug = True

# Run through pages in the category, from startpoint to endpoint. Set as '' to process all pages
startpoint = 'Acmeshachia gigantea'
endpoint = 'Alphaea florescens'

# Must the articles require an infobox?
require_infobox = False
infobox_strings = ['infobox']  # Add additional elements for various infobox types
sole_infobox = True  # Skip pages that have more than one infobox

# Stage to file?
stage_to_file = True
max_stage = 10
success_file = 'Moths.txt'
failure_file = 'Moths_failures.txt'

# Write examples to my wp userspace?
wp_examples = True
max_examples = 10
success_examples_wp = 'User:MichaelMaggs/Moths'
failure_examples_wp = 'User:MichaelMaggs/Moths_failures'

# Set a minimum wait time between live wp edits. Time in seconds.
wait_time = 1.0

# Initialise the site
wikipedia = pywikibot.Site('en', 'wikipedia')


# FUNCTIONS

# Function to check against a specific trial criteria that's passed to it. Returns True if OK
def trial_criteria(page, this_regex):
    intro_text = get_lead(page)
    if this_regex(intro_text):
        return True
    return False


# Generate the descriptions. Called by shortdesc_stage
# Returns (True, draft description) for good result, or (False, errortext) for failure or skipped
def shortdesc_generator(page, require_infobox, infobox_strings, sole_infobox, interests_list):
    global wikipedia
    has_infobox = False

    # First, check if the page needs to be skipped (not included in the list of failures)
    # Check for existing short description
    if shortdesc_exists(wikipedia, page):
        print(page.title() + ' - Skipped: already has short description')
        return False, 'Skipped: already has short description'
    # Check for required infobox, and no more than one if specified
    if require_infobox:
        for option in infobox_strings:  # Check through the various strings that identify an infobox
            if option in page.text.lower():
                has_infobox = True
        if not has_infobox:
            print(page.title() + ' - Skipped: does not have infobox')
            return False, 'Skipped: does not have infobox'
        if sole_infobox:
            if count_infoboxes(page) > 1:
                print(page.title() + ' - Skipped: has multiple infoboxes')
                return False, 'Skipped: has multiple infoboxes'

    #  Now check against the trial_regexes. Fail the page if there are multiple or zero matches
    list_of_matches = []
    for item in interests_list:
        trial_result = trial_criteria(page, item[0])  # item[0] passes in the current Regex
        list_of_matches.append(trial_result)
    count = list_of_matches.count(True)
    if count == 0:
        print(page.title() + ' - FAILED: No Regex match')
        return False, 'Failed: No Regex match'
    if count > 1:
        print(page.title() + ' - FAILED: Multiple Regex matches')
        return False, 'Failed: Multiple Regex matches'
    matched_index = list_of_matches.index(True)
    description = interests_list[0][matched_index]  # This is the draft description corresponding to the Regex match
    return True, description


# Function to stage draft descriptions to local file, and optionally write examples to userspace
# Calls shortdesc_generator
def shortdesc_stage(targetcat, max_arts, max_stage, max_examples, startpoint, endpoint, require_infobox,
                    infobox_strings, sole_infobox, interests_list, success_file, failure_file):
    global wikipedia
    # Initialising parameters
    count_arts = 0
    count_success = 0
    count_success_examples = 0
    count_failure = 0
    count_failure_examples = 0
    success_str = ''
    success_examples_str = ''
    failure_str = ''
    failure_examples_str = ''
    if startpoint == '':
        trip = False

    # Link with enwp and find pages in the category
    cat = pywikibot.Category(wikipedia, targetcat)

    # Loop over pages
    for page in pagegenerators.CategorizedPageGenerator(cat, recurse=False):

        # This checks for trip/startpoint/endpoint
        if not trip:
            if startpoint in page.title():
                trip = True
            else:
                continue
        if endpoint != '' and endpoint in page.title():
            break

        # Call shortdesc_generator to get draft description or the errortext for this page
        result = shortdesc_generator(page, require_infobox, infobox_strings, sole_infobox, interests_list)
        good_desc = result[0]

        if good_desc:   #  True if we have a draft description
            description = result[1]
            print(page.title() + ' - STAGING NEW SD: ' + description)

            wikidata_description = get_wikidata_desc(page)
            intro_text = get_lead(page)

            # Using the new description, build up success_str string ready to save to local file
            if count_success <= max_stage:
                count_success += 1
                success_str += page.title() + ' || ' + description + " || " + wikidata_description + " || " + intro_text + "\n"
                print(page.title() + ' - STAGING NEW SD: ' + description)

            #  Build up success_examples_str string ready to write to userspace
            if wp_examples and (count_success_examples <= max_examples):
                count_success_examples += 1
                success_examples_str += '|-\n'
                success_examples_str += '| [[' + page.title() + "]] || " + description + " || " + wikidata_description + " || " + intro_text + "\n"

        else:   #  The page has failed the Regex matches, and no description has been generated
            errortext = result[1]

            # Build up failure_str ready to save to local file
            if count_failure <= max_stage:
                count_failure += 1
                failure_str += page.title() + ' || ' + errortext + " || " + wikidata_description + " || " + intro_text + "\n"
                print(page.title() + ' - FAILED: ' + errortext)

            #  Build up success_examples_str ready to write to userspace
            if wp_examples and (count_failure_examples <= max_examples):
                count_failure_examples += 1
                failure_examples_str += '|-\n'
                failure_examples_str += '| [[' + page.title() + "]] || " + errortext + " || " + wikidata_description + " || " + intro_text + "\n"

        count_arts += 1
        if count_arts >= max_arts:
            break

    # Finished creating the strings. Now stage the successes to success_file
    with open('success_file', 'w') as f1:
        f1.write(success_str)

    # Write examples to my userspace
    if wp_examples:
        page = pywikibot.Page(wikipedia, success_examples_wp)
        header_text = "\n|+\nShortDescBot proposed short descriptions\n!Article\n!Proposed SD\n!(Wikidata SD)\n!Opening words of the lead\n"
        page.text = '{| class="wikitable"' + header_text + success_str + "|}"
        page.save("Saving a sample of ShortDescBot draft short descriptions")
        print('Examples are at https://en.wikipedia.org/wiki/' + success_examples_wp.replace(' ', '_'))

    #  Write the failures to failure_file
    with open('failure_file', 'w') as f2:
        f2.write(failure_str)

    # Write examples of failures to my userspace
        if wp_examples:
        page = pywikibot.Page(wikipedia, failure_examples_wp)
        header_text = "\n|+\nShortDescBot failed pages\n!Article\n!Reason for failure\n!(Wikidata SD)\n!Opening words of the lead\n"
        page.text = '{| class="wikitable"' + header_text + output + "|}"
        page.save("Save a sample of ShortDescBot failed pages")
        print('Failures are at https://en.wikipedia.org/wiki/' + failure_examples_wp.replace(' ', '_'))

    print('\nYour new set of short descriptions is in ' + success_file + ', with failures in ' + failure_file)

    # All done!
    return


# Function to write the descriptions to mainspace, reading in from local success_file
def shortdesc_add(debug, success_file, wait_time):
    global wikipedia
    count = 0

    # Get the list of articles and the draft short descriptions from local file
    with open('success_file') as f:
        data = f.read()
        todo = data.splitlines()

    # Work through them one by one
    for line in todo:
        # print(line)
        # Only if we don't have a table header
        if '{|' not in line and '|}' not in line and line.strip() != '':
            values = line.split('||')
            page = pywikibot.Page(wikipedia, values[0].strip())

            # Check again that page still has no existing description
            if shortdesc_exists(wikipedia, page):
                print(page.title() + ' - NO EDIT MADE: Page now has an existing description')
                continue

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
                page.save('Adding short description ("' + description + '")', minor=False)

            time.sleep(wait_time)

    print("DONE! Added short descriptions to " + str(count) + " articles ")
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


# Get the first sentence(s) (up to 120 chars) of the lead
def get_lead(page):
    global wikipedia
    sections = pywikibot.textlib.extract_sections(page.text, wikipedia)
    text = sections[0]
    text = re.sub(r"{{.*?}}", "", text)
    text = re.sub(r"\[\[([^\]\[|]*)\|", "[[", text, re.MULTILINE)
    if "}}" in text:
        text = text.split("}}")[-1]
    text = re.sub(r"<ref.*?</ref>", "", text, re.MULTILINE)
    text = re.sub("[\[\]]+", "", text, re.MULTILINE)
    text = re.sub(r"[^A-Za-z0-9,\.;:\- ]+", "", text, re.MULTILINE)
    text = text[0:120].strip()
    text = text.rpartition('.')[0] + '.'
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


def shortdesc_exists(wikipedia, page):
    description = ''
    test = get_pageinfo(wikipedia, page)
    for item in test['query']['pages']:
        try:
            description = test['query']['pages'][item]['pageprops']['wikibase-shortdesc']
        except:
            null = 0
    if len(description) >= 0:
        return True
    return False


# MAIN CODE

# Run staging code
if mode_flag == 'edit':
    input('***** Ready to stage. Press return to continue')
    shortdesc_stage(targetcat, max_arts, max_stage, max_examples, startpoint, endpoint, require_infobox,
                    infobox_strings, sole_infobox, interests_list, success_file, failure_file)

# Run live editing code
if mode_flag == 'edit':
    if debug:
        run_type = 'assisted'
    else:
        run_type = 'automatic'
    input('***** READY TO WRITE LIVE EDITS in ' + run_type + ' mode. Press return to continue')
    shortdesc_add(debug, success_file, wait_time)
