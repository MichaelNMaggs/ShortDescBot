# See sd_run.py for status and copyright release information

from statistics import multimode

from sd_adjust_desc import adjust_desc
from sd_functions import *
from sd_rank_from import rank_from_category, rank_from_lead, rank_from_speciesbox, \
    rank_from_taxobox, info_from_autobox
from sd_is_monotypic_genus import is_monotypic_genus


# Generate the draft SD. Called by shortdesc_stage. Returns (True, description) for good result, or (False, errortext)
# NOTE: For each bot task, the code here needs to be hand-crafted
def shortdesc_generator(page, lead_text):
    #  Make compressed searchable version of page text
    text_compressed = page.text.lower().replace(' ', '')

    # Get title, ignoring brackets
    title = page.title()
    title_nobra = re.sub(r'\(.+?\)', '', title).strip()
    single_word_title = True if len(title_nobra.split()) == 1 else False

    rank_category = rank_from_category(page)
    rank_lead = rank_from_lead(title_nobra, lead_text, name_singular, verbose_stage)
    rank_speciesbox = rank_from_speciesbox(text_compressed)
    rank_taxobox = rank_from_taxobox(title_nobra, text_compressed)
    rank_autobox, isextinct_autobox = info_from_autobox(wikipedia, text_compressed)
    all_ranks = [rank_category, rank_lead, rank_speciesbox, rank_taxobox, rank_autobox]

    # Must be Variety or Subspecies if so noted in title
    if 'var.' in title:
        best_rank = 'Variety'
        shortdesc = best_rank + ' of ' + shortdesc_end(best_rank, name_singular, name_singular)
        return True, adjust_desc(page, lead_text, shortdesc, isextinct_autobox)
    if 'subsp.' in title:
        best_rank = 'Subspecies'
        shortdesc = best_rank + ' of ' + shortdesc_end(best_rank, name_singular, name_singular)
        return True, adjust_desc(page, lead_text, shortdesc, isextinct_autobox)

    # Get the most common rank from the list (excluding None)
    all_ranks_xnone = [x for x in all_ranks if x is not None]
    best_ranks = multimode(all_ranks_xnone)  # List of most common ranks (eg a list of 2 if there is a tie)
    best_rank = ''
    if len(best_ranks) == 1:
        best_rank = best_ranks[0]  # The single best rank, if there is one

    if verbose_stage:
        print('rank_category, rank_lead, rank_speciesbox, rank_taxobox, rank_autobox')
        print(all_ranks)
        print(all_ranks_xnone)
        print('best_ranks: ', best_ranks, 'Best rank: ', best_rank)

    # Deal with situation where a single best rank has been identified
    if best_rank:

        if single_word_title:  # Species is unexpected if single-word title; but may be monotypic genus
            if best_rank == 'Species' and is_monotypic_genus(text_compressed, lead_text):
                best_rank = 'Genus'
                shortdesc = best_rank + ' of ' + shortdesc_end(best_rank, name_singular, name_plural)
                return True, adjust_desc(page, lead_text, shortdesc, isextinct_autobox)
            if best_rank in ['Subspecies', 'Variety']:  # Subspecies/variety is unexpected if single-word title
                shortdesc = best_rank + ' of ' + shortdesc_end(best_rank, name_singular, name_singular)
                return False, '*** : ' + adjust_desc(page, lead_text, shortdesc, isextinct_autobox)

        if not single_word_title:  # Genus or higher rank unexpected if multi-word title
            if best_rank not in ('Species', 'Subspecies', 'Variety'):
                shortdesc = best_rank + ' of ' + shortdesc_end(best_rank, name_singular, name_plural)
                return False, '*** : ' + adjust_desc(page, lead_text, shortdesc, isextinct_autobox)

        shortdesc = best_rank + ' of ' + shortdesc_end(best_rank, name_singular, name_plural)  # Best rank looks good
        return True, adjust_desc(page, lead_text, shortdesc, isextinct_autobox)

    # Return False if nothing at all works
    diff_ranks = list(set(all_ranks_xnone))
    if not diff_ranks:
        return False, "*** : NO MATCHING RANKS"

    # At this point we have several conflicting ranks for this page

    # Exceptions for Genus/Species: single-word titles classified as species are normally monotypic genus articles
    # Single-word titles are very rarely species
    if 'Genus' in diff_ranks and 'Species' in diff_ranks:
        if not single_word_title:
            shortdesc = 'Species' + ' of ' + name_singular
        if single_word_title:
            shortdesc = 'Genus' + ' of ' + name_plural
        return True, adjust_desc(page, lead_text, shortdesc, isextinct_autobox)

    # Prefer subspecies/variety to species
    if 'Subspecies' in diff_ranks and 'Species' in diff_ranks:
        shortdesc = 'Subspecies' + ' of ' + name_singular
        return True, adjust_desc(page, lead_text, shortdesc, isextinct_autobox)
    if 'Variety' in diff_ranks and 'Species' in diff_ranks:
        shortdesc = 'Variety' + ' of ' + name_singular
        return True, adjust_desc(page, lead_text, shortdesc, isextinct_autobox)

    # Accept Species if a two-word title and at least one other possibility matches
    if 'Species' in diff_ranks and len(title_nobra.split()) == 2:
        if verbose_stage:
            print('Two-word title and at least one match to Species')
        shortdesc = 'Species' + ' of ' + name_singular
        return True, adjust_desc(page, lead_text, shortdesc, isextinct_autobox)

    # Drop inconsistent_automatictaxobox rank, and check if there is a new best one. Then return with that
    if rank_autobox is not None:
        best_ranks.remove(rank_autobox)
        if len(best_ranks) == 1:
            best_rank = best_ranks[0]  # The single best rank, if there is one
            shortdesc = best_rank + ' of ' + shortdesc_end(best_rank, name_singular, name_plural)
            if verbose_stage:
                print(f'Overriding automatictaxobox rank: ', rank_autobox)
                print('New best_ranks: ', best_ranks, 'New best_rank: ', best_rank)
            return True, adjust_desc(page, lead_text, shortdesc, isextinct_autobox)

    # Failed: return with some useful error text
    if rank_autobox is not None:
        return False, f'*** :  AUTOTAXOBOX HAS {rank_autobox}'

    return False, "*** : CAN'T GET BEST RANK"
