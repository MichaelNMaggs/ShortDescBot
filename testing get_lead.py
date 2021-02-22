# Just some ad hoc tests. Not part of the codebase

import re

import pywikibot

from sd_functions import clean_text, find_parens
from sd_get_lead import get_lead

article = 'Anderella'
wikipedia = pywikibot.Site('en', 'wikipedia')
page = pywikibot.Page(wikipedia, article)

if not page.exists():
    print(' PAGE DOES NOT EXIST')



lead= get_lead(page)
print('\n***** FINAL LEAD *****')
print(lead)
