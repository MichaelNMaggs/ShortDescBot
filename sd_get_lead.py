# See sd_run.py for status and copyright release information

from sd_config import *
from sd_functions import find_parens, clean_text


# Clean up lead and get the first 150 chars
def get_lead(page):
    sections = pywikibot.textlib.extract_sections(page.text, wikipedia)
    lead = sections[0]
    # Remove any templates: {{ ... }}
    # First, replace template double braces with single so we can use find_parens
    try:
        lead = lead.replace("{{", "{")
        lead = lead.replace("}}", "}")
        result = find_parens(lead, '{', '}')  # Get start and end indexes for all templates
        # Go through templates and replace with ` strings of same length, to avoid changing index positions
        for key in result:
            start = key
            end = result[key]
            length = end - start + 1
            lead = lead.replace(lead[start:end + 1], "`" * length)
    except IndexError:
        pass

    # Deal with piped wikilinks: replace [[xxx|yyy]] with [[yyy]]
    lead = re.sub(r"\[([^\]\[|]*)\|", "[", lead, re.MULTILINE)

    # Remove any images: [[File: ... ]] or [[Image: ... ]]
    # Replace double square brackets with single so we can use find_parens
    try:
        lead = lead.replace("[[", "[")
        lead = lead.replace("]]", "]")
        result = find_parens(lead, '[', ']')  # Get start and end indexes for all square brackets
        # Go through results and replace wikicode representing images with ` strings of same length
        for key in result:
            start = key
            end = result[key]
            strstart = lead[start + 1:start + 7]
            if 'File:' in strstart or 'Image:' in strstart:
                length = end - start + 1
                lead = lead.replace(lead[start:end + 1], "`" * length)
    except IndexError:
        pass

    # Remove re-used refs such as <ref name = "Name" / >
    lead = re.sub("<ref.{1,40}\/\s{0,3}>", "", lead, re.MULTILINE)

    # Replace "<ref" and "ref>" with sentinels ! and ~ so we can use find_parens
    try:
        lead = lead.replace("<ref", "!")
        lead = lead.replace("ref>", "~")
        lead = lead.replace("ref >", "~")
        # # Go through templates and replace with ` strings of same length
        result = find_parens(lead, '!', '~')  # Get start and end indexes for sentinels
        for key in result:
            start = key
            end = result[key]
            length = end - start + 1
            lead = lead.replace(lead[start:end + 1], "`" * length)
    except:  # (Don't know why, but need to reverse the replacements here)
        lead = lead.replace("!", "<ref")
        lead = lead.replace("~", "ref>")

    # Delete the temporary ` strings and clean up
    try:
        lead = clean_text(lead)  # (includes removal of remaining '[' and ']')
        lead = lead[:150].strip()
    except:
        pass

    return lead
