# Code for ShortDescBot, task 2 - organisms
#
# Michael Maggs, released under GPL v3
# Developed from original code by Mike Peel, GPL v3, 28 November 2020:
# https://bitbucket.org/mikepeel/wikicode/src/master/shortdesc_run.py and
# https://bitbucket.org/mikepeel/wikicode/src/master/shortdesc_functions.py
# 2020–21. Latest update 2 February 2021

from sd_add import *
from sd_stage import *

# Initialise the site
wikipedia = pywikibot.Site('en', 'wikipedia')
username = pywikibot.config.usernames['wikipedia']['en']

# Run staging code
if mode_flag == 'stage':
    print('\nLogged in as ' + username)
    if write_wp_examples:
        print(f'Will write up to {max_examples} examples to my Wikipedia userspace\n')
    if petscan_tf:
        input('***** Ready to stage from Petscan file. Press return to continue\n')
    else:
        input(f'***** Ready to stage from {targetcat}. Press return to continue\n')
    shortdesc_stage()

# Run live editing code
if mode_flag == 'edit':
    print('\nLogged in as ' + username)
    run_type = 'assisted' if assisted_mode else 'automatic'
    if override_manual or override_embedded:
        print('WARNING: the bot may change existing descriptions')
    input(f'***** READY TO WRITE LIVE EDITS in {run_type} mode. Press return to continue\n')
    shortdesc_add()
