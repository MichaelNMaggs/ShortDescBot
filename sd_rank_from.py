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
        'superfamilies': 'Superfamily',
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
    if rank == 'Family' and in_category(page, 'superfamilies'):
        rank = 'Superfamily'

    return rank


# Get rank from lead
def rank_from_lead(lead_txt):
    # Tight regex, just to catch obvious leads such as "is a <rank> ..."
    regex_code1 = "(is\sa|are\sa|was\sa|were\sa)\s"
    # Looser regex covering "is a", "is an" etc + ... maximum of 30 chars not including 'in the' ... + "order"
    # Need to ensure eg that "is an order of fungi in the class Tremellomycetes" maps to 'Order' not Class'
    # Tempered greedy token - http://www.rexegg.com/regex-quantifiers.html#tempered_greed
    regex_code2 = "(is\sa|are\sa|was\sa|were\sa)(?:(?!\sin\sthe).){0,50}\s"  # Looser

    lead_dict1 = {  # Partial strings to ensure unique matches
        'Subgenus': regex_code1 + 'subgenu',
        'Genus': regex_code1 + 'genus',
        'Superfamily': regex_code1 + 'superfami',
        'Family': regex_code1 + 'famil',
        'Subfamily': regex_code1 + 'subfami',
        'Tribe': regex_code1 + 'tribe',
        'Subtribe': regex_code1 + 'subtrib',
        'Class': regex_code1 + 'class',
        'Subclass': regex_code1 + 'subclas',
        'Order': regex_code1 + 'order',
        'Suborder': regex_code1 + 'suborde',
        'Infraorder': regex_code1 + 'infraorde',
        'Clade': regex_code1 + 'clade',
        'Variety': regex_code1 + 'variet',
        'Species': regex_code1 + 'species',
        'Informal group': regex_code1 + 'informal group',
    }
    lead_dict2 = {  # Partial strings to ensure unique matches
        'Subgenus': regex_code2 + 'subgenu',
        'Genus': regex_code2 + 'genus',
        'Superfamily': regex_code2 + 'superfami',
        'Family': regex_code2 + 'famil',
        'Subfamily': regex_code2 + 'subfami',
        'Tribe': regex_code2 + 'tribe',
        'Subtribe': regex_code2 + 'subtrib',
        'Class': regex_code2 + 'class',
        'Subclass': regex_code2 + 'subclas',
        'Order': regex_code2 + 'order',
        'Suborder': regex_code2 + 'suborde',
        'Infraorder': regex_code1 + 'infraorde',
        'Clade': regex_code2 + 'clade',
        'Variety': regex_code2 + 'variet',
        'Species': regex_code2 + 'species',
        'Informal group': regex_code2 + 'informal group',
    }

    rank = None
    # For this function only, just consider the first sentence
    lead_sen = lead_txt.split('.')[0]
    if len(lead_sen) > 26:  # Don't do this if first sentence is unreasonably short
        lead_txt = lead_sen

    # Pre-filter with tight regex 1 to extract any obvious initial match before attempting anything cleverer

    for key, val in lead_dict1.items():
        #print('INITIAL ', key, val)
        if re.search(val, lead_txt):
            rank = key
            print('Regex1 lead rank is ', rank)
            return rank

    # Work through the possibilities with looser regex 2. Return if exactly one rank matches, otherwise None
    matched = False
    for key, val in lead_dict2.items():
        if re.search(val, lead_txt):
            print("A regex2 lead match on", key)
            if matched:
                return None
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
    # Check whether the exact title_nobra is shown in bold. If so, that defines the rank (apart from species/subspecies)
    for key, val in match_taxobox_dict.items():
        to_match = f"|{key}='''''{title_nobra}'''''"  # No match if first part of a binomial is abbreviated
        if to_match in text_compressed:
            # print ("RETURNING 1")
            return val

    # Check what else is in bold
    for key, val in match_taxobox_dict.items():
        to_match = f"|{key}='''''"  # No match if first part of a binomial is abbreviated
        if to_match in text_compressed:
            rank = val

    # Exceptions for multiple matches
    if rank == 'Genus' and r"|'subgenus='''''" in text_compressed:
        rank = 'Subgenus'
        # print("RETURNING 2")
        return rank
    if rank == 'Family' and r"|'subfamilia='''''" in text_compressed:
        rank = 'Subfamily'
        # print("RETURNING 3")
        return rank
    if rank == 'Tribe' and r"|'subtribus='''''" in text_compressed:
        rank = 'Subtribe'
        # print("RETURNING 4")
        return rank
    if rank == 'Species' and r"|'subspecies='''''" in text_compressed:
        rank = 'Subspecies'
        # print("RETURNING 5")
        return rank
    if rank == 'Class' and r"|'subclassis='''''" in text_compressed:
        rank = 'Subclass'
        # print("RETURNING 6")
        return rank
    if rank == 'Order' and r"|'subordo='''''" in text_compressed:
        rank = 'Suborder'
        # print("RETURNING 7")
        return rank

    # Species/genus oddities
    # Accept species if genus is not in bold
    if "|genus='''''" not in text_compressed:
        species_strs = ["|species='''''", "|binomial=''"]  # (only two quote marks for binomial)
        if any(x in text_compressed for x in species_strs):
            rank = "Species"
            if r"|'subspecies='''''" in text_compressed:
                rank = 'Subspecies'
            # print("RETURNING 8")
            return rank
    # If both genus and species both in bold, probably a monotypic genus
    if "|genus='''''" in text_compressed:
        species_strs = ["|species='''''", "|binomial=''"]  # (only two quote marks for binomial)
        if any(x in text_compressed for x in species_strs):
            rank = "Genus"
            # print("RETURNING 9")
            return rank

    # print("RETURNING 10")
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

    isextinct = False
    try:
        taxon = find_between(text_compressed, 'taxon=', r'|')
        taxo_template = f'Template:Taxonomy/{taxon.capitalize()}'
        taxo_page = pywikibot.Page(wikipedia, taxo_template)
        taxo_txt_comp = taxo_page.text.lower().replace(' ', '')
        taxo_rank = find_between(taxo_txt_comp, 'rank=', r'|')
        rank = match_auto_dict[taxo_rank]
        if '|extinct=yes' in taxo_txt_comp or '|extinct=true' in taxo_txt_comp:
            isextinct = True
        return rank, isextinct
    except:
        return None, False


# ********** NOT YET IN USE ***************

# Does lead_text match possible_rank (ignoring other possibilities)?
def check_rank_from_lead(lead_text, possible_rank):
    regex_code = "(is\sa|are\sa|was\sa|were\sa)(?:(?!\sin\sthe).){0,50}\s"
    match_lead_dict = {
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
    # Searching only the first sentence of the lead
    if re.search(match_lead_dict[possible_rank], lead_text.split('.')[0]):
        return True

    return False
