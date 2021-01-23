# See sd_run.py for status and copyright release information

# Generate the draft SD. Called by shortdesc_stage. Returns (True, description) for good result, or (False, errortext)
# NOTE: For each task, the code here needs to be hand-crafted

from sd_config import *


def shortdesc_generator(page, lead_text):
    title = page.title()
    matched_type = ''
    mono_list_page = ['[[category:monotypic']
    mono_list_lead = ['monotypic', 'monospecific', ' a single species ', ' the single species',
                      'single-species']  # Only for genus articles
    mono_sd_prefix = 'Single-species '
    extinct_list_page = ['isafossil', 'isanextinct', '{{extinct}}', '|status=ex', '|extinct=y', '|extinct=t',
                         '|type_species=†', 'extinctions]]', '[[category:prehistoric']
    extinct_sd_prefix = 'Extinct '
    regex_code = "(is a |are a |is an |are an |was a |were a |was an |were an )(?:(?! in the ).){,30}"
    # Need to ensure eg that "is an order of fungi in the class Tremellomycetes" maps to 'Order' not Class'
    # So, regex covers:  "is a" + ... maximum of 30 chars not including 'in the' ... + "order"
    # Tempered greedy token - see http://www.rexegg.com/regex-quantifiers.html#tempered_greed
    sdtype_dict = {
        'Genus': regex_code + 'genus',
        'Family': regex_code + 'famil',
        'Superfamily': regex_code + 'superfamil',
        'Tribe': regex_code + 'tribe',
        'Subtribe': regex_code + 'subtribe',
        'Subfamily': regex_code + 'subfamil',
        'Subgenus': regex_code + 'subgenus',
        'Class': regex_code + 'class',
        'Order': regex_code + 'order'
    }

    # Get title length, ignoring brackets; make compressed searchable version of page text
    title_nobra = re.sub(r'\(.+?\)', '', title).strip()
    title_nobra_len = len(title_nobra.split())
    text_compressed = page.text.lower().replace(' ', '')

    # Check if this is a species article
    if title_nobra_len > 1 and ('{speciesbox' in text_compressed or "|species='''''" in text_compressed):
        matched_type = 'Species'
        shortdesc = matched_type + ' of ' + name_singular

    # Check if this is a subspecies article
    elif title_nobra_len > 1 and ('{subspeciesbox' in text_compressed or "|subspecies='''''" in text_compressed):
        matched_type = 'Subspecies'
        shortdesc = matched_type + ' of ' + name_singular

    else:  # Not species or subspecies
        if title_nobra_len > 1:
            return False, "Multi-word title, but possibly not a species or subspecies"
        matched = False

        for sdtype in sdtype_dict:  # Work through the other options. Accept only if exactly one rank matches
            sdregex = sdtype_dict[sdtype]
            if re.search(sdregex, lead_text):
                if matched:
                    return False, "Multiple descriptions possible"
                # print("FOUND MATCH on", sdtype)
                matched_type = sdtype
                matched = True

        # Final chance to save an unmatched Genus article that doesn't mention 'genus' but is in a genera category
        if not matched:
            if "|genus='''''" in text_compressed:
                matched_type = 'Genus'
                print('Last chance genus')
            else:  # No good
                return False, "Can't create description"

        shortdesc = matched_type + ' of ' + name_plural

    # Check for extinction. Add "Extinct " to the start of SD if room to do so
    for extinct in extinct_list_page:  # Parse entire page
        if extinct.lower() in text_compressed and len(extinct_sd_prefix + shortdesc) <= 40:
            shortdesc = extinct_sd_prefix + shortdesc.lower()
            break

    # For monotypic genuses, add "Single-species " to the start of SD if room to do so
    if matched_type == 'Genus':
        for mono in mono_list_page:  # Parse entire page
            if mono.lower() in text_compressed and len(mono_sd_prefix + shortdesc) <= 40:
                shortdesc = mono_sd_prefix + shortdesc.lower()
                return True, shortdesc
        for mono in mono_list_lead:  # Parse the lead only
            if mono.lower() in lead_text.lower() and len(mono_sd_prefix + shortdesc) <= 40:
                shortdesc = mono_sd_prefix + shortdesc.lower()
                return True, shortdesc

    return True, shortdesc
