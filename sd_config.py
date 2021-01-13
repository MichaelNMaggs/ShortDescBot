# Code for ShortDescBot, task 1 - moths
#
# Michael Maggs, released under GPL v3
# Incorporates code by Mike Peel, GPL v3, 28 November 2020:
# https://bitbucket.org/mikepeel/wikicode/src/master/shortdesc_run.py and
# https://bitbucket.org/mikepeel/wikicode/src/master/shortdesc_functions.py
# Latest update 13 January 2021

import re

import pywikibot

# INITIALISE

# MODE OF OPERATION:
# 'stage': write to staging file (and optionally examples to userspace)
# 'edit':  read from staging file and write live edits to namespace
mode_flag = 'stage'

#  STAGING CONFIGURATION

# Run staging based on from file of Petscan results in tsv format. Works from category unless petscan_tf = True
petscan_tf = False
petscan_file = "Petscan.tsv"

# Category to work on
targetcat = 'Category:Moths'
recurse_cats = True
verbose_stage = False

# Define the pages that that we are interested in. Others will be skipped without comment
require_infobox = False
infobox_strings = ['infobox']  # Add additional elements for various infobox types
sole_infobox = True  # Skip pages that have more than one infobox (applies only if require_infobox = True)
# Define test criteria. Pages that fail any of these will be recorded
required_words = []
excluded_words = []
test_regex_tf = True
test_regex = re.compile(r'', re.IGNORECASE)
title_regex_tf = True
title_regex = re.compile(r'^((?!list of).)*$', re.IGNORECASE)  # Fail any article entitled 'List of ...'
# Maximum number of articles to look through
max_arts = 0  # Set to 0 for no limit
# Set partial=True to enable processing between startpoint and endpoint. Set as False and '' to do all pages
partial = False
startpoint = ''
endpoint = ''
# Stage to file?
stage_to_file = True
max_stage = 0  # Set to 0 for no limit
success_file = 'Moths.txt'
failure_file = 'Moths_failures.txt'
# Write examples to my wp userspace?
wp_examples = False
max_examples = 200
success_examples_wp = 'User:MichaelMaggs/Moths'
failure_examples_wp = 'User:MichaelMaggs/Moths_failures'

#  **** For each task the code in shortdesc_generator also needs to be hand-crafted ****

#  EDIT CONFIGURATION
# Debug. Set to 'True' to run live editing in assisted mode (step though and confirm every amendment in advance)
# Run from normal account, not bot account, if before BAG approval
debug = False
# Set a longer than usual wait time between live wp edits. Normally controlled by put_throttle in user-config.py
wait_time = 0

# Initialise the site
wikipedia = pywikibot.Site('en', 'wikipedia')
username = pywikibot.config.usernames['wikipedia']['en']
