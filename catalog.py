import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse

BASE_URL = "https://animesdigital.org"

TOKEN = "c1deb78cd4"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


PROX={
        "http": "http://edlhxrdo:31f47r79qu9u@23.95.150.145:6114/",
        "https": "http://edlhxrdo:31f47r79qu9u@23.95.150.145:6114/"
    }

def obter_token_e_limite():
    try:
        pagina_listagem_url = f"{BASE_URL}" 
        response = requests.get(pagina_listagem_url, headers=HEADERS, proxies=PROX)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        token_element = soup.find(class_='menu_filter_box')
        token = token_element['data-secury'] if token_element else None
        limit_element = soup.find(class_='filter_number active')
        limit = limit_element['data-value'] if limit_element else 100
        if not token:
            print("ERRO: Não foi possível encontrar o 'token' na página.")
            # return None, None
        print(f"Token encontrado: {token}")
        print(f"Limite encontrado: {limit}")
        return TOKEN, limit
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar a página principal: {e}")
        return None, None

def buscar_animes(token, limit, pagina=1, pesquisa=0, filtros={}):
    api_url = f"{BASE_URL}/func/listanime"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': BASE_URL,
        'Referer': f"{BASE_URL}/animes"
    }
    
    filter_data_string = (
        f"filter_letter={filtros.get('filter_letter', 0)}"
        f"&type_url={filtros.get('type_url', '')}"
        f"&filter_audio={filtros.get('filter_audio', '')}"
        f"&filter_order={filtros.get('filter_order', 'name')}"
    )

    filters_obj_interno = {
        "filter_data": filter_data_string,
        "filter_genre_add": filtros.get('filter_genre_add', ''),
        "filter_genre_del": filtros.get('filter_genre_del', '')
    }
    
    payload = {
        'token': token,
        'pagina': pagina,
        'search': pesquisa,
        'limit': limit,
        'type': 'lista',
        'filters': json.dumps(filters_obj_interno)
    }
    
    try:
        response = requests.post(api_url, headers=headers, data=payload)
        texto_completo = response.text
        inicio_json = texto_completo.find('{')
        fim_json = texto_completo.rfind('}')
        
        if inicio_json != -1 and fim_json != -1:
            string_json_puro = texto_completo[inicio_json : fim_json + 1]
            dados = json.loads(string_json_puro)
            return dados['results']
        else:
            print("ERRO: Não foi possível encontrar um objeto JSON ({...}) na resposta.")
            return None
    except Exception as e:
        print(f"Erro na requisição POST: {e}")
        return None
    
def extrair_catalogo(dados):
    catalogo = []
    
    for html in dados:
        soup = BeautifulSoup(html, 'lxml')    

        try:
            link_tag = soup.find('a')
            img_tag = soup.find('img')
            title_tag = soup.find('span', class_='title_anime')

            # Extrai o link para obter o ID e o tipo
            href = link_tag.get('href')
            path_parts = urlparse(href).path.strip('/').split('/')
            
            # Ex: /video/a/25750b0 -> type='video', id='a/25750b0'
            item_type = path_parts[0] if path_parts else None
            item_id = path_parts[-1]
            # item_id = '/'.join(path_parts[1:]) if len(path_parts) > 1 else None

            # Extrai o nome do anime/episódio
            name = title_tag.text.strip()

            # Extrai a URL do poster
            poster = img_tag.get('src')
            
            # Adiciona ao catálogo apenas se todos os dados essenciais foram encontrados
            if item_id and item_type and name and poster:
                catalogo.append({
                    'id': item_id,
                    'type': "series",
                    'name': name,
                    'poster': poster
                })

        except AttributeError:
            continue
                
    return catalogo

def get_lista_desenho():
    token_seguranca, limite_pagina = obter_token_e_limite()
    print(token_seguranca, "  " , limite_pagina)
    if token_seguranca:
        dados_recebidos = buscar_animes(
            token=token_seguranca, 
            limit=limite_pagina,
            pagina=1, 
            pesquisa=0, 
            filtros={
                "filter_letter": 0,
                "type_url": "desenhos",
                "filter_audio": "dublado",
                "filter_order": "name",
                "filter_genre_add": "", 
                "filter_genre_del": "" 
            }
        )

        if dados_recebidos:
            return extrair_catalogo(dados_recebidos)
        
    return None




