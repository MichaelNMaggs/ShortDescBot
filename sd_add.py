# See sd_run.py for status and copyright release information


import datetime
import time

from sd_edit_allowed import ok_to_edit
from sd_functions import *


# Main function for 'edit' mode. Write the descriptions to mainspace, reading in from local staging_file
def shortdesc_add():
    ecount = ecount_success = ecount_failure = skip_count = 0
    esuccess_str = efailure_str = ''

    # Check login
    if username not in ('MichaelMaggs', 'ShortDescBot'):
        print('STOPPING - unexpected username: ', username)
        return
    if username != 'ShortDescBot' and not assisted_mode:
        print(f'STOPPING - cannot run bot in automatic mode with Username:{username}')
        return

    # Get the list of articles and the new short descriptions from local staging_file
    try:
        with open('staged.tsv') as sfile:
            data = sfile.read()
            lines = data.splitlines()
    except:
        print("STOPPING - can't open staging file")
        return

    # Work through lines of staging_file, one by one

    for line in lines:
        # Skip line if it's a table header
        if '{|' in line or '|}' in line or line.strip() == '':
            continue

        # Set up for this page, from current line
        values = line.split('\t')
        title = values[1].strip()
        description = values[2].strip()  # This is the new description we want to use
        page = pywikibot.Page(wikipedia, title)

        # Get existing description and type: manual or embedded
        existing_desc, existing_type = existing_shortdesc(page)

        # Check for various things before allowing a page edit
        try:
            if not ok_to_edit(page, title, description, username, existing_desc, existing_type, override_manual,
                              override_embedded, existing_desc_regex, existing_desc_required_words,
                              existing_desc_excluded_words):
                skip_count += 1
                continue   # Go on to next line, ie page to edit
        except AssertionError:
            return  # Unexpected error in page title

        # Get manual confirmation if in assisted mode
        if assisted_mode:
            key_input = confirm_edit(title, existing_desc, existing_type, description)
            if key_input == 's':
                break
            if key_input != 'y':
                continue

        # OK to edit at this point
        ecount += 1

        # Add a new description where none currently exists
        if existing_type is None:
            edit_text = 'Adding [[Wikipedia:Short description|short description]]'
            if username == 'ShortDescBot':
                edit_text = '[[User:ShortDescBot|ShortDescBot]] adding [[Wikipedia:Short description|short ' \
                            'description]]'
            page.text = '{{Short description|' + description + '}}\n' + page.text
            print(str(ecount + 1) + ': ' + title + f' - WRITING NEW SD: ' + description)

            try:
                page.save(edit_text + ' "' + description + '"', minor=False)
            except:
                print(f'UNABLE TO EDIT {title}. Will retry in 1 minute')
                time.sleep(60)
                try:
                    page.save(edit_text + ' "' + description + '"', minor=False)
                except:
                    print(f'STILL UNABLE TO EDIT {title}. Mark as failed')
                    # Build up efailure_str string ready to log to local file
                    efailure_str += title + '\t FAILED: ' + description + '\n'
                    ecount -= 1
                    ecount_failure += 1
                else:  # OK on second attempt
                    # Build up esuccess_str string ready to log to local file
                    esuccess_str += title + '\t' + description + '\n'
                    ecount_success += 1
            else:  # Succeeded on first attempt
                # Build up esuccess_str string ready to log to local file
                esuccess_str += title + '\t' + description + '\n'
                ecount_success += 1

        # Override an existing embedded description
        if existing_type == 'embedded':
            edit_text = 'Overriding [[Wikipedia:Short description|short description]] from infobox with'
            if username == 'ShortDescBot':
                edit_text = '[[User:ShortDescBot|ShortDescBot]] overriding [[Wikipedia:Short description|short ' \
                            'description]] from infobox with'
            page.text = '{{Short description|' + description + '}}\n' + page.text
            print(str(ecount + 1) + ': ' + title + f' - OVERRIDING EMBEDDED SD: ' + description)

            try:
                page.save(edit_text + ' "' + description + '"', minor=False)
            except:
                print(f'UNABLE TO EDIT {title}. Will retry in 1 minute')
                time.sleep(60)
                try:
                    page.save(edit_text + ' "' + description + '"', minor=False)
                except:
                    print(f'STILL UNABLE TO EDIT {title}. Mark as failed')
                    # Build up efailure_str string ready to log to local file
                    efailure_str += title + '\t FAILED: ' + description + '\n'
                    ecount -= 1
                    ecount_failure += 1
                else:  # OK on second attempt
                    # Build up esuccess_str string ready to log to local file
                    esuccess_str += title + '\t' + description + '\n'
                    ecount_success += 1
            else:  # Succeeded on first attempt
                # Build up esuccess_str string ready to log to local file
                esuccess_str += title + '\t' + description + '\n'
                ecount_success += 1

        # Replace/edit a manual short description
        if existing_type == 'manual':
            # Construct a {{Short description}} template we know should exist, then remove it
            sd_constructed = '{{Short description|' + existing_desc + '}}'
            sd_constructed2 = '{{short description|' + existing_desc + '}}'
            if sd_constructed not in page.text and sd_constructed2 not in page.text:
                print(page.title() + ' - ERROR: Cannot locate SD template, though it should exist')
                continue

            page.text = page.text.replace(sd_constructed + '\n', '')
            page.text = page.text.replace(sd_constructed2 + '\n', '')

            edit_text = 'Changing [[Wikipedia:Short description|short description]] from'
            if username == 'ShortDescBot':
                edit_text = '[[User:ShortDescBot|ShortDescBot]] changing [[Wikipedia:Short description|short ' \
                            'description]] from'
            page.text = '{{Short description|' + description + '}}\n' + page.text
            print(str(ecount + 1) + ': ' + title + f' - CHANGING MANUAL SD: ' + description)

            try:
                page.save(edit_text + ' "' + existing_desc + '" to "' + description + '"', minor=False)
            except:
                print(f'UNABLE TO EDIT {title}. Will retry in 1 minute')
                time.sleep(60)
                try:
                    page.save(edit_text + ' "' + description + '"', minor=False)
                except:
                    print(f'STILL UNABLE TO EDIT {title}. Mark as failed')
                    # Build up efailure_str string ready to log to local file
                    efailure_str += title + '\t FAILED: ' + description + '\n'
                    ecount -= 1
                    ecount_failure += 1
                else:  # OK on second attempt
                    # Build up esuccess_str string ready to log to local file
                    esuccess_str += title + '\t' + description + '\n'
                    ecount_success += 1
            else:  # Succeeded on first attempt
                # Build up esuccess_str string ready to log to local file
                esuccess_str += title + '\t' + description + '\n'
                ecount_success += 1

        time.sleep(wait_time)

    # Now write to one-off edit logging files
    print('\n')
    now = datetime.datetime.now()
    dt_extension = f'{now:%Y-%m-%d (%H %M).tsv}'
    name_start = 'log_success '
    if username == 'MichaelMaggs':
        name_start = 'MNM non-bot log_success '  # Distinguish assisted (non-bot) edits with my username
    try:
        if esuccess_str:
            log_success_file = name_start +  f'({ecount_success}) {dt_extension}'
            with open(log_success_file, 'w') as ls_file:
                ls_file.write(esuccess_str)
            print('Successes logged in ' + log_success_file)
        if efailure_str:
            log_fail_file = 'log_fail ' + f'({ecount_failure}) {dt_extension}'
            with open(log_fail_file, 'w') as lf_file:
                lf_file.write(efailure_str)
            print('Failures logged in ' + log_fail_file)
    except:
        print(f'\nSTOPPING: Unable to create or write to logging files')
        return

    try:
        etargets = ecount_failure + ecount_success
        esucc_pc = round(100 * ecount_success / etargets, 2)
        efail_pc = round(100 * ecount_failure / etargets, 2)
        print(
            f'EDIT TARGETS: {etargets}  SUCCESS: {ecount_success} ({esucc_pc}%)  FAILURE: {ecount_failure} ('
            f'{efail_pc}%)')
        print(f'SKIPPED: {skip_count} articles')
    except:
        print('\nNo edit target articles found.')

    return
