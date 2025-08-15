from flask import Flask, Response, jsonify, url_for, abort
from functools import wraps
import catalog
import version1_backup.animesdigitalstream as animesdigitalstream
from datetime import datetime, timezone


app = Flask(__name__)

OPTIONAL_META = ["posterShape", "background", "logo", "videos", "description", "releaseInfo", "imdbRating", "director", "cast",
                 "dvdRelease", "released", "inTheaters", "certification", "runtime", "language", "country", "awards", "website", "isPeered"]


def respond_with(data):
    resp = jsonify(data)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = '*'
    return resp

METAHUB_URL = 'https://images.metahub.space/poster/medium/{}/img'

MANIFEST = {
    'id': 'org.personal',
    'version': '1.0.0',

    'name': 'Sam Personal Addon',
    'description': 'Personal Stremio Addon Dublado',

    'types': ['movie', 'series'],

    'catalogs': [
            {"id": "movieCatalog", "type": "movie", "name": "Filmes"},
            {"id": "desenhosCatalog", "type": "series", "name": "Desenhos"},
            {"id": "seriesCatalog", "type": "series", "name": "Seriados"}
    ],

    'resources': [
        'catalog',
        {
            'name': 'stream', 
            'types': ['movie', 'series'],
            'idPrefixes': ["ps"]
        },
        {
            "name": "meta",
            "types": ["movie", "series"],
            "idPrefixes": ["ps"]
        }
    ]
}

@app.route('/manifest.json')
def addon_manifest():
    return respond_with(MANIFEST)

@app.route('/catalog/<type>/<id>.json')
def addon_catalog(type, id:str):
    if type not in MANIFEST['types']:
        abort(404)
    
    if type == "series" and id.startswith("desenhosCatalog"):
        metaPreviews = {
            'metas': [
                {
                    'id': 'psa:'+item['id'],
                    'type': item['type'],
                    'name': item['name'],
                    'poster': item['poster']
                } for item in catalog.get_lista_desenho()
            ]
        }
        return respond_with(metaPreviews)

@app.route('/meta/<type>/<id>.json')
def addon_meta(type, id):
    print(type," ", id)

    
    if type not in MANIFEST['types']:
        abort(404)
    
    if type == "series" and id.startswith('ps'):
        
        series_slug = id.split(':')[-1]
        data = animesdigitalstream.get_info(series_slug)
        
        series_info = data['series_info']
        episodes_list = data['episodes']
        original_poster_url = series_info['poster']
        
        video_objects = []
        for ep in episodes_list:
            release_date = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

            video_objects.append({
                'id': f"ps:{ep['id']}:{ep['season']}:{ep['episode']}",
                'title': "Episodio " + str(ep['episode']),
                'released': release_date,
                'season': ep['season'],
                'episode': ep['episode']
            })

        meta_object = {
            'id': id,
            'type': type,
            'name': series_info['name'],
            'poster' : original_poster_url,
            'videos': video_objects 
        }

        # Wrap it in the final response format
        return respond_with({'meta': meta_object})

@app.route('/stream/<type>/<id>.json')
def addon_stream(type, id):

    if type not in MANIFEST['types']:
         abort(404)
    
    if type == "series" and id.startswith('ps'):

        id_parts = id.split(':')
        # The episode slug is the second part (index 1)
        episode_slug = id_parts[1] 

        stream_url = animesdigitalstream.get_stream_url(episode_slug)
        
        if not stream_url:
            return respond_with({'streams': []})

        search_term = "mp4"
        index_of_mp4 = stream_url.index(search_term)
        end_index = index_of_mp4 + len(search_term)
        
        # 3. Slice the string from the beginning to the calculated end position
        substring = stream_url[:end_index]
        
        streams = [{
            "externalUrl": stream_url,
            "title": "Link Dublado",
            "behaviorHints": {
                # This tells Stremio to use its native player, which ignores CORS
                # "notWebReady": True,
                
                # This sends the required headers to the server
                "proxyHeaders": {
                    "request": {
                        "Referer": "https://animesdigital.org/",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
                    }
                }
            }
        }]

        
        return respond_with({'streams': streams})
        
    # If the prefix doesn't match, return an empty list
    return respond_with({'streams': []})
        
    
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000')
