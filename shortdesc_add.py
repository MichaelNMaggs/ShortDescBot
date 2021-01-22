# See sd_run.py for status and copyright release information

# Main function for 'edit' mode. Write the descriptions to mainspace, reading in from local success_file

import time

from sd_functions import *


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
    try:
        with open(success_file) as f:
            data = f.read()
            todo = data.splitlines()
    except:
        print('STOPPING - can\'t open input file')
        return

    # Work through them one by one
    for line in todo:
        values = line.split('\t')
        page = pywikibot.Page(wikipedia, values[0].strip())
        if not page.exists():
            print(page.title() + ' -  PAGE DOES NOT EXIST')
            return
        description = values[1].strip()

        # Skip line if it's a table header
        if '{|' in line or '|}' in line or line.strip() == '':
            continue
        # Check for Bots template exclusion
        if not allow_bots(page.text, username):
            print(page.title() + ' - NO EDIT MADE: Bot is excluded via the Bots template')
            continue
        # Check again that page still has no short description
        # **** NEED TO ALTER THIS TO ALLOW EDITS OF SELECTED EXISTING DESCRIPTIONS ****
        if shortdesc_exists(page):
            print(page.title() + ' - NO EDIT MADE: Page now has a description')
            continue

        do_this_page = True
        if debug:  # Require a 'y' input to do this page if in debug mode
            key_input = input(
                'Add "' + description + '" to https://en.wikipedia.org/wiki/' + values[0].strip().replace(
                    ' ', '_') + "? (Type 'y' to apply) ")
            if key_input != 'y':
                do_this_page = False

        if do_this_page:
            print(str(count + 1) + ': ' + page.title() + f' - WRITING NEW SD {str(count)}: ' + description)
            page.text = '{{Short description|' + description + '}}\n' + page.text
            try:
                page.save(edit_text + ' "' + description + '"', minor=False)
                count += 1
            except:
                print(f"UNABLE TO EDIT {page.title()}. Will retry in 1 minute")
                count -= 1
                time.sleep(60)
                try:
                    page.save(edit_text + ' "' + description + '"', minor=False)
                    count += 1
                except:
                    print(f"STILL UNABLE TO EDIT {page.title()}. Skipping this page")
                    count -= 1

        time.sleep(wait_time)

    print(f"\nDONE! Added short descriptions to {str(count)} articles ")
    return
