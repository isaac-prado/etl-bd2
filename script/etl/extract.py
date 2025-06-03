import requests

REQUEST_FIELDS = (
    "code,product_name,nutriscore_grade,ecoscore_grade,nova_group,brands,"
    "categories_hierarchy,carbohydrates_100g,energy-kcal_100g,fat_100g,"
    "proteins_100g,saturated-fat_100g,sodium_100g,sugars_100g,"
    "ingredients,additives_tags,allergens_tags"
)
def fetch_product_data_from_api(product_code: str) -> dict | None:
    """
    Busca os dados de um produto da API.
    Retorna o JSON do produto ou None em caso de erro.
    """
    # URL da API diretamente no código
    api_url = f"https://world.openfoodfacts.net/api/v2/product/{product_code}.json"
    
    headers = {
        "User-Agent": "ETLProject/1.0 (isaacpalmeida@unifei.edu.br; Academic Project)"
    }

    params = {
        "fields": REQUEST_FIELDS
    }

    try:
        print(f"INFO: Buscando dados para o produto_code: {product_code} na URL: {api_url}")
        response = requests.get(api_url, headers=headers, params=params, timeout=20)
        response.raise_for_status() 
        
        data = response.json()
        if data.get("status") == 0 and "product not found" in data.get("status_verbose", ""):
            print(f"WARN: Produto {product_code} não encontrado na API (status 0). Detalhe: {data.get('status_verbose')}")
            return None
        if not data.get("product"): 
             print(f"WARN: Resposta da API para {product_code} não contém o objeto 'product'.")
             return None
        print(f"INFO: Dados para {product_code} extraídos com sucesso.")
        return data
    except requests.exceptions.HTTPError as http_err:
        print(f"ERROR: Erro HTTP ao buscar {product_code}: {http_err} - Status: {response.status_code} - Resposta: {response.text[:200]}...")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"ERROR: Erro de conexão ao buscar {product_code}: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"ERROR: Timeout ao buscar {product_code}: {timeout_err}")
    except requests.exceptions.JSONDecodeError as json_err:
        print(f"ERROR: Erro ao decodificar JSON da API para {product_code}: {json_err} - Resposta: {response.text[:200]}...")
    except requests.exceptions.RequestException as req_err:
        print(f"ERROR: Erro geral na requisição para {product_code}: {req_err}")
    return None