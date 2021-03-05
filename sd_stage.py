# See sd_run.py for status and copyright release information

import datetime

from pywikibot import pagegenerators

from sd_functions import *
from sd_generator import shortdesc_generator
from sd_get_lead import get_lead


# Main function for 'stage' mode
# Calls check_page, check_criteria and shortdesc_generator
def shortdesc_stage():
    count_arts = count_success = count_success_examples = count_failure = 0
    staging_str = success_examples_str = ''
    tripped = False

    # Set up pages as iterable, from cat or from Petscan file. Each item in pages must be created as a Pywikibot object
    if use_basefile:  # Import a file of Petscan results
        pages = []
        with open(base_file) as f:
            data = f.read()
            todo = data.splitlines()
        for line in todo:
            values = line.split('\t')
            if values[0] == 'number':  # Ignore any header line
                continue
            title = values[1]  # Column 0 is a sequence number
            page = pywikibot.Page(wikipedia, title)
            pages.append(page)

    else:  # Use articles in the Wikipedia category
        cat = pywikibot.Category(wikipedia, targetcat)
        pages = pagegenerators.CategorizedPageGenerator(cat, recurse=recurse_cats, namespaces=[0])

    # Main loop
    for page in pages:
        lead_text = get_lead(page)
        title = clean_title(page.title())

        # If partial is True, skip over initial pages until we reach the startpoint
        if partial and not tripped:
            at_startpoint = startpoint in title
            tripped = at_startpoint
            if not at_startpoint:
                continue

        if verbose_stage:
            print('\nCHECKING PAGE  - ', title)

        # Do we want this page? Check against page definition
        result_page, skip_text = check_page(page)
        if not result_page:   # Should we skip this page? (not recorded in the list of failures)
            print(title + ' - Skipped: ' + skip_text)
            continue

        # OK, now process this page
        count_arts += 1

        # If we have not been able to extract a lead, write failure line to staging_str
        if lead_text is None:
            print(str(count_arts) + ': ' + title + ' - FAILED: Could not extract lead')
            errortext = 'Could not extract lead'
            count_failure += 1
            staging_str += str(
                count_arts) + '\t' + title + '\t' + errortext + '\t' + wikidata_sd + '\t' + '[None]' + '\n'
            if stop_now(max_arts, count_arts):
                break
            continue

        # We have a page to work with. Check against the criteria and get Wikidata SD (for reference only)
        result_criteria, errortext = check_criteria(page, lead_text)
        wikidata_sd = get_wikidata_desc(page)

        # If the page fails, write failure line to staging_str
        if not result_criteria:
            print(str(count_arts) + ': ' + title + ' - FAILED: ' + errortext)
            count_failure += 1
            staging_str += str(
                count_arts) + '\t' + title + '\t' + errortext + '\t' + wikidata_sd + '\t' + lead_text + '\n'
            if stop_now(max_arts, count_arts):
                break
            continue

        # The page matches - work out a new short description
        result_gen, description = shortdesc_generator(page, lead_text)
        if not result_gen:  #  If nothing usable, write failure line to staging_str
            print(str(count_arts) + ': ' + title + ' - FAILED: ' + description)
            count_failure += 1
            staging_str += str(
                count_arts) + '\t' + title + '\t' + description + '\t' + wikidata_sd + '\t' + lead_text \
                           + '\n'
            if stop_now(max_arts, count_arts):
                break
            continue

        # We have a good draft description!
        count_success += 1
        print(str(count_arts) + ': ' + title + f' - STAGING NEW SD {count_success}: ' + description)

        # Add to staging_str
        staging_str += str(
            count_arts) + '\t' + title + '\t' + description + '\t' + wikidata_sd + '\t' + lead_text + '\n'
        #  If needed, also build up success_examples_str string ready to write to userspace
        if write_wp_examples and count_success_examples <= max_examples:
            count_success_examples += 1
            success_examples_str += '|-\n'
            success_examples_str += '| [[' + title + ']] || ' + description + ' || ''' + wikidata_sd + ' || ' \
                                    + lead_text + '\n'

        if stop_now(max_arts, count_arts) or stop_now(max_stage, count_success):
            break
        if partial and tripped:  # If partial is True, stop when we reach the endpoint
            at_endpoint = endpoint in title
            if at_endpoint:
                break

    # Finished creating staging_str. Now stage to staged_output
    if staging_str:
        try:
            now = datetime.datetime.now()
            dt_extension = f'{now:%Y-%m-%d (%H %M)}'
            staged_output = staging_file.split('.')[0] + f' ({count_success} of {count_arts}) ' + dt_extension + '.tsv'
            with open(staged_output, 'w') as f1:
                f1.write(staging_str)
        except:
            print(f'\nSTOPPING: Unable to open {staged_output}')
            return

    # Write examples to my userspace, if requested
    if write_wp_examples and success_examples_str:
        try:
            page = pywikibot.Page(wikipedia, wp_examples_page)
            header_text = "\n|+\nShortDescBot proposed short descriptions\n!Article\n!Proposed SD\n!(Wikidata " \
                          "SD)\n!Opening words of the lead\n"
            page.text = 'The bot does not use Wikidata\'s short description in any way. It is listed here for ' \
                        'reference only\n{| class="wikitable"' + header_text + success_examples_str + "|}"
            page.save("Saving a sample of ShortDescBot draft short descriptions")
        except:
            print(f'\nWARNING: Unable to write examples to {wp_examples_page}')

    try:
        targets = count_failure + count_success
        succ_pc = round(100 * count_success / targets, 2)
        fail_pc = round(100 * count_failure / targets, 2)
        print(f'\nDrafts are staged in {staged_output}')
        if write_wp_examples:
            print('Examples are at https://en.wikipedia.org/wiki/' + wp_examples_page.replace(' ', '_'))
        print(f'\nTARGETS: {targets}  SUCCESS: {count_success} ({succ_pc}%)  FAILURE: {count_failure} ({fail_pc}%)')
    except:
        print('\nNo target articles found')
    return
