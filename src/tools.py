from duckduckgo_search import DDGS

def web_search(query):
    """Perform a web search using DuckDuckGo and return the results."""
    return DDGS().text(query, max_results=5, safesearch='Moderate')