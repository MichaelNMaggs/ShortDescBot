# See sd_run.py for status and copyright release information

import re

import pywikibot

# INITIALISE

# MODE OF OPERATION:
# 'stage': write to staging file (and optionally examples to userspace)
# 'edit':  read from staging file and write live edits to namespace
#  Note: When writing live edits, the SDs are taken from the staging file, and are not re-calculated anew
mode_flag = 'edit'

#  STAGING CONFIGURATION

# Base text for SDs
name_singular = 'woodlouse'
name_plural = 'woodlice'
verbose_stage = False

# Maximum number of articles to process, not including articles that are skipped
max_arts = 0  # Set to 0 for no limit
# Set partial=True to enable processing between startpoint and endpoint. Set as False and '' to do all pages
partial = False
startpoint = ''
endpoint = ''

# Staging input
# NOTE: Make sure this covers only the required subcategories, as some may have little relevance to the top level cat
# (1) Read from WP Category. Does this unless use_basefile = True
targetcat = ''
recurse_cats = True  # Be careful with this!
# (2) Or, read from use_basefile, in tsv format
# This can be a Petscan tsv output file, or a recycled and manually-corrected staged_fail file
use_basefile = True
base_file = f'base_file {name_plural}.tsv'

# Define the pages that that we intend to stage. Others will be skipped without comment
require_infobox = False
infobox_strings = ['Speciesbox', 'Taxobox']  # Covers Automatic Taxobox and Subspeciesbox (case insensitive)
sole_infobox = False  # Skip pages that have more than one infobox (applies only if require_infobox = True)

# Special staging criteria. Can usually skip this. Pages that fail any of these will be recorded
# These restrict the pages from the Cat/base_file input that are considered as targets, not how they will be processed
# For how the targets are to be processed, need to hand-craft the code in shortdesc_generator
required_words = []  # Must have all of these
some_words = []  # Must have at least one of these
excluded_words = []  # Must not have any of these
text_regex_tf = False  # Check for this regex in the text
text_regex = re.compile(r'', re.IGNORECASE)
title_regex_tf = False  # Check for this regex in the page title
title_regex = re.compile(r'', re.IGNORECASE)

# Staging output
stage_to_file = True  # Stage to file?
max_stage = 0  # Set to 0 for no limit
staging_file = f'staged {name_plural}.tsv'  # (date is added for staging_file output)
staged_fail = f'staged_fail {name_plural}.tsv'
write_wp_examples = False  # Write some examples to my wp userspace, for community review
wp_examples_page = 'User:MichaelMaggs/ShortDesc'
max_examples = 200

#  EDIT CONFIGURATION

# assisted_mode: set to True to step though and confirm every live edit in advance
# If before BAG approval, must run from normal user account, not the bot account,
assisted_mode = False
# Is the bot allowed to change existing existing manual/embedded descriptions?
override_manual = False  # Existing description with the {{Short description}} template
override_embedded = False  # Existing description embedded within eg an infobox
# Set a longer than usual wait time between live wp edits. Normally controlled by put_throttle in user-config.py
wait_time = 0

# Initialise the site
wikipedia = pywikibot.Site('en', 'wikipedia')
username = pywikibot.config.usernames['wikipedia']['en']
