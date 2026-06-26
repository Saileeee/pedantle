import requests
import time
import json

REQUEST_DELAY = 1
#MAX_RETRIES = 5
api_endpoint = "https://en.wikipedia.org/w/api.php"

#only works for levels 1-3 probably
def get_vital_articles(session, level=1):
    base_params = {
        'action': 'query', 
        'titles': f"Wikipedia:Vital_articles/Level_{level}",
        'prop': 'links',
        'pllimit': 'max',
        'plnamespace': 0,
        'format': 'json',
        'formatversion': 2
    }

    articles = []
    params = base_params.copy()

    while True:
        #get page links
        response = session.get(api_endpoint, params=params, timeout = 30)
        try:           
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            if response.status_code == 429:    
                print("Error 429: Too Many Requests. Waiting for 5 seconds before retrying...")
                time.sleep(5)
                continue
            print(f"Request failed: {e}")
            break
        
        #get the actual data from the response 
        pages = data.get("query", {}).get("pages", [])

        #add title from links in each page if not a disambiguation page
        for page in pages:
            for link in page.get("links", []):
                title = link.get("title")
                if title:
                    articles.append(title)
        print(f"Fetched {len(articles)} articles so far...")


        if data.get("continue"):
            # Update only the continue keys, keep base params intact
            params = {**base_params, **data["continue"]}
            time.sleep(REQUEST_DELAY)
        else:
            break
  
    return articles

def main():
    level = 3 #just testing level 1 for now
    session = requests.Session()
    session.headers.update({"User-Agent": "MyVitalArticlesGame/1.0 (vardesailee@gmail.com)"})

    print(f"Fetching Level {level} vital articles...")
    articles = get_vital_articles(session, level) 
    # later add a loop to get levels 2 & 3 and additional handling for 4 & 5
    articles = list(set(articles))  # deduplicate
    print(f"Level {level} has {len(articles)} unique articles.")

    output_path = f"vital_articles_level_{level}.json"
    with open(output_path, "w") as f:
        json.dump(articles, f, indent=2)
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    main()
        