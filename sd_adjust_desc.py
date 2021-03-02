# See sd_run.py for status and copyright release information
from sd_functions import in_category


# Add 'Extinct ...' to description unless that would make it too long
def adjust_desc(page, lead_text, shortdesc, isextinct_autobox):
    extinct_in_lead = ['is a fossil', 'is an extinct']
    extinct_in_cat = ['fossil', 'prehistoric', 'extinctions']

    if len('Extinct ' + shortdesc) > 40:
        return shortdesc

    # Don't bother with more checks if we already have the answer from an Automatictaxobox
    if isextinct_autobox:
        return 'Extinct ' + shortdesc.lower()

    for extinct in extinct_in_lead:
        if extinct in lead_text.lower():
            return 'Extinct ' + shortdesc.lower()
    for extinct in extinct_in_cat:
        if in_category(page, extinct):
            return 'Extinct ' + shortdesc.lower()

    return shortdesc
