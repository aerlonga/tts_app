from google import genai
import sys

# Insira sua chave aqui para testar ou passe via linha de comando
API_KEY = ""

def list_my_models(api_key):
    try:
        client = genai.Client(api_key=api_key)
        print("\n--- Modelos Disponíveis para sua Chave ---\n")
        
        # Filtra por modelos que suportam geração de conteúdo
        for model in client.models.list():
            # Na nova SDK, o atributo costuma ser supported_generation_methods ou simplesmente listamos o nome
            print(f"ID: {model.name}")
            print(f"Nome: {model.display_name}")
            if hasattr(model, 'supported_generation_methods'):
                print(f"Metodos: {', '.join(model.supported_generation_methods)}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Erro ao listar modelos: {e}")

if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else API_KEY
    if key == "SUA_CHAVE_AQUI":
        print("Por favor, rode o comando assim: python list_models.py SUA_API_KEY_AQUI")
    else:
        list_my_models(key)
