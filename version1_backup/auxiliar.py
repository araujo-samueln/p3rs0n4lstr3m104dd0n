import requests
from PIL import Image, ImageOps
from io import BytesIO
import os

# --- Constantes de Configuração ---
# O ideal é manter configurações em um local centralizado.
POSTER_DIR = 'static/posters'
TARGET_ASPECT_RATIO = 1 / 0.675
TARGET_WIDTH = 400  # Largura final padronizada para os pôsteres.
BASE_URL = "http://127.0.0.1:5000" # URL base da sua aplicação.

# --- Cache e Inicialização ---
poster_cache = {}
os.makedirs(POSTER_DIR, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

PROX={
        "http": "http://edlhxrdo:31f47r79qu9u@23.95.150.145:6114/",
        "https": "http://edlhxrdo:31f47r79qu9u@23.95.150.145:6114/"
    }



def get_processed_poster(series_id: str, jpg_url: str) -> str:
    """
    Faz o download, corta, redimensiona e salva um pôster de imagem.
    Retorna a URL local para a imagem processada.
    """
    if series_id in poster_cache:
        return poster_cache[series_id]

    png_filename = f"{series_id}.png"
    png_filepath = os.path.join(POSTER_DIR, png_filename)
    
    # Se o arquivo já existe, não processa novamente.
    if os.path.exists(png_filepath):
        local_png_url = f"{BASE_URL}/{POSTER_DIR}/{png_filename}"
        poster_cache[series_id] = local_png_url
        return local_png_url

    try:
        response = requests.get(jpg_url, timeout=10, headers=HEADERS, proxies=PROX)
        response.raise_for_status()

        with Image.open(BytesIO(response.content)) as img:
            # Centraliza e corta a imagem para o aspect ratio desejado.
            cropped_img = ImageOps.fit(
                img, 
                (TARGET_WIDTH, int(TARGET_WIDTH * TARGET_ASPECT_RATIO)), 
                method=Image.Resampling.LANCZOS
            )
            
            # Salva a imagem processada no formato PNG com otimização.
            cropped_img.save(png_filepath, 'PNG', optimize=True)

        local_png_url = f"{BASE_URL}/{POSTER_DIR}/{png_filename}"
        poster_cache[series_id] = local_png_url
        
        return local_png_url

    except requests.exceptions.RequestException as e:
        print(f"Falha no download da imagem para series_id {series_id}: {e}")
        return jpg_url # Retorna URL original em caso de falha de rede.
    except Exception as e:
        print(f"Falha ao processar a imagem para series_id {series_id}: {e}")

        return jpg_url # Retorna URL original em caso de falha de processamento.

