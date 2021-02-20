# See sd_run.py for status and copyright release information

import pywikibot
from sd_functions import find_between

def info_automatictaxobox(wikipedia, txt_comp):
    auto_dict = {
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
    }

    try:
        taxon = find_between(txt_comp, 'taxon=', r'|')
        #print('Taxon: ', taxon)
        taxo_template = f'Template:Taxonomy/{taxon.capitalize()}'
        #print(taxo_template)
        taxo_page = pywikibot.Page(wikipedia, taxo_template)
        taxo_txt_comp = taxo_page.text.lower().replace(' ', '')
        taxo_rank = find_between(taxo_txt_comp, 'rank=', r'|')
        rank = auto_dict[taxo_rank]
        #print('Rank: ', rank)
    except:
        rank = None  # Return None if any exception or if rank is not listed in auto_dict
    try:
        extinct = find_between(taxo_txt_comp, 'extinct=', r'|')
        isextinct = 'yes' in extinct or 'true' in extinct
        #print('Extinct: ', isextinct)
    except:
        isextinct = False  # Return False if any exception or if nothing is listed

    return rank, isextinct

