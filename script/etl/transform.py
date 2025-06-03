import model

def _get_enum_member(enum_class, value_str: str | int | None):
    if value_str is None: return None
    str_value_for_lookup = str(value_str)
    if enum_class == model.TipoNovaScoreDB: # Acessa via model.
        for member in enum_class:
            if member.value == str_value_for_lookup: return member
    else:
        for member in enum_class:
            if member.name == str_value_for_lookup.upper(): return member
    print(f"WARN: Valor '{value_str}' não encontrado no enum {enum_class.__name__}. Retornando None.")
    return None

def _parse_boolean_from_api(value: str | None) -> bool | None:
    if value is None: return None
    val_lower = str(value).lower()
    if val_lower in ["yes", "en:yes", "true"]: return True
    if val_lower in ["no", "en:no", "false"]: return False
    if val_lower == "maybe": print(f"DEBUG: Valor 'maybe' encontrado para booleano, será tratado como None.")
    return None

def transform_api_data(api_data: dict, requested_product_code: str) -> dict | None:
    if not api_data or "product" not in api_data or not isinstance(api_data["product"], dict) :
        print(f"WARN: Dados da API ausentes, 'product' não é um dicionário ou está incompleto para o código solicitado {requested_product_code}")
        return None

    product_api = api_data["product"]
    actual_product_code = product_api.get("code")
    if not actual_product_code:
        print(f"ERROR: Campo 'code' ausente dentro do objeto 'product' da API para o código solicitado {requested_product_code}. Impossível prosseguir.")
        return None
    if actual_product_code != requested_product_code:
        print(f"WARN: Código do produto na API ({actual_product_code}) difere do código solicitado ({requested_product_code}). Usando código da API: {actual_product_code}.")
    
    print(f"INFO: Iniciando transformação para o produto_code: {actual_product_code}")
    transformed_data = {}
    nova_score_api_val = product_api.get("nova_group")
    transformed_data["produto"] = {
        "codigo": actual_product_code,
        "nome": product_api.get("product_name"),
        "nutriscore": _get_enum_member(model.TipoNutriEcoScoreDB, product_api.get("nutriscore_grade")),
        "ecoscore": _get_enum_member(model.TipoNutriEcoScoreDB, product_api.get("ecoscore_grade")),
        "novascore": _get_enum_member(model.TipoNovaScoreDB, nova_score_api_val),
    }
    transformed_data["marca_nome"] = product_api.get("brands")
    transformed_data["categorias_nomes"] = []
    for cat_api in product_api.get("categories_hierarchy", []):
        if cat_api and isinstance(cat_api, str):
            cat_name = cat_api.split(":")[-1]
            if cat_name: transformed_data["categorias_nomes"].append(cat_name)
    transformed_data["tags"] = []
    for tag_api in product_api.get("allergens_tags", []):
        if tag_api and isinstance(tag_api, str):
            tag_name = tag_api.split(":")[-1]
            if tag_name: transformed_data["tags"].append({"nome": tag_name, "tipo": model.TipoTagDB.allergen})
    for tag_api in product_api.get("additives_tags", []):
        if tag_api and isinstance(tag_api, str):
            tag_name = tag_api.split(":")[-1]
            if tag_name: transformed_data["tags"].append({"nome": tag_name, "tipo": model.TipoTagDB.additive})
    transformed_data["nutrientes_produto"] = []
    nutrient_fields_map = {
        "energy-kcal_100g": {"nome": "Energy Kcal", "unidade": "kcal"},
        "fat_100g": {"nome": "Fat", "unidade": "g"},
        "saturated-fat_100g": {"nome": "Saturated fat", "unidade": "g"},
        "carbohydrates_100g": {"nome": "Carbohydrates", "unidade": "g"},
        "sugars_100g": {"nome": "Sugars", "unidade": "g"},
        "proteins_100g": {"nome": "Proteins", "unidade": "g"},
        "sodium_100g": {"nome": "Sodium", "unidade": "g"},
    }
    for api_field, nutrient_info in nutrient_fields_map.items():
        api_value = product_api.get(api_field)
        if api_value is not None:
            try:
                quantidade = float(api_value) 
                transformed_data["nutrientes_produto"].append({
                    "nome_nutriente": nutrient_info["nome"],
                    "unidade_nutriente": nutrient_info["unidade"],
                    "quantidade_100g": quantidade
                })
            except (ValueError, TypeError):
                print(f"WARN: Valor não numérico para nutriente '{api_field}' no produto {actual_product_code}: '{api_value}'")
    transformed_data["ingredientes_produto"] = []
    for ing_api in product_api.get("ingredients", []):
        if not isinstance(ing_api, dict):
            print(f"WARN: Item de ingrediente não é um dicionário para o produto {actual_product_code}: {ing_api}")
            continue
        nome_ingrediente = ing_api.get("text")
        if not nome_ingrediente or not isinstance(nome_ingrediente, str) or not nome_ingrediente.strip():
            original_id_api = ing_api.get("id", "ID_API_DESCONHECIDO")
            print(f"WARN: Ingrediente com ID textual da API '{original_id_api}' no produto {actual_product_code} não possui nome (text) válido. Ingrediente ignorado.")
            continue
        quantity_val = ing_api.get("percent")
        if quantity_val is None:
            quantity_val = ing_api.get("percent_estimate")
        quantidade_estimada_final = None
        if quantity_val is not None:
            try:
                quantidade_estimada_final = float(quantity_val)
            except (ValueError, TypeError):
                print(f"WARN: Valor de quantidade ('{quantity_val}') inválido para ingrediente '{nome_ingrediente}' no produto {actual_product_code}.")
        transformed_data["ingredientes_produto"].append({
            "nome_ingrediente": nome_ingrediente.strip(),
            "vegano": _parse_boolean_from_api(ing_api.get("vegan")),
            "vegetariano": _parse_boolean_from_api(ing_api.get("vegetarian")),
            "quantidade_estimada": quantidade_estimada_final
        })
    print(f"INFO: Transformação concluída para o produto_code: {actual_product_code}")
    return transformed_data