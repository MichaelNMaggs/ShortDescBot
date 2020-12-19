

import pywikibot



article = 'Father Christmas'


wikipedia = pywikibot.Site('en', 'wikipedia')
print(wikipedia)
page = pywikibot.Page(wikipedia, article)
username = pywikibot.config.usernames['wikipedia']['en']

text = page.text


