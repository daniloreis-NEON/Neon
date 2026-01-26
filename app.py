import openai # ou google.generativeai
import pandas as pd

# 1. Carregar sua lista
df = pd.read_excel("lista_fluidos.xlsx")

def consultar_compatibilidade(substancia):
    prompt = f"""
    Analise a compatibilidade química de: {substancia}.
    Para vedações de: EPDM e VITON (FKM).
    Responda estritamente neste formato:
    EPDM: [Excelente/Bom/Ruim/Não Usar]
    VITON: [Excelente/Bom/Ruim/Não Usar]
    """
    
    # Chamada fictícia à API
    resposta = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return resposta.choices[0].message.content

# 2. Loop para preencher a tabela
for index, row in df.iterrows():
    resultado = consultar_compatibilidade(row['Nome_Substancia'])
    print(f"Processando {row['Nome_Substancia']}...")
    # Aqui você salvaria o resultado na coluna nova
