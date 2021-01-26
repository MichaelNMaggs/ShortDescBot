# See sd_run.py for status and copyright release information

# Main function for 'edit' mode. Write the descriptions to mainspace, reading in from local success_file

import time

from sd_functions import *


def shortdesc_add():
    # Check login
    if username not in ('MichaelMaggs', 'ShortDescBot'):
        print('STOPPING - unexpected username: ', username)
        return
    if username != 'ShortDescBot' and not assisted_mode:
        print(f'STOPPING - cannot run bot in automatic mode with Username:{username}')
        return

    # Get the list of articles and the new short descriptions from local success_file
    try:
        with open(success_file) as f:
            data = f.read()
            todo = data.splitlines()
    except:
        print("STOPPING - can't open staging file")
        return

    # Work through them one by one
    count = 0
    for line in todo:
        # Skip line if it's a table header
        if '{|' in line or '|}' in line or line.strip() == '':
            continue

        # Set up for this page, from current line of success_file
        values = line.split('\t')
        title = values[0].strip()
        description = values[1].strip()  # This is the new description we want to use
        page = pywikibot.Page(wikipedia, title)

        # Get existing description and type: manual or embedded
        existing = existing_shortdesc(page)
        existing_desc = existing[0]
        existing_type = existing[1]

        # Check for various things before allowing a page edit
        if not page.exists():
            print(page.title() + ' -   NO EDIT MADE: Page does not exist')
            return
        if page.text == '':
            print(page.title() + ' - NO EDIT MADE: Page has been blanked')
            continue
        if not allow_bots(page.text, username):
            print(page.title() + ' - NO EDIT MADE: Bot is excluded via the Bots template')
            continue
        if description == existing_desc:
            print(page.title() + f' - NO EDIT MADE: No change to "{description}"')
            continue

        # Don't edit if not allowed to change an existing description
        if not override_manual and existing_type == 'manual':
            print(page.title() + ' - NO EDIT MADE: Page now has a manual description')
            continue
        if not override_embedded and existing_type == 'embedded':
            print(page.title() + ' - NO EDIT MADE: Page now has an embedded description')
            continue

        # Get manual confirmation if in assisted mode
        if assisted_mode and confirm_edit(title, existing_desc, existing_type, description) != 'y':
            continue

        # OK to edit at this point

        # Add a new description where none currently exists
        if existing_type is None:
            edit_text = 'Adding [[Wikipedia:Short description|short description]]'
            if username == 'ShortDescBot':
                edit_text = '[[User:ShortDescBot|ShortDescBot]] adding [[Wikipedia:Short description|short ' \
                            'description]]'
            page.text = '{{Short description|' + description + '}}\n' + page.text
            print(str(count + 1) + ': ' + page.title() + f' - WRITING NEW SD: ' + description)
            try:
                page.save(edit_text + ' "' + description + '"', minor=False)
                count += 1
            except:
                print(f'UNABLE TO EDIT {page.title()}. Will retry in 1 minute')
                count -= 1
                time.sleep(60)
                try:
                    page.save(edit_text + ' "' + description + '"', minor=False)
                    count += 1
                except:
                    print(f'STILL UNABLE TO EDIT {page.title()}. Skipping this page')
                    count -= 1

        # Page has an existing description

        # Override an existing embedded description
        if existing_type == 'embedded':
            edit_text = 'Overriding [[Wikipedia:Short description|short description]] from infobox'
            if username == 'ShortDescBot':
                edit_text = '[[User:ShortDescBot|ShortDescBot]] overriding [[Wikipedia:Short description|short ' \
                            'description]] from infobox'
            page.text = '{{Short description|' + description + '}}\n' + page.text
            print(str(count + 1) + ': ' + page.title() + f' - OVERRIDING EMBEDDED SD: ' + description)
            try:
                page.save(edit_text + ' "' + description + '"', minor=False)
                count += 1
            except:
                print(f'UNABLE TO EDIT {page.title()}. Will retry in 1 minute')
                count -= 1
                time.sleep(60)
                try:
                    page.save(edit_text + ' "' + description + '"', minor=False)
                    count += 1
                except:
                    print(f'STILL UNABLE TO EDIT {page.title()}. Skipping this page')
                    count -= 1

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
            print(str(count + 1) + ': ' + page.title() + f' - CHANGING MANUAL SD: ' + description)
            try:
                page.save(edit_text + ' "' + existing_desc + '" to "' + description + '"', minor=False)
                count += 1
            except:
                print(f'UNABLE TO EDIT {page.title()}. Will retry in 1 minute')
                count -= 1
                time.sleep(60)
                try:
                    page.save(edit_text + ' "' + description + '"', minor=False)
                    count += 1
                except:
                    print(f'STILL UNABLE TO EDIT {page.title()}. Skipping this page')
                    count -= 1

        time.sleep(wait_time)

    print(f'\nDONE! Added short descriptions to {str(count)} articles')
    return
