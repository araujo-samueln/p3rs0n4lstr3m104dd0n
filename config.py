# config.py
"""Módulo de configuração centralizado para a aplicação."""

from datetime import timedelta

# --- Configurações do Servidor ---
APP_HOST = "0.0.0.0"
APP_PORT = 5000

# --- Configurações de Caching ---
# Define o tempo de vida do cache para 4 horas e o tamanho máximo.
CACHE_TTL = timedelta(hours=4).total_seconds()
CACHE_MAXSIZE = 256

# --- Configurações do Scraper ---
BASE_URL = "https://animesdigital.org"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Origin': BASE_URL,
    'Referer': f"{BASE_URL}/",
    'X-Requested-With': 'XMLHttpRequest'
}
PROXIES = None # Desativado por padrão. Ative se necessário.

# --- Configurações do Addon Stremio ---
ID_PREFIX = "ad:" # "ad" de AnimesDigital
MANIFEST = {
    'id': 'org.animesdigital.personal',
    'version': '2.0.0',
    'name': 'Animes Digital',
    'description': 'Addon pessoal para desenhos dublados do AnimesDigital.',
    'types': ['series'],
    'catalogs': [
        {
            "id": "desenhosCatalog",
            "type": "series",
            "name": "AD:Desenhos",
            "extra": [{"name": "search", "isRequired": False}]
        },
        {
            "id": "animesCatalog",
            "type": "series",
            "name": "AD:Animes",
            "extra": [{"name": "search", "isRequired": False}]
        }
        
    ],
    'resources': [
        'catalog',
        {'name': 'meta', 'types': ['series'], 'idPrefixes': [ID_PREFIX]},
        {'name': 'stream', 'types': ['series'], 'idPrefixes': [ID_PREFIX]}
    ]
}

# --- Constantes da API do Site ---
API_TOKEN = "c1deb78cd4"
API_LIST_URL = f"{BASE_URL}/func/listanime"
VIDEO_PAGE_URL_TEMPLATE = f"{BASE_URL}/video/a/{{episode_slug}}"
ANIME_PAGE_URL_TEMPLATE = f"{BASE_URL}/anime/a/{{query}}"