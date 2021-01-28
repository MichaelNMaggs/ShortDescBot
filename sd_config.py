# See sd_run.py for status and copyright release information

import re

import pywikibot

# INITIALISE

# MODE OF OPERATION:
# 'stage': write to staging file (and optionally examples to userspace)
# 'edit':  read from staging file and write live edits to namespace
mode_flag = 'edit'

#  STAGING CONFIGURATION

name_singular = 'moth'
name_plural = 'moths'
# Category to work on
targetcat = ''
# Run staging based on from file of Petscan results in tsv format. Works from category unless petscan_tf = True
petscan_tf = True
petscan_file = "Petscan.tsv"

recurse_cats = False
verbose_stage = True

# Define the pages that that we are interested in. Others will be skipped without comment
require_infobox = True
infobox_strings = ['Speciesbox', 'Taxobox']  # Covers Automatic Taxobox and Subspeciesbox (case insensitive)
sole_infobox = False  # Skip pages that have more than one infobox (applies only if require_infobox = True)

# Define any one-off special test criteria. Can usually skip this. Pages that fail any of these will be recorded
# These just restrict the pages from the Cat or Petscan input are considered as targets, not how they will be processed
# NOTE: For how the targets are to be processed, need to hand-craft the code in shortdesc_generator
required_words = []  # Must have all of these
some_words = []  # Must have at least one of these
excluded_words = []  # Must not have any of these
text_regex_tf = False
text_regex = re.compile(r'', re.IGNORECASE)
title_regex_tf = False
title_regex = re.compile(r'', re.IGNORECASE)

# Maximum number of articles to process, not including articles that are skipped
max_arts = 0  # Set to 0 for no limit
# Set partial=True to enable processing between startpoint and endpoint. Set as False and '' to do all pages
partial = False
startpoint = ''
endpoint = ''
# Stage to file?
stage_to_file = True
max_stage = 20  # Set to 0 for no limit
success_file = 'success.tsv'    #  < This is the output file for staging and the input file for editing
failure_file = 'failures.tsv'
# Write examples to my wp userspace?
write_wp_examples = False
wp_examples_page = 'User:MichaelMaggs/ShortDesc'
max_examples = 200

#  EDIT CONFIGURATION
# assisted_mode: set to 'True' to step though and confirm every live edit in advance
# Run from normal account, not bot account, if before BAG approval
assisted_mode = True
# Set a longer than usual wait time between live wp edits. Normally controlled by put_throttle in user-config.py
wait_time = 0
# Is the bot allowed to change existing existing manual/embedded descriptions?
override_manual = True  # Existing description with the {{Short description}} template
override_embedded = False  # Existing description embedded within eg an infobox

# Initialise the site
wikipedia = pywikibot.Site('en', 'wikipedia')
username = pywikibot.config.usernames['wikipedia']['en']
