# See sd_run.py for status and copyright release information

from pywikibot import pagegenerators

from sd_functions import *
from sd_generator import *


# Main function for 'stage' mode
# Calls check_page, check_criteria and shortdesc_generator
def shortdesc_stage():
    count_arts = count_success = count_success_examples = count_failure = 0
    success_str = success_examples_str = failure_str = ''
    tripped = False

    # Set up pages as iterable, from cat or from Petscan file. Each item in pages must be created as a Pywikibot object
    if petscan_tf:  # Import a file of Petscan results
        pages = []
        with open(petscan_file) as f:
            data = f.read()
            todo = data.splitlines()
        for line in todo:
            values = line.split('\t')
            if values[0] == 'number':  # Ignore any header line
                continue
            title = values[0]
            page = pywikibot.Page(wikipedia, title)
            pages.append(page)

    else:  # Use articles in the Wikipedia category
        cat = pywikibot.Category(wikipedia, targetcat)
        pages = pagegenerators.CategorizedPageGenerator(cat, recurse=recurse_cats, namespaces=[0])

    # Main loop
    for page in pages:
        lead_text = get_lead(page)

        # If partial is True, skip over initial pages until we reach the startpoint
        if partial and not tripped:
            at_startpoint = startpoint in page.title()
            tripped = at_startpoint
            if not at_startpoint:
                continue

        if verbose_stage:
            print('\nCHECKING PAGE IN SHORTDESC_STAGE - ', page.title())

        # Do we want this page? Check against page definition
        result_page, skip_text = check_page(page)

        # Should we skip this page? (not recorded in the list of failures)
        if not result_page:
            print(page.title() + ' - Skipped: ' + skip_text)
            continue

        # OK, now process this page
        count_arts += 1

        # If we have not been able to extract a lead, write a new line to failure_str, for staging later
        if lead_text is None:
            print(str(count_arts) + ': ' + page.title() + ' - FAILED: Lead could not be extracted')
            errortext = 'Lead could not be extracted'
            failure_str += page.title() + ' | ' + errortext + ' | ' + wikidata_sd + ' | ' + '[None]' + '\n'
            count_failure += 1
            if stop_now(max_arts, count_arts):
                break
            continue

        # We have a page to work with. Check against the criteria and get Wikidata SD
        result_criteria, errortext = check_criteria(page, lead_text)
        wikidata_sd = get_wikidata_desc(page)

        # If the page fails, write a new line to failure_str, for staging later
        if not result_criteria:
            print(str(count_arts) + ': ' + page.title() + ' - FAILED: ' + errortext)
            failure_str += page.title() + '\t' + errortext + '\t' + wikidata_sd + '\t' + lead_text + '\n'
            count_failure += 1
            if stop_now(max_arts, count_arts):
                break
            continue

        # The page matches, so we now need to get the new short description
        result_gen, result_gen_txt = shortdesc_generator(page, lead_text)
        #  If no usable short description, treat as a page failure and write to failure_st
        if not result_gen:
            print(str(count_arts) + ': ' + page.title() + ' - FAILED: ' + result_gen_txt)
            failure_str += page.title() + '\t' + result_gen_txt + '\t' + wikidata_sd + '\t' + lead_text + '\n'
            count_failure += 1
            if stop_now(max_arts, count_arts):
                break
            continue

        # We have a good draft description!
        count_success += 1
        description = result_gen_txt
        print(str(count_arts) + ': ' + page.title() + f' - STAGING NEW SD {count_success}: ' + description)

        # Build up success_str string ready to save to local file
        success_str += page.title() + '\t' + description + '\t' + wikidata_sd + '\t' + lead_text + '\n'
        #  If needed, also build up success_examples_str string ready to write to userspace
        if write_wp_examples and count_success_examples <= max_examples:
            count_success_examples += 1
            success_examples_str += '|-\n'
            success_examples_str += '| [[' + page.title() + ']] || ' + description + ' || ''' + wikidata_sd + ' || ' \
                                    + lead_text + '\n'

        if stop_now(max_arts, count_arts) or stop_now(max_stage, count_success):
            break
        if partial and tripped:  # If partial is True, stop when we reach the endpoint
            at_endpoint = endpoint in page.title()
            if at_endpoint:
                break

    # Finished creating the strings. Now stage the successes to success_file
    try:
        with open(success_file, 'w') as f1:
            f1.write(success_str)
    except:
        print(f'\nSTOPPING: Unable to open {success_file}')
        return

    # Write examples to my userspace, if requested
    if write_wp_examples:
        try:
            page = pywikibot.Page(wikipedia, wp_examples_page)
            header_text = "\n|+\nShortDescBot proposed short descriptions\n!Article\n!Proposed SD\n!(Wikidata " \
                          "SD)\n!Opening words of the lead\n"
            page.text = 'The bot does not use Wikidata\'s short description in any way. It is listed here for ' \
                        'reference only\n{| class="wikitable"' + header_text + success_examples_str + "|}"
            page.save("Saving a sample of ShortDescBot draft short descriptions")
        except:
            print(f'\nWARNING: Unable to write examples to {wp_examples_page}')

    #  Write the failures to failure_file
    try:
        with open(failure_file, 'w') as f2:
            f2.write(failure_str)
    except:
        print(f'\nSTOPPING: Unable to open {failure_file}')
        return

    try:
        targets = count_failure + count_success
        succ_pc = round(100 * count_success / targets, 2)
        fail_pc = round(100 * count_failure / targets, 2)
        print(f'\nThe draft short descriptions are staged in {success_file}, with failures in {failure_file}')
        if write_wp_examples:
            print('Examples are at https://en.wikipedia.org/wiki/' + wp_examples_page.replace(' ', '_'))
        print(f'\nTARGETS: {targets}  SUCCESS: {count_success} ({succ_pc}%)  FAILURE: {count_failure} ({fail_pc}%)')
    except:
        print('\nNo target articles found.')
    return

