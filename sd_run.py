# Code for ShortDescBot, task 1 - moths
#
# Michael Maggs, released under GPL v3
# Incorporates code by Mike Peel, GPL v3, 28 November 2020:
# https://bitbucket.org/mikepeel/wikicode/src/master/shortdesc_run.py and
# https://bitbucket.org/mikepeel/wikicode/src/master/shortdesc_functions.py
# Latest update 13 January 2021


from sd_functions import *

# Run staging code
if mode_flag == 'stage':
    print('\nLogged in as ' + username)
    if petscan_tf:
        input('***** Ready to stage from Petscan file. Press return to continue\n')
    else:
        input(f'***** Ready to stage from {targetcat}. Press return to continue\n')
    shortdesc_stage()

# Run live editing code
if mode_flag == 'edit':
    print('\nLogged in as ' + username)
    if debug:
        run_type = 'assisted'
    else:
        run_type = 'automatic'
    print('\nLogged in as ' + username)
    input(f'***** READY TO WRITE LIVE EDITS in {run_type} mode. Press return to continue\n')
    shortdesc_add()
