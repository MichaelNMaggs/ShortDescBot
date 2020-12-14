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

# Set to 'True' to run editing in assisted mode (step though and confirm every amendment in advance)
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
local_file = 'Moths.txt'
local_file_failures = 'Moths_failures.txt'

# Write examples to my wp userspace?
wp_examples = True
max_summaries = 10
wp_examples_page = 'User:MichaelMaggs/Moths'
wp_examples_failures = 'User:MichaelMaggs/Moths_failures'

# Set a minimum wait time between live wp edits. Time in seconds.
wait_time = 1.0

# Dates not used for this task - leave as False
add_birth_date = False
add_death_date = False

# Initialise the site
wikipedia = pywikibot.Site('en', 'wikipedia')


# FUNCTIONS

# Function to check against a specific trial criteria that's passed to it. Returns True if OK
def trial_criteria(page, this_regex):
    intro_sentence = get_lead(page)
    if this_regex(intro_sentence):
        return True
    return False


# Generate the descriptions. Called by shortdesc_stage
# Returns (True, draft description) for good result, or (False, errortext) for failure or skipped
def shortdesc_generator(page, require_infobox, infobox_strings,
                        sole_infobox, interests_list, add_birth_date, add_death_date):
    global wikipedia
    description = ''
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

    #  Now check the page against the trial_regexes and build up the appropriate SD: species, then genus ...
    #  Fail the page if there are multiple or zero Regex matches
    for item in interests_list:
        list_of_matches = []
        trial_result = trial_criteria(page, item[0])  # item[0] passes in the current Regex
        list_of_matches.append(trial_result)

    count = list_of_matches.count(True)
    if count == 0:
        print(page.title() + ' - FAILED: No Regex match')
        return False, 'Failed: No Regex match'
    if count > 1:
        print(page.title() + ' - FAILED: Multiple Regex matches')
        return False, 'Failed: Multiple Regex matches'

    # Add dates to the SD if needed. MP's code, not used for this task
    if not (add_birth_date or add_death_date):  # Only if we need to add a date
        birthdate = calculateBirthDateFull(page=page).strip()
        deathdate = calculateDeathDateFull(page=page).strip()
    if birthdate != '' and deathdate != '' and add_birth_date and add_death_date:
        description += ' (' + str(birthdate[0:5]).replace('-', '').strip() + "–" + str(deathdate[0:4]) + ')'
    elif birthdate != '' and add_birth_date:
        description += ' (' + str(birthdate[0:5]).replace('-', '').strip() + '–)'
    elif deathdate != '' and add_death_date:
        description += ' (–' + str(deathdate[0:5]).replace('-', '').strip() + ')'

    return True, description


# Function to generate and stage draft descriptions to local file, and optionally write summaries to userspace
# Calls shortdesc_generator
def shortdesc_stage(targetcat, max_arts, max_stage, max_summaries, debug, startpoint, endpoint, require_infobox,
                    infobox_strings,
                    sole_infobox, description, add_birth_date, add_death_date, interests_list,
                    local_file, local_file_failures):
    global wikipedia
    # Initialising parameters
    count_arts = 0
    count_staged = 0
    count_summaries = 0
    if startpoint == '':
        trip = False
    output = ''

    # Linking with enwp and finding related pages
    cat = pywikibot.Category(wikipedia, targetcat)

    # Loop over all related pages
    for page in pagegenerators.CategorizedPageGenerator(cat, recurse=False):

        # This checks for trip/startpoint/endpoint
        if not trip:
            if startpoint in page.title():
                trip = True
            else:
                continue
        if endpoint != '' and endpoint in page.title():
            break

        # Call shortdesc_generator to get best description for this page
        description = shortdesc_generator(page, require_infobox, infobox_strings,
                                          sole_infobox, interests_list, add_birth_date, add_death_date)

        if description[0]:
            wikidata_description = get_wikidata_desc(page)
            intro_sentence = get_lead(page)

            # We have a new description; build up output strings ready to save to local file and/or write to userspace

            if count_staged <= max_stage:
                count_staged += 1
                output += page.title() + ' || ' + description + " || " + wikidata_description + " || " + intro_sentence + "\n"
                print(page.title() + ' - NEW SHORT DESCRIPTION')

            if wp_examples and (count_examples <= max_summaries):
                count_staged += 1
                output += '|-\n'
                output += '| [[' + page.title() + "]] || " + description + " || " + wikidata_description + " || " + intro_sentence + "\n"

        count_arts += 1
        if count_arts > max_arts:
            break

    # Finished generating the new descriptions: now stage to file and write optional examples to userspace
    with open('local_file', 'w') as f:
        f.write(output)

    print('\nYour new set of short descriptions is in ' + local_file + ' with failures in ' + local_file_failures)

    if wp_examples:
        page = pywikibot.Page(wikipedia, wp_examples_page)
        header_text = "\n|+\nShortDescBot proposed short descriptions\n!Article\n!Proposed SD\n!(Wikidata SD)\n!Opening words of the lead\n"
        page.text = '{| class="wikitable"' + header_text + output + "|}"
        page.save("Save a sample of short descriptions to userspace")
        print('Summaries are at https://en.wikipedia.org/wiki/' + wp_examples_page.replace(' ', '_'))

    # All done!
    return


# Function to write the descriptions to mainspace, reading in from local staging file
def shortdesc_add(debug, local_file, wait_time):
    global wikipedia
    # Setup
    count = 0
    count2 = 0

    # Get the list of articles and the draft short descriptions from local file
    with open('local_file') as f:
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

            new_description = values[1].strip()
            test = 'y'
            if debug:
                test = 'n'
                test = input(
                    'Add "' + new_description + '"" to https://en.wikipedia.org/wiki/' + values[0].strip().replace(
                        ' ', '_') + "? (Type 'y' to apply)")
            if test == 'y':
                count += 1
                page.text = '{{Short description|' + new_description + '}}\n' + page.text
                page.save('Adding short description ("' + new_description + '")', minor=False)

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


# Calculate birth date based on common syntaxes present in biographies
# MP's code. Not used for this task!
def calculateBirthDateFull(page=''):
    if not page:
        return ''
    m = re.findall(r'\{\{(?:B|b)irth (?:D|d)ate and age\s*\|(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)',
                   page.text.replace('|df=yes', '').replace('|df=y', '').replace('|mf=yes', '').replace('|mf=y', ''))
    if m:
        return str(m[0][0]) + '-' + str(m[0][1]) + '-' + str(m[0][2])
    m = re.findall(r'\{\{(?:B|b)irth date\|(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)',
                   page.text.replace('|df=yes', '').replace('|df=y', '').replace(',', '').replace('[', '').replace(']',
                                                                                                                   ''))
    if m:
        try:
            temp = dateparser.parse(str(m[0][0]) + ' ' + str(m[0][1]) + ' ' + str(m[0][2]))
            return str(temp.year) + '-' + str(temp.month) + '-' + str(temp.day)
        except:
            m = False
    if m:
        return str(m[0][0]) + '-' + str(m[0][1]) + '-' + str(m[0][2])
    m = re.findall(r'\|\s*(?:B|b)irth(?:_| )date\s*=\s*(\w+)\s*(\w+)\s*(\w+)',
                   page.text.replace('|df=yes', '').replace('|df=y', '').replace(',', '').replace('[', '').replace(']',
                                                                                                                   ''))
    if m:
        if (len(m[0][0]) + len(m[0][1]) + len(m[0][2]) > 5) and m[0][2].isnumeric():
            try:
                temp = dateparser.parse(str(m[0][0]) + ' ' + str(m[0][1]) + ' ' + str(m[0][2]))
                return str(temp.year) + '-' + str(temp.month) + '-' + str(temp.day)
            except:
                m = False
    m = re.findall(r'(?im)\[\[\s*Category\s*:\s*(\d+)s births\s*[\|\]]', page.text)
    if m:
        return str(m[0]) + 's'
    m = re.findall(r'(?im)\[\[\s*Category\s*:\s*(\d+) births\s*[\|\]]', page.text)
    if m:
        return m[0]
    return ''


# This calculates the death date based on common syntaxes present in biographies
# MP's code. Not used for this task!
def calculateDeathDateFull(page=''):
    if not page:
        return ''
    m = re.findall(r'\{\{(?:D|d)da\|(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)',
                   page.text.replace('|df=yes', '').replace('|df=y', '').replace('|mf=yes', '').replace('|mf=y', ''))
    if m:
        return str(m[0][0]) + '-' + str(m[0][1]) + '-' + str(m[0][2])
    m = re.findall(r'\{\{(?:D|d)eath date and age\|(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)',
                   page.text.replace('|df=yes', '').replace('|df=y', '').replace('|mf=yes', '').replace('|mf=y', ''))
    if m:
        return str(m[0][0]) + '-' + str(m[0][1]) + '-' + str(m[0][2])
    m = re.findall(r'\{\{(?:D|d)eath year and age\|(\d+)',
                   page.text.replace('|df=yes', '').replace('|df=y', '').replace(',', '').replace('[', '').replace(']',
                                                                                                                   ''))
    if m:
        return str(m[0])
    m = re.findall(r'\{\{(?:D|d)eath date\|(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)',
                   page.text.replace('|df=yes', '').replace('|df=y', '').replace(',', '').replace('[', '').replace(']',
                                                                                                                   ''))
    if m:
        if (len(m[0][0]) + len(m[0][1]) + len(m[0][2]) > 5) and m[0][2].isnumeric():
            try:
                temp = dateparser.parse(str(m[0][0]) + ' ' + str(m[0][1]) + ' ' + str(m[0][2]))
                return str(temp.year) + '-' + str(temp.month) + '-' + str(temp.day)
            except:
                m = False
    m = re.findall(r'\|\s*(?:D|d)eath(?:_| )date\s*=\s*(\w+)\s*(\w+)\s*(\w+)',
                   page.text.replace('|df=yes', '').replace('|df=y', '').replace(',', '').replace('[', '').replace(']',
                                                                                                                   ''))
    if m:
        if (len(m[0][0]) + len(m[0][1]) + len(m[0][2]) > 5) and m[0][2].isnumeric():
            try:
                temp = dateparser.parse(str(m[0][0]) + ' ' + str(m[0][1]) + ' ' + str(m[0][2]))
                return str(temp.year) + '-' + str(temp.month) + '-' + str(temp.day)
            except:
                m = False
    m = re.findall(r'(?im)\[\[\s*Category\s*:\s*(\d+) deaths\s*[\|\]]', page.text)
    if m:
        return m[0]
    return ''


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
    shortdesc_stage(targetcat, max_arts, max_stage, max_summaries, debug, startpoint, endpoint, require_infobox,
                    infobox_strings,
                    sole_infobox, description, add_birth_date, add_death_date, interests_list,
                    wp_examples_page, wp_examples_failures, local_file, local_file_failures)

# Run live editing code
if mode_flag == 'edit':
    if debug:
        run_type = 'assisted'
    else:
        run_type = 'automatic'
    input('***** READY TO WRITE LIVE EDITS in ' + run_type + ' mode. Press return to continue')
    shortdesc_add(debug, local_file, wait_time)
