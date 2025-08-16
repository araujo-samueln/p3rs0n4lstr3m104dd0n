import logging
from datetime import datetime, timezone

from flask import Flask, jsonify, abort
from cachetools import cached, TTLCache

from config import MANIFEST, ID_PREFIX, CACHE_TTL, CACHE_MAXSIZE, APP_HOST, APP_PORT, BASE_URL, HEADERS
from scraper import AnimesDigitalScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)
scraper = AnimesDigitalScraper()
cache = TTLCache(maxsize=CACHE_MAXSIZE, ttl=CACHE_TTL)

def respond_with(data):
    """Cria uma resposta JSON com cabeçalhos CORS."""
    resp = jsonify(data)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = '*'
    return resp

@app.route('/manifest.json')
def addon_manifest():
    return respond_with(MANIFEST)

@app.route('/catalog/<type>/<id>.json')
@app.route('/catalog/<type>/<id>/search=<search_query>.json')
def addon_catalog(type: str, id: str, search_query: str = None):
    if type != 'series' or id != 'desenhosCatalog':
        abort(404)
    
    metas = get_cached_catalog(id, search_query)
    return respond_with({'metas': metas})

@cached(cache)
def get_cached_catalog(id: str, search_query: str = None):
    """Função cacheada para buscar e formatar o catálogo."""
    logging.info(f"CACHE MISS - Buscando catálogo (busca: {search_query or 'N/A'})")
    
    if id == 'desenhosCatalog':
        id_type = "desenhos"
        limit = 290
    else:
        id_type = "animes"
        limit = 310
    
    items = scraper.get_catalog(id_type, limit, search_query)
    return [{'id': f"{ID_PREFIX}{i['id']}", **i} for i in items]

@app.route('/meta/<type>/<id>.json')
@cached(cache)
def addon_meta(type: str, id: str):
    logging.info(f"CACHE MISS - Buscando metadados para ID: {id}")
    if type != 'series' or not id.startswith(ID_PREFIX):
        abort(404)

    series_slug = id[len(ID_PREFIX):]
    data = scraper.get_series_metadata(series_slug)
    if not data:
        abort(404, "Metadados não encontrados.")

    videos = [{
        'id': f"{ID_PREFIX}{ep['id']}", 'title': f"Episódio {ep['episode']}",
        'season': ep['season'], 'episode': ep['episode'],
        'released': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    } for ep in data['episodes']]
    
    meta = {
        'id': id, 'type': type, 'name': data['name'], 'poster': data['poster'],
        'description': data.get('description', ''), 'videos': videos
    }
    return respond_with({'meta': meta})

@app.route('/stream/<type>/<id>.json')
def addon_stream(type: str, id: str):
    if type != 'series' or not id.startswith(ID_PREFIX):
        abort(404)
        
    episode_slug = id[len(ID_PREFIX):]
    stream_url = scraper.get_stream_url(episode_slug)
    if not stream_url:
        return respond_with({'streams': []})

    stream = {
        "externalUrl": stream_url,
        "title": "Link Dublado",
        "behaviorHints": {
            "proxyHeaders": {
                "request": {"Referer": BASE_URL, "User-Agent": HEADERS['User-Agent']}
            }
        }
    }
    return respond_with({'streams': [stream]})

if __name__ == '__main__':
    app.run(host=APP_HOST, port=APP_PORT, debug=False)