# See sd_run.py for status and copyright release information
import re
import pywikibot

from sd_functions import find_between, in_category

# Get rank from categories
def rank_from_category(page):
    match_cat_dict = {
        'subspecies': 'Subspecies',
        'subgenera': 'Subgenus',
        'genera': 'Genus',
        'subfamilies': 'Subfamily',
        'families': 'Family',
    }

    rank = None
    for key, val in match_cat_dict.items():
        if in_category(page, key):
            rank = val
            break
    # Exceptions for multiple matches
    if rank == 'Genus' and in_category(page, 'subgenera'):
        rank = 'Subgenus'
    if rank == 'Family' and in_category(page, 'subfamilies'):
        rank = 'Subfamily'

    return rank

# Get rank from lead
def rank_from_lead(lead_text):
    # Need to ensure eg that "is an order of fungi in the class Tremellomycetes" maps to 'Order' not Class'
    # So, regex covers:  "is a" + ... maximum of 30 chars not including 'in the' ... + "order"
    # Tempered greedy token - see http://www.rexegg.com/regex-quantifiers.html#tempered_greed
    regex_code = "(is a |are a |is an |are an |was a |were a |was an |were an )(?:(?! in the ).){,30}"
    match_lead_dict = {  # Partial strings to ensure unique matches
        'Subgenus': regex_code + 'subgenu',
        'Genus': regex_code + 'genus',
        'Superfamily': regex_code + 'superfami',
        'Family': regex_code + 'famil',
        'Subfamily': regex_code + 'subfami',
        'Tribe': regex_code + 'tribe',
        'Subtribe': regex_code + 'subtrib',
        'Class': regex_code + 'class',
        'Subclass': regex_code + 'subclas',
        'Order': regex_code + 'order',
        'Suborder': regex_code + 'suborde',
        'Clade': regex_code + 'clade',
        'Variety': regex_code + 'variet',
        'Species': regex_code + 'species',
        'Informal group': regex_code + 'informal group',
    }

    # Work through the parsed lead possibilities. Return if exactly one rank matches, otherwise None
    rank = None
    matched = False
    for key, val in match_lead_dict.items():
        if re.search(val, lead_text):
            if matched:
                return None
            # print("FOUND MATCH on", sdtype)
            rank = key
            matched = True

    return rank


# Rank from speciesbox or subspeciesbox
def rank_from_speciesbox(text_compressed):
    if '{{speciesbox' in text_compressed:
        return 'Species'
    if '{{subspeciesbox' in text_compressed:
        return 'Subspecies'


# Rank from general taxobox
def rank_from_taxobox(title_nobra, text_compressed):
    match_taxobox_dict = {
        'genus': 'Genus',
        'varietas': 'Variety',
        'tribus': 'Tribe',
        'superfamilia': 'Superfamily',
        'subtribus': 'Subtribe',
        'subspecies': 'Subspecies',
        'classis': 'Class',
        'subfamilia': 'Subfamily',
        'species': 'Species',
        'subordo': 'Suborder',
        'subgenus': 'Subgenus',
        'ordo': 'Order',
        'subclassis': 'Subclass',
        'familia': 'Family',
        'informalgroup': 'Informal group',
        'stemgroup': 'Group',
        'localgroup': 'Group',
        'clade': 'Clade',
        'cladus': 'Clade',
    }

    if '{{taxobox' not in text_compressed:
        return None
    rank = None

    for key, val in match_taxobox_dict.items():
        to_match = f"|{key}='''''{title_nobra}'''''"
        if to_match in text_compressed:
            rank = val

    if r"|binomial=''" in text_compressed:
        rank = 'Species'

    # Exceptions for multiple matches
    if rank == 'Genus' and f"|'subgenus='''''{title_nobra}'''''" in text_compressed:
        rank = 'Subgenus'
    if rank == 'Family' and f"|'subfamilia='''''{title_nobra}'''''" in text_compressed:
        rank = 'Subfamily'
    if rank == 'Tribe' and f"|'subtribus='''''{title_nobra}'''''" in text_compressed:
        rank = 'Subtribe'
    if rank == 'Species' and f"|'subspecies='''''{title_nobra}'''''" in text_compressed:
        rank = 'Subspecies'
    if rank == 'Class' and f"|'subclassis='''''{title_nobra}'''''" in text_compressed:
        rank = 'Subclass'
    if rank == 'Order' and f"|'subordo='''''{title_nobra}'''''" in text_compressed:
        rank = 'Suborder'

    return rank

# Rank and extinct status from autotaxobox
def info_from_autobox(wikipedia, text_compressed):
    match_auto_dict = {
        'genus': 'Genus',
        'varietas': 'Variety',
        'tribus': 'Tribe',
        'superfamilia': 'Superfamily',
        'subtribus': 'Subtribe',
        'subspecies': 'Subspecies',
        'classis': 'Class',
        'subfamilia': 'Subfamily',
        'species': 'Species',
        'subordo': 'Suborder',
        'subgenus': 'Subgenus',
        'ordo': 'Order',
        'subclassis': 'Subclass',
        'familia': 'Family',
        'informalgroup': 'Informal group',
        'stemgroup': 'Group',
        'localgroup': 'Group',
        'clade': 'Clade',
        'cladus': 'Clade',
    }

    if '{{automatictaxobox' not in text_compressed:
        return None, False
    rank = None

    try:
        taxon = find_between(text_compressed, 'taxon=', r'|')
        # print('Taxon: ', taxon)
        taxo_template = f'Template:Taxonomy/{taxon.capitalize()}'
        # print(taxo_template)
        taxo_page = pywikibot.Page(wikipedia, taxo_template)
        taxo_text_compressed = taxo_page.text.lower().replace(' ', '')
        taxo_rank = find_between(taxo_text_compressed, 'rank=', r'|')
        rank = match_auto_dict[taxo_rank]
        # print('Rank: ', rank)
    except:
        rank = None  # Return None if any exception, or if rank is not listed in auto_dict
    try:
        extinct = find_between(taxo_text_compressed, 'extinct=', r'|')
        isextinct = 'yes' in extinct or 'true' in extinct
        # print('Extinct: ', isextinct)
    except:
        isextinct = False  # Return False if any exception or if nothing is listed

    return rank, isextinct

