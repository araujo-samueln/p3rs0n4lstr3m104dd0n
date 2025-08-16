# scraper.py
"""Módulo responsável por todo o scraping e extração de dados."""

import logging
import json
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

import cloudscraper
from bs4 import BeautifulSoup

from config import (
    BASE_URL, HEADERS, PROXIES, API_TOKEN, API_LIST_URL,
    VIDEO_PAGE_URL_TEMPLATE, ANIME_PAGE_URL_TEMPLATE, ID_PREFIX
)

class AnimesDigitalScraper:
    """Encapsula a lógica de scraping do site animesdigital.org."""

    def __init__(self):
        self.scraper = cloudscraper.create_scraper()

    def _make_request(self, method: str, url: str, **kwargs) -> Optional[str]:
        """Método centralizado para realizar requisições HTTP com tratamento de erros."""
        try:
            response = self.scraper.request(method, url, headers=HEADERS, proxies=PROXIES, **kwargs)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logging.error(f"Falha ao acessar {url}: {e}")
            return None

    # def _get_api_limit(self) -> int:
    #     """Obtém o limite de itens por página para a chamada da API."""
    #     response_text = self._make_request('GET', BASE_URL)
    #     if not response_text:
    #         return 290 # Valor de fallback do código original

    #     soup = BeautifulSoup(response_text, 'html.parser')
    #     limit_element = soup.find(class_='filter_number active')
    #     return int(limit_element['data-value']) if limit_element else 290

    def get_catalog(self, type_url: str, limit: int, search_query: str = "") -> List[Dict[str, Any]]:
        """Busca o catálogo de desenhos na API, com suporte a busca."""
        filters = {
            "filter_data": f"filter_letter=0&type_url={type_url}&filter_audio=dublado&filter_order=name",
            "filter_genre_add": "", "filter_genre_del": ""
        }
        payload = {
            'token': API_TOKEN, 'pagina': 1, 'limit': limit, 'type': 'lista',
            'search': search_query if search_query else 0,
            'filters': json.dumps(filters)
        }

        response_text = self._make_request('POST', API_LIST_URL, data=payload)
        if not response_text:
            return []
        
        try: # A API retorna um JSON malformado, então extraímos a parte válida.
            json_str = response_text[response_text.find('{') : response_text.rfind('}') + 1]
            if not json_str:
                raise json.JSONDecodeError("Nenhum objeto JSON encontrado.", response_text, 0)
            
            data = json.loads(json_str)
            return self._parse_catalog_html(data.get('results', []))
        except json.JSONDecodeError as e:
            logging.error(f"Falha ao decodificar JSON da API: {e}")
            return []

    def _parse_catalog_html(self, items: List[str]) -> List[Dict[str, Any]]:
        """Analisa os fragmentos de HTML da API para extrair dados do catálogo."""
        catalog = []
        for html in items:
            soup = BeautifulSoup(html, 'lxml')
            link = soup.find('a')
            img = soup.find('img')
            title = soup.find('span', class_='title_anime')

            if not all([link, img, title]) or not link.get('href'):
                continue
            
            path = urlparse(link['href']).path.strip('/')
            item_id = path.split('/')[-1] if path else None

            if item_id:
                catalog.append({
                    'id': f"{ID_PREFIX}{item_id}", 'type': "series", 'name': title.text.strip(),
                    'poster': img.get('src')
                })
        return catalog

    def get_series_metadata(self, series_slug: str) -> Optional[Dict[str, Any]]:
        """Busca os metadados de uma série, incluindo a lista de episódios."""
        page_url = ANIME_PAGE_URL_TEMPLATE.format(query=series_slug)
        response_text = self._make_request('GET', page_url)
        if not response_text:
            return None

        soup = BeautifulSoup(response_text, 'html.parser')
        try:
            name = soup.select_one("div.dados h1").text.strip()
            poster = soup.select_one("div.poster img")["src"]
        except (AttributeError, TypeError):
            logging.error(f"Erro ao parsear metadados para '{series_slug}'.")
            return None
        
        all_episode_divs = []
        pagination = soup.select_one("div.content-pagination")
        
        if pagination:
            try:
                last_page_link = pagination.select("li a")[-2]
                total_pages = int(last_page_link.text)
            except (IndexError, ValueError):
                total_pages = 1

            for page_num in range(total_pages, 0, -1):
                current_url = f"{page_url}/page/{page_num}" if page_num > 1 else page_url
                page_content = response_text if page_num == 1 else self._make_request('GET', current_url)
                
                if page_content:
                    page_soup = BeautifulSoup(page_content, 'html.parser')
                    all_episode_divs = page_soup.select("div.item_ep") + all_episode_divs
        else:
            all_episode_divs = soup.select("div.item_ep")

        episodes = []
        for i, ep_div in enumerate(reversed(all_episode_divs), start=1):
            link = ep_div.find('a', href=True)
            if link:
                episodes.append({
                    'id': link['href'].strip('/').split('/')[-1],
                    'season': 1,
                    'episode': i
                })
        return {'name': name, 'poster': poster, 'episodes': episodes}

    def get_stream_url(self, episode_slug: str) -> Optional[str]:
        """Obtém a URL final do stream a partir da página do vídeo."""
        page_url = VIDEO_PAGE_URL_TEMPLATE.format(episode_slug=episode_slug)
        response_text = self._make_request('GET', page_url)
        if not response_text:
            return None

        soup = BeautifulSoup(response_text, 'html.parser')
        iframe = soup.find("iframe", src=True)
        return iframe['src'] if iframe else None