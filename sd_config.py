# See sd_run.py for status and copyright release information

import re

import pywikibot

# INITIALISE

# MODE OF OPERATION:
# 'stage': write to staging file (and optionally examples to userspace)
# 'edit':  read from staging file and write live edits to namespace
mode_flag = 'stage'

#  STAGING CONFIGURATION

name_singular = 'velvet worm'
name_plural = 'velvet worms'
# Category to work on
targetcat = 'Onychophorans'
# Run staging based on from file of Petscan results in tsv format. Works from category unless petscan_tf = True
petscan_tf = False
petscan_file = "Petscan.tsv"

recurse_cats = False
verbose_stage = False

# Define the pages that that we are interested in. Others will be skipped without comment
require_infobox = True
infobox_strings = ['Speciesbox', 'Taxobox']  # Covers Automatic Taxobox and Subspeciesbox
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
max_stage = 0  # Set to 0 for no limit
success_file = 'success.tsv'
failure_file = 'failures.tsv'
# Write examples to my wp userspace?
write_wp_examples = False
wp_examples_page = 'User:MichaelMaggs/ShortDesc'
max_examples = 200

#  EDIT CONFIGURATION
# Debug: set to 'True' to run live editing in assisted mode (step though and confirm every amendment in advance)
# Run from normal account, not bot account, if before BAG approval
debug = True
# Set a longer than usual wait time between live wp edits. Normally controlled by put_throttle in user-config.py
wait_time = 0
# Set allow_sd_changes to True if the bot is allowed to replace existing descriptions
allow_sd_changes = False

# Initialise the site
wikipedia = pywikibot.Site('en', 'wikipedia')
username = pywikibot.config.usernames['wikipedia']['en']
