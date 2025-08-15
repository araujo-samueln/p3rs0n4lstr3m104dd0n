import cloudscraper
from bs4 import BeautifulSoup

BASE_URL = "https://animesdigital.org"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

PROX={
        "http": "http://edlhxrdo:31f47r79qu9u@23.95.150.145:6114/",
        "https": "http://edlhxrdo:31f47r79qu9u@23.95.150.145:6114/"
    }

scraper = cloudscraper.create_scraper()

def get_info(query):
    try:
        page_url = f"{BASE_URL}/anime/{query}"
        response = scraper.get(page_url, headers=HEADERS, proxies=PROX)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        series_name = soup.find("div", class_="dados").find("h1").text.strip()
        poster_url = soup.find("div", class_="poster").find("img")["src"]
        
        series_info = {
            'name': series_name,
            'poster': poster_url,
        }

        episodes = []
        ep_divs = soup.find_all("div", class_="item_ep")
        
        for i, ep_div in enumerate(reversed(ep_divs)): # Reverse to get Ep 1 first
            link_tag = ep_div.find('a')
            if not link_tag:
                continue
            
            href = link_tag.get('href')
            episode_id = href.split('/')[-2]
            episode_title = ep_div.find("div", class_="title_anime").text.strip()
            
            episodes.append({
                'id': episode_id,
                'title': episode_title,
                'season': 1, # Assuming a single season for simplicity
                'episode': i + 1,
            })
            
        return {'series_info': series_info, 'episodes': episodes}
            
    except Exception as e:
        print(f"Error scraping info for '{query}': {e}")
        return None
    
def get_stream_url(episode_slug):
    """Scrapes the final episode page to get the direct video URL."""
    try:
        page_url = f"{BASE_URL}/video/a/{episode_slug}" 
        response = scraper.get(page_url, headers=HEADERS, proxies=PROX)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        return soup.find("iframe")['src']
        # Encontra a tag de vídeo e pega o atributo 'src'
        # video_tag = soup.find("video", id="my_video_1")
        # if video_tag and video_tag.has_attr('src'):
        #     return video_tag['src']
            
        return None
        
    except Exception as e:
        print(f"Error scraping stream for '{episode_slug}': {e}")

        return None



