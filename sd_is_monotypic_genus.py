# See sd_run.py for status and copyright release information

# Return True if a monotypic genus article. Call ony when a single-word species article is suspected to be a genus
def is_monotypic_genus(text_compressed, lead_text):
    mono_list_page = ['[[category:monotypic']
    mono_list_lead = ['monotypic', 'monospecific', ' a single species', ' the single species',
                      ' single-species', ' only one species', ' only the one species',
                      ' its only species']

    for mono in mono_list_page:  # Parse entire page
        if mono.lower() in text_compressed:
            return True
        for mono in mono_list_lead:  # Parse the lead only
            if mono in lead_text.lower():
                return True

    return False
