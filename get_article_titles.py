import requests
import time

request_delay = 0.1 

def get_vital_articles(level=1):
    session = requests.Session()
    session.headers.update({"User-Agent": "MyVitalArticlesGame/1.0 (your@email.com)"})

    params = {
    'action': 'query',
    'titles': f"Wikipedia:Vital_articles/Level/{level}",
    'prop': 'links',
    'pllimit': 'max',
    'plnamespace': 0,   # main article namespace only
    'format': 'json',
    'formatversion': 2
}

    articles = []
    while True:
        response = session.get("https://en.wikipedia.org/w/api.php", params=params).json()
        links = response["query"]["pages"].popitem()[1]["links"]
        articles += [l["*"] for l in links if l["ns"] == 0]

        if "continue" not in response:
            break
        params.update(response["continue"])
        time.sleep(request_delay)  # Respect API rate limits

    return articles

def main():
    #for level in range(1, 6):
    level = 1
    print(f"Fetching Level {level} vital articles...")
    articles = get_vital_articles(level)
    print(f"Level {level} has {len(articles)} articles.")

if __name__ == "__main__":
    main()
        