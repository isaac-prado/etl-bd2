# main.py
import traceback
from sqlalchemy.orm import Session

DATABASE_URL = "postgresql://seu_usuario:sua_senha@seu_host:5432/seu_banco"
API_BASE_URL_PARA_EXTRACT = "https_url_da_sua_api_aqui" # Ex: "https://world.openfoodfacts.net/api/v2"


from database import get_db_session, engine as db_engine
import model
from etl import extract
from etl import transform
from etl import load


def process_product_etl(product_code_to_fetch: str, db: Session, api_base_url: str):
    print(f"INFO: --- Iniciando ETL para o código solicitado: {product_code_to_fetch} ---")
    
    # Passa a api_base_url para a função de extração
    api_data = extract.fetch_product_data_from_api(product_code_to_fetch, api_base_url)
    if not api_data:
        print(f"ERROR: Falha na extração para {product_code_to_fetch}. ETL interrompido para este produto.")
        return False

    transformed_data = transform.transform_api_data(api_data, product_code_to_fetch)
    if not transformed_data:
        print(f"ERROR: Falha na transformação para {product_code_to_fetch}. ETL interrompido para este produto.")
        return False

    try:
        load.load_data_to_db(db, transformed_data)
        return True
    except Exception as e: 
        print(f"ERROR: Erro CRÍTICO durante a fase de carga para o produto originado do código {product_code_to_fetch}: {e}")
        traceback.print_exc()
        return False

def run_etl_pipeline():
    print(f"INFO: === INICIANDO PROCESSO ETL COMPLETO ===")

    product_codes_to_process = [
        "3155250349793", 
        "7622210449283", 
        "3017620422003",
        "000000000000000", # Código que provavelmente não existe
    ] 
    print(f"DEBUG: Códigos a processar: {product_codes_to_process}")
    if not product_codes_to_process:
        print(f"WARN: Lista de códigos de produto está vazia. Nada a fazer.")
        return

    db_session_generator = get_db_session(DATABASE_URL) # Passa a DATABASE_URL para configurar a sessão
    db: Session = next(db_session_generator)

    successful_products_codes = []
    failed_products_codes = []

    for code in product_codes_to_process:
        try:
            # Passa a API_BASE_URL_PARA_EXTRACT para a função de processamento
            was_preparation_successful = process_product_etl(code, db, API_BASE_URL_PARA_EXTRACT)
            
            if was_preparation_successful:
                db.commit()
                print(f"INFO: COMMIT realizado com sucesso para o produto originado do código: {code}")
                successful_products_codes.append(code)
            else:
                db.rollback()
                print(f"WARN: ROLLBACK realizado para o produto originado do código: {code} devido a falha no ETL.")
                failed_products_codes.append(code)
        except Exception as e: 
            print(f"ERROR: Erro INESPERADO no loop principal para o produto originado do código {code}: {e}")
            traceback.print_exc()
            try:
                db.rollback()
                print(f"WARN: ROLLBACK realizado para o produto {code} devido a erro inesperado.")
            except Exception as rb_exc:
                print(f"ERROR: Erro ao tentar realizar ROLLBACK para {code} após erro inesperado: {rb_exc}")
            failed_products_codes.append(code)
        finally:
            print(f"INFO: --- Finalizado processamento ETL para o código solicitado: {code} ---")
            
    print(f"INFO: === PROCESSO ETL COMPLETO FINALIZADO ===")
    print(f"INFO: Total de produtos processados com sucesso (commit): {len(successful_products_codes)}")
    if successful_products_codes: print(f"INFO: Códigos de produtos com sucesso: {', '.join(successful_products_codes)}")
    if failed_products_codes:
        print(f"WARN: Total de produtos com falha no processamento: {len(failed_products_codes)}")
        print(f"WARN: Códigos de produtos com falha: {', '.join(failed_products_codes)}")
    
    try:
        next(db_session_generator) # Fecha a sessão do banco
    except StopIteration:
        pass 
    except Exception as e:
        print(f"ERROR: Erro ao fechar a sessão do banco de dados: {e}")

if __name__ == "__main__":
    print("DEBUG: main.py - Script iniciado, entrando no bloco __main__")
    if DATABASE_URL == "postgresql://seu_usuario:sua_senha@seu_host:5432/seu_banco" or not DATABASE_URL:
        print("CRITICAL_ERROR: A constante DATABASE_URL não foi alterada neste arquivo (main.py)! Edite-a com seus dados.")
        exit(1)
    if API_BASE_URL_PARA_EXTRACT == "https_url_da_sua_api_aqui" or not API_BASE_URL_PARA_EXTRACT:
        print("CRITICAL_ERROR: A constante API_BASE_URL_PARA_EXTRACT não foi alterada neste arquivo (main.py)! Edite-a com a URL da API.")
        exit(1)
    
    print("DEBUG: Constantes DATABASE_URL e API_BASE_URL_PARA_EXTRACT parecem definidas. Chamando run_etl_pipeline()")
    run_etl_pipeline()
    print("DEBUG: run_etl_pipeline() concluído.")