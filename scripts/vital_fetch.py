#!/usr/bin/env python3
"""
Fetch Wikipedia Vital Articles (Levels) and save a curated JSON file.

Run:
  python scripts/vital_fetch.py

Output:
  vital_articles.json        - curated list with status/exclude fields for manual review
  vital_articles_raw.json    - raw metadata backup (titles + page_id + extract)
"""
import requests  # HTTP library for MediaWiki API calls
import json      # JSON serialization for output files
import time      # Rate-limiting delays between API requests
import argparse  # CLI argument parsing
import os        # OS utilities (unused, kept for future file ops)
import urllib.parse
from html.parser import HTMLParser

# Wikipedia MediaWiki API endpoint; all requests go here
API_ENDPOINT = "https://en.wikipedia.org/w/api.php"
MAX_TITLES_PER_QUERY = 50  # MediaWiki query limit for titles per request
REQUEST_DELAY = 0.1        # Delay between requests to obey API load limits
MAX_RETRIES = 3            # Number of retries for transient API errors

# Vital Articles pages to fetch from Wikipedia.
# Level 1 = most vital, Level 5 = least vital.
# The main index page is also included.
PAGES = [
    "Wikipedia:Vital articles/Level/1",
    "Wikipedia:Vital articles/Level/2",
    "Wikipedia:Vital articles/Level/3",
    "Wikipedia:Vital articles/Level/4",
    "Wikipedia:Vital articles/Level/5",
    "Wikipedia:Vital articles"
]


def api_get(session, params):
    """Perform a GET request with retry/backoff and return parsed JSON."""
    headers = {
        'User-Agent': 'pedantle-vital-fetch/1.0 (vardesailee@gmail.com)'
    }
    for attempt in range(1, MAX_RETRIES + 1):
        r = session.get(API_ENDPOINT, params=params, headers=headers, timeout=30)
        if r.status_code == 429 or r.status_code == 503:
            # Back off on too many requests or temporary unavailability
            sleep_time = REQUEST_DELAY * attempt
            time.sleep(sleep_time)
            continue
        r.raise_for_status()
        return r.json()
    # Final attempt without catching to surface errors
    r = session.get(API_ENDPOINT, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()


class WikiLinkHTMLParser(HTMLParser):
    """HTML parser that extracts Wikipedia article titles from anchor hrefs."""

    def __init__(self):
        super().__init__()
        self.titles = []

    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        href = None
        for name, value in attrs:
            if name == 'href':
                href = value
                break
        if not href or not href.startswith('/wiki/'):
            return

        # Ignore non-article namespaces and special pages.
        path = href.split('#', 1)[0].split('?', 1)[0]
        title = path[len('/wiki/'):]
        title = urllib.parse.unquote(title).replace('_', ' ')
        if not title or ':' in title:
            return
        self.titles.append(title)


def fetch_links(session, page):
    """Fetch article links from a Wikipedia page using the parse API.

    Uses rendered HTML output, which expands templates and transclusions,
    then extracts direct /wiki/ anchors from that output.
    """
    params = {
        'action': 'parse',      # Parse action returns structured wiki markup
        'page': page,           # Target page
        'prop': 'text',        # Get rendered HTML output
        'format': 'json'       # JSON response format
    }
    data = api_get(session, params)
    parse_data = data.get('parse', {})
    html_text = parse_data.get('text', {}).get('*', '')

    parser = WikiLinkHTMLParser()
    parser.feed(html_text)
    titles = parser.titles

    print(f"  {page}: parsed HTML got {len(titles)} link targets")
    print(f"  {page}: finished with {len(titles)} total articles")
    return titles


def chunked(iterable, n):
    """Yield successive chunks of size n from an iterable.
    
    Args:
        iterable: sequence to chunk
        n: chunk size (e.g., 50 titles per API batch)
    
    Yields:
        lists of n items (or fewer on final chunk)
    """
    it = list(iterable)
    for i in range(0, len(it), n):
        yield it[i:i+n]


def fetch_metadata(session, titles):
    """Fetch page IDs and intro extracts for a list of article titles.
    
    Batches titles (50 at a time) to stay within API limits.
    Returns a dict mapping title -> {page_id, extract}.
    
    Args:
        session: requests Session
        titles: list of article title strings
    
    Returns:
        dict {title: {page_id: int, extract: str}}
    """
    metadata = {}
    # Process in batches of 50 to respect API query limits
    for batch in chunked(titles, MAX_TITLES_PER_QUERY):
        params = {
            'action': 'query',              # Query action for page info
            'titles': '|'.join(batch),      # Pipe-delimited list of titles
            'prop': 'info|extracts|pageprops',  # Include pageprops to detect disambiguation
            'exintro': 1,                   # Only get intro section (not full article)
            'explaintext': 1,               # Strip wiki markup from extract
            'redirects': 1,                 # Auto-follow redirects
            'format': 'json',
            'formatversion': 2              # Newer JSON format
        }
        data = api_get(session, params)
        # Extract page_id and intro text for each article
        for page in data.get('query', {}).get('pages', []):
            title = page.get('title')
            # pageprops may include a 'disambiguation' key for disambig pages
            pageprops = page.get('pageprops', {}) or {}
            is_disambig = 'disambiguation' in pageprops
            metadata[title] = {
                'page_id': page.get('pageid'),
                'extract': page.get('extract') or '',
                'pageprops': pageprops,
                'is_disambiguation': bool(is_disambig)
            }
        # Small delay to respect Wikipedia's rate-limiting guidelines
        time.sleep(REQUEST_DELAY)
    return metadata


def main():
    """Main entry point: fetch Vital Articles and save curated + raw JSON files."""
    # Parse command-line arguments for custom output file names
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', '-o', default='vital_articles.json',
                        help='Output file for curated list (default: vital_articles.json)')
    parser.add_argument('--raw', default='vital_articles_raw.json',
                        help='Output file for raw metadata backup (default: vital_articles_raw.json)')
    args = parser.parse_args()

    # Create a persistent session for connection pooling and cookie handling
    session = requests.Session()
    all_titles = []      # Accumulate all titles from all pages
    level_map = {}       # Map: title -> level (1-5 or 'index')

    print('Fetching links from Vital Articles pages...')
    # Iterate through each Vital Articles page and extract article titles
    for page in PAGES:
        try:
            titles = fetch_links(session, page)
        except Exception as e:
            print(f'Failed to fetch {page}: {e}')
            titles = []
        
        # Extract level number from page name (e.g., '/Level/3' -> '3')
        lvl = 'unknown'
        if '/Level/' in page:
            lvl = page.split('/Level/')[-1]
        else:
            lvl = 'index'
        
        # Record the level for each title (first level encountered is kept)
        for t in titles:
            if t not in level_map:
                level_map[t] = lvl
        
        all_titles.extend(titles)
        time.sleep(0.1)  # Rate limiting between page fetches

    # Remove duplicates while preserving order (dict.fromkeys preserves insertion order in Python 3.7+)
    unique_titles = list(dict.fromkeys(all_titles))
    print(f'Found {len(unique_titles)} unique article titles.')

    # Fetch page IDs and intro text for all unique titles
    print('Fetching page metadata (pageid + extract)...')
    metadata = fetch_metadata(session, unique_titles)

    # Build the curated item list with culling fields for manual review
    items = []
    for t in unique_titles:
        md = metadata.get(t, {})
        # Skip disambiguation pages entirely in the curated output
        if md.get('is_disambiguation'):
            # keep them in the raw backup, but do not include in curated list
            continue

        # Non-disambiguation pages are added with a default 'review' status
        items.append({
            'title': t,
            'page_id': md.get('page_id'),
            'level': level_map.get(t, 'unknown'),
            'status': 'review',
            'exclude_reason': '',
            'notes': '',
            'extract': md.get('extract', '')
        })

    # Save raw backup file (titles + full metadata dict)
    with open(args.raw, 'w', encoding='utf-8') as f:
        json.dump({'titles': unique_titles, 'metadata': metadata}, f, indent=2, ensure_ascii=False)

    # Save curated file (structured list with culling fields)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

    print('Saved', args.output, 'and', args.raw)


# Entry point: run main() when script is executed directly
if __name__ == '__main__':
    main()
