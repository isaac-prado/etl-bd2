# load.py
from sqlalchemy.orm import Session
import model

def get_or_create_marca(db: Session, nome_marca: str | None) -> model.Marca | None:
    if not nome_marca or not isinstance(nome_marca, str):
        print(f"DEBUG: Nome da marca ausente ou inválido: {nome_marca}")
        return None
    marca_obj = db.query(model.Marca).filter(model.Marca.nome == nome_marca).first()
    if not marca_obj:
        marca_obj = model.Marca(nome=nome_marca)
        db.add(marca_obj)
        db.flush() 
        print(f"INFO: Marca criada: '{nome_marca}' (ID: {marca_obj.id})")
    return marca_obj

def get_or_create_categoria(db: Session, nome_categoria: str) -> model.Categoria | None:
    if not nome_categoria: return None
    cat_obj = db.query(model.Categoria).filter(model.Categoria.nome == nome_categoria).first()
    if not cat_obj:
        cat_obj = model.Categoria(nome=nome_categoria)
        db.add(cat_obj)
        db.flush()
        print(f"INFO: Categoria criada: '{nome_categoria}' (ID: {cat_obj.id})")
    return cat_obj

def get_or_create_tag(db: Session, nome_tag: str, tipo_tag_enum: model.TipoTagDB) -> model.Tag | None:
    if not nome_tag: return None
    tag_obj = db.query(model.Tag).filter(model.Tag.nome == nome_tag, model.Tag.tipo == tipo_tag_enum).first()
    if not tag_obj:
        tag_obj = model.Tag(nome=nome_tag, tipo=tipo_tag_enum)
        db.add(tag_obj)
        db.flush()
        print(f"INFO: Tag criada: '{nome_tag}' (Tipo: {tipo_tag_enum.value}, ID: {tag_obj.id})")
    return tag_obj

def get_or_create_nutriente(db: Session, nome_nutriente: str, unidade_nutriente: str) -> model.Nutriente | None:
    if not nome_nutriente or not unidade_nutriente: return None
    nut_obj = db.query(model.Nutriente).filter(model.Nutriente.nome == nome_nutriente).first()
    if not nut_obj:
        nut_obj = model.Nutriente(nome=nome_nutriente, unidade=unidade_nutriente)
        db.add(nut_obj)
        db.flush()
        print(f"INFO: Nutriente criado: '{nome_nutriente}' ({unidade_nutriente}), ID: {nut_obj.id}")
    elif nut_obj.unidade != unidade_nutriente:
        print(f"ERROR: CONFLITO DE UNIDADE para Nutriente '{nome_nutriente}': DB='{nut_obj.unidade}', API='{unidade_nutriente}'. Usando unidade do DB.")
    return nut_obj

def get_or_create_ingrediente_by_name(db: Session, nome_ing: str, vegano: bool | None, vegetariano: bool | None) -> model.Ingrediente | None:
    if not nome_ing or not isinstance(nome_ing, str) or not nome_ing.strip():
        print(f"WARN: Nome do ingrediente ausente ou inválido: '{nome_ing}'. Ingrediente ignorado.")
        return None
    nome_ing_limpo = nome_ing.strip()
    ingrediente_obj = db.query(model.Ingrediente).filter(model.Ingrediente.nome == nome_ing_limpo).first()
    if not ingrediente_obj:
        ingrediente_obj = model.Ingrediente(nome=nome_ing_limpo, vegano=vegano, vegetariano=vegetariano)
        db.add(ingrediente_obj)
        db.flush()
        print(f"INFO: Ingrediente CRIADO: '{nome_ing_limpo}' (ID: {ingrediente_obj.id}, Vegano: {vegano}, Vegetariano: {vegetariano})")
    else:
        updated = False
        if vegano is not None and ingrediente_obj.vegano != vegano:
            ingrediente_obj.vegano = vegano
            updated = True
        if vegetariano is not None and ingrediente_obj.vegetariano != vegetariano:
            ingrediente_obj.vegetariano = vegetariano
            updated = True
        if updated:
            db.flush()
            print(f"INFO: Ingrediente ATUALIZADO: '{nome_ing_limpo}' (ID: {ingrediente_obj.id}, Vegano: {vegano}, Vegetariano: {vegetariano})")
        else:
            print(f"DEBUG: Ingrediente ENCONTRADO: '{nome_ing_limpo}' (ID: {ingrediente_obj.id}). Sem alterações.")
    return ingrediente_obj

def load_data_to_db(db: Session, transformed_data: dict):
    produto_data_dict = transformed_data["produto"]
    codigo_produto = produto_data_dict["codigo"]
    print(f"INFO: Iniciando carregamento para o produto: {codigo_produto}")
    produto_existente = db.query(model.Produto).filter(model.Produto.codigo == codigo_produto).first()
    if produto_existente:
        print(f"INFO: Produto {codigo_produto} já existe. Atualizando e limpando associações antigas...")
        db.query(model.ProdutoMarca).filter(model.ProdutoMarca.produto_id == codigo_produto).delete(synchronize_session=False)
        db.query(model.ProdutoNutriente).filter(model.ProdutoNutriente.produto_id == codigo_produto).delete(synchronize_session=False)
        db.query(model.ProdutoIngrediente).filter(model.ProdutoIngrediente.produto_id == codigo_produto).delete(synchronize_session=False)
        db.query(model.ProdutoTag).filter(model.ProdutoTag.produto_id == codigo_produto).delete(synchronize_session=False)
        db.query(model.ProdutoCategoria).filter(model.ProdutoCategoria.produto_id == codigo_produto).delete(synchronize_session=False)
        db.flush()
        produto_existente.nome = produto_data_dict["nome"]
        produto_existente.nutriscore = produto_data_dict["nutriscore"]
        produto_existente.ecoscore = produto_data_dict["ecoscore"]
        produto_existente.novascore = produto_data_dict["novascore"]
        produto_obj = produto_existente
    else:
        print(f"INFO: Criando novo produto: {codigo_produto}")
        produto_obj = model.Produto(**produto_data_dict)
        db.add(produto_obj)
    if transformed_data.get("marca_nome"):
        marca_obj = get_or_create_marca(db, transformed_data["marca_nome"])
        if marca_obj: db.add(model.ProdutoMarca(produto=produto_obj, marca=marca_obj))
    for nome_cat in transformed_data.get("categorias_nomes", []):
        cat_obj = get_or_create_categoria(db, nome_cat)
        if cat_obj: db.add(model.ProdutoCategoria(produto=produto_obj, categoria=cat_obj))
    for tag_data in transformed_data.get("tags", []):
        tag_obj = get_or_create_tag(db, tag_data["nome"], tag_data["tipo"])
        if tag_obj: db.add(model.ProdutoTag(produto=produto_obj, tag=tag_obj))
    for nutri_prod_data in transformed_data.get("nutrientes_produto", []):
        nutriente_obj = get_or_create_nutriente(db, nutri_prod_data["nome_nutriente"], nutri_prod_data["unidade_nutriente"])
        if nutriente_obj:
            db.add(model.ProdutoNutriente(
                produto=produto_obj, nutriente=nutriente_obj,
                quantidade_100g=nutri_prod_data["quantidade_100g"]
            ))
    for ing_prod_data in transformed_data.get("ingredientes_produto", []):
        ingrediente_obj = get_or_create_ingrediente_by_name(
            db, ing_prod_data["nome_ingrediente"],
            ing_prod_data["vegano"], ing_prod_data["vegetariano"]
        )
        if ingrediente_obj:
            assoc_exists = db.query(model.ProdutoIngrediente).filter_by(
                produto_id=produto_obj.codigo, ingrediente_id=ingrediente_obj.id
            ).first()
            if not assoc_exists:
                db.add(model.ProdutoIngrediente(
                    produto=produto_obj, ingrediente=ingrediente_obj,
                    quantidade_estimada=ing_prod_data["quantidade_estimada"]
                ))
            else:
                print(f"DEBUG: Associação Produto-Ingrediente já existe para produto {produto_obj.codigo} e ingrediente {ingrediente_obj.nome}. Pulando.")
    print(f"INFO: Dados para produto {codigo_produto} preparados para commit.")