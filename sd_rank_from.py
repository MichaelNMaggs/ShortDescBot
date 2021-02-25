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
        'orders': 'Order',
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
def rank_from_lead(title_nobra, lead_txt, name_singular, verbose_stage):
    regex_start1 = "(is\sa|is\san|was\sa|was\san)\s"  # eg "is a genus ..."
    # Regex2 covers eg "is a" + <maximum of 30 chars not including 'in the'> + "genus"
    # Need to ensure that "is an order of fungi in the class Tremellomycetes" maps to 'Order' not Class'
    # Tempered greedy token - http://www.rexegg.com/regex-quantifiers.html#tempered_greed
    regex_start2 = "(is\sa|are\sa|was\sa|were\sa)(?:(?!\sin\sthe).){0,50}\s"

    lead_dict1 = {  # Partial strings to ensure unique matches
        'Subgenus': regex_start1 + 'subgenu',
        'Genus': regex_start1 + 'genus',
        'Superfamily': regex_start1 + 'superfami',
        'Family': regex_start1 + 'famil',
        'Subfamily': regex_start1 + 'subfami',
        'Tribe': regex_start1 + 'tribe',
        'Subtribe': regex_start1 + 'subtrib',
        'Class': regex_start1 + 'class',
        'Subclass': regex_start1 + 'subclas',
        'Order': regex_start1 + 'order',
        'Suborder': regex_start1 + 'suborde',
        'Infraorder': regex_start1 + 'infraorde',
        'Clade': regex_start1 + 'clade',
        'Variety': regex_start1 + 'variet',
        'Species': regex_start1 + 'species',
        'Informal group': regex_start1 + 'informal group',
        'Phylum': regex_start1 + 'phylum',
        'Subphylum': regex_start1 + 'subphylu',
    }
    lead_dict2 = {  # Partial strings to ensure unique matches
        'Subgenus': regex_start2 + 'subgenu',
        'Genus': regex_start2 + 'genus',
        'Superfamily': regex_start2 + 'superfami',
        'Family': regex_start2 + 'famil',
        'Subfamily': regex_start2 + 'subfami',
        'Tribe': regex_start2 + 'tribe',
        'Subtribe': regex_start2 + 'subtrib',
        'Class': regex_start2 + 'class',
        'Subclass': regex_start2 + 'subclas',
        'Order': regex_start2 + 'order',
        'Suborder': regex_start2 + 'suborde',
        'Infraorder': regex_start1 + 'infraorde',
        'Clade': regex_start2 + 'clade',
        'Variety': regex_start2 + 'variet',
        'Species': regex_start2 + 'species',
        'Informal group': regex_start2 + 'informal group',
        'Phylum': regex_start1 + 'phylum',
        'Subphylum': regex_start1 + 'subphylu',
    }
    rank = None

    # For this function only, just consider the first sentence
    lead_sen = lead_txt.split('.')[0]
    if len(lead_sen) > 26:  # Don't do this if first sentence is unreasonably short
        lead_txt = lead_sen

    # Pre-filter with tight regex of lead_dict1 to extract any obvious match before attempting anything clever
    for key, val in lead_dict1.items():
        if re.search(val, lead_txt):  # eg "is a genus ..."
            rank = key
            if verbose_stage:
                print('lead_dict1 lead rank is ', rank)
            return rank

    # Must be Species if lead has eg "Abacetus alesi is a beetle ..."
    regex_sp1 = f"{title_nobra}\s(is\sa|is\san|was\sa|was\san)\s{name_singular}"
    if re.search(regex_sp1, lead_txt):
        if verbose_stage:
            print('regex_sp1 lead match on Species')
        return 'Species'

    # Most probably Species if lead has eg " ... is a beetle ..."
    regex_sp2 = f"(is\sa|is\san|was\sa|was\san)\s{name_singular}"
    if re.search(regex_sp2, lead_txt):
        if verbose_stage:
            print('regex_sp2 lead match on Species')
        return 'Species'

    # Work through the options with looser regex of lead_dict2. Return if exactly one rank matches, otherwise None
    matched = False
    for key, val in lead_dict2.items():
        if re.search(val, lead_txt):
            if verbose_stage:
                print('lead_dict2 lead matches on ', key)
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
        'phylum':  'Phylum',
        'subphylum': 'Subphylum',
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
        'phylum': 'Phylum',
        'subphylum': 'Subphylum',
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
        'Phylum': regex_code + 'phylum',
        'Subphylum': regex_code + 'subphylu',
    }
    # Searching only the first sentence of the lead
    if re.search(match_lead_dict[possible_rank], lead_text.split('.')[0]):
        return True

    return False
