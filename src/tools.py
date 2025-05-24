from googlesearch import search

def web_search(query):
    """Perform a web search"""
    return search(query, num_results=3)