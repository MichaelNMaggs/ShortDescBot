# See sd_run.py for status and copyright release information

from sd_functions import allow_bots


# Check for various things before allowing a page edit
def ok_to_edit(page, title, description, username, existing_desc, existing_type, override_manual, override_embedded,
               existing_desc_regex):
    if not override_manual and existing_type == 'manual':  # Don't edit if not allowed to change an existing desc
        print(title + ' - NO EDIT MADE: Page now has a manual description')
        return False
    if not override_embedded and existing_type == 'embedded':
        print(title + ' - NO EDIT MADE: Page now has an embedded description')
        return False
    override = (override_manual and existing_type == 'manual') or (override_embedded and existing_type == 'embedded')
    if override:
        result = existing_desc_regex.match(existing_desc)  # Returns object if a match, or None
        if result is None:
            print(title + ' - NO EDIT MADE: Existing description does not match regex')
            return False
    if '#REDIRECT' in page.text.upper():
        print(title + ' - NO EDIT MADE: Page has been converted to a redirect')
        return False
    if not page.exists():
        print(title + ' - NO EDIT MADE: Page does not exist')
        return False
    if not page.text:
        print(title + ' - NO EDIT MADE: Page blanked or a blank page has been served')
        return False
    if description == existing_desc:
        print(title + f' - NO EDIT MADE: No change to "{description}"')
        return False
    if '*' in description:
        print(title + ' - NO EDIT MADE: Description starts with "*"')  # Indicates a page that previously failed staging
        return False
    if '#REDIRECT' in page.text.upper():
        print(title + ' - NO EDIT MADE: Page has been converted to a redirect')
    if not allow_bots(page.text, username):
        print(title + ' - NO EDIT MADE: Bot is excluded by the Bots template')
        return False
    if title != page.title():  # Unexpected error
        print(title + f' - ERROR: page.title is "{page.title()}", but title from file is "{title}"')
        raise AssertionError
        return False

    return True
