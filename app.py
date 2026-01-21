import streamlit as st

# --- CLASSE PARA REPRESENTAR CADA SUBSTÂNCIA ---
class Ingrediente:
    def __init__(self, nome, concentracao, 
                 ate_oral=None, ate_dermica=None, ate_inalacao=None,
                 cat_pele=None, cat_olho=None,
                 cat_resp_sens=None, cat_pele_sens=None,
                 cat_muta=None, cat_carc=None, cat_repro=None, 
                 cat_stot_se=None, cat_stot_re=None,
                 cat_aquatico_agudo=None, cat_aquatico_cronico=None,
                 fator_m_agudo=1, fator_m_cronico=1):
        
        self.nome = nome
        self.c = float(concentracao) # Porcentagem (0-100)
        
        # Toxicidade Aguda (Valores numéricos DL50)
        self.ate_oral = ate_oral
        self.ate_dermica = ate_dermica
        self.ate_inalacao = ate_inalacao
        
        # Classificações Físicas/Saúde (Texto: '1A', '2', 'NC')
        self.cat_pele = str(cat_pele).upper() if cat_pele else 'NC'
        self.cat_olho = str(cat_olho).upper() if cat_olho else 'NC'
        
        # Classificações Crônicas
        self.cat_muta = str(cat_muta).upper() if cat_muta else 'NC'
        self.cat_carc = str(cat_carc).upper() if cat_carc else 'NC'
        self.cat_repro = str(cat_repro).upper() if cat_repro else 'NC'
        self.cat_stot_se = str(cat_stot_se).upper() if cat_stot_se else 'NC'
        self.cat_stot_re = str(cat_stot_re).upper() if cat_stot_re else 'NC'

        # Ambiental (Inteiros: 1, 2, 3...)
        self.cat_aquatico_agudo = int(cat_aquatico_agudo) if cat_aquatico_agudo else None
        self.cat_aquatico_cronico = int(cat_aquatico_cronico) if cat_aquatico_cronico else None
        self.fator_m_agudo = int(fator_m_agudo)
        self.fator_m_cronico = int(fator_m_cronico)

# --- O MOTOR DE CÁLCULO GHS (LÓGICA ABNT 14725) ---
class ClassificadorGHS:
    def __init__(self, mistura):
        self.ingredientes = mistura

    # 1. TOXICIDADE AGUDA (Fórmula de Aditividade)
    def calcular_ate_mix(self, via):
        soma_fracao = 0
        concentracao_desconhecida = 0

        for ing in self.ingredientes:
            valor_ate = getattr(ing, f'ate_{via}')
            if valor_ate is not None and valor_ate > 0:
                soma_fracao += (ing.c / valor_ate)
            else:
                concentracao_desconhecida += ing.c
        
        if soma_fracao == 0: return "Dados Insuficientes"

        # Ajuste se desconhecidos > 10%
        base_calculo = 100 - concentracao_desconhecida if concentracao_desconhecida > 10 else 100
        ate_mix = base_calculo / soma_fracao
        return round(ate_mix, 2)

    # 2. PELE
    def classificar_pele(self):
        soma_cat1 = sum([i.c for i in self.ingredientes if i.cat_pele in ['1', '1A', '1B', '1C']])
        soma_cat2 = sum([i.c for i in self.ingredientes if i.cat_pele == '2'])
        soma_cat3 = sum([i.c for i in self.ingredientes if i.cat_pele == '3'])

        if soma_cat1 >= 5.0: return "Categoria 1 (Corrosivo)"
        if soma_cat1 >= 1.0 or soma_cat2 >= 10.0 or (10*soma_cat1 + soma_cat2) >= 10.0: return "Categoria 2 (Irritante)"
        if soma_cat3 >= 10.0 or (10*soma_cat1 + soma_cat2 + soma_cat3) >= 10.0: return "Categoria 3 (Irritante Leve)"
        return "Não Classificado"

    # 3. OLHOS
    def classificar_olhos(self):
        soma_cat1 = sum([i.c for i in self.ingredientes if i.cat_olho == '1' or i.cat_pele in ['1', '1A', '1B', '1C']])
        soma_cat2 = sum([i.c for i in self.ingredientes if i.cat_olho in ['2', '2A', '2B']])

        if soma_cat1 >= 3.0: return "Categoria 1 (Lesão Grave)"
        if soma_cat1 >= 1.0 or soma_cat2 >= 10.0 or (10*soma_cat1 + soma_cat2) >= 10.0: return "Categoria 2 (Irritante Ocular)"
        return "Não Classificado"

    # 4. AMBIENTAL
    def classificar_ambiental(self):
        # Agudo
        soma_aguda_1 = sum([i.c * i.fator_m_agudo for i in self.ingredientes if i.cat_aquatico_agudo == 1])
        soma_aguda_2 = sum([i.c for i in self.ingredientes if i.cat_aquatico_agudo == 2])
        
        res_agudo = "Não Classificado"
        if soma_aguda_1 >= 25.0: res_agudo = "Agudo 1"
        elif (soma_aguda_1 * 10 + soma_aguda_2) >= 25.0: res_agudo = "Agudo 2"

        # Crônico
        soma_cron_1 = sum([i.c * i.fator_m_cronico for i in self.ingredientes if i.cat_aquatico_cronico == 1])
        soma_cron_2 = sum([i.c for i in self.ingredientes if i.cat_aquatico_cronico == 2])
        
        res_cronico = "Não Classificado"
        if soma_cron_1 >= 25.0: res_cronico = "Crônico 1"
        elif (soma_cron_1 * 10 + soma_cron_2) >= 25.0: res_cronico = "Crônico 2"

        return f"{res_agudo} / {res_cronico}"

    def executar_tudo(self):
        return {
            "Toxicidade Aguda (Oral)": self.calcular_ate_mix('oral'),
            "Corrosão/Irritação Pele": self.classificar_pele(),
            "Lesões/Irritação Ocular": self.classificar_olhos(),
            "Perigo ao Meio Ambiente": self.classificar_ambiental()
        }

# --- INTERFACE VISUAL (STREAMLIT) ---
st.set_page_config(page_title="GHS Calculator", layout="wide")

st.title("🧪 Classificador de Misturas GHS (ABNT 14725)")
st.markdown("Adicione os ingredientes na barra lateral e clique em calcular.")

# Inicializa a lista de ingredientes na memória
if 'lista_ingredientes' not in st.session_state:
    st.session_state.lista_ingredientes = []

# --- BARRA LATERAL (ENTRADA DE DADOS) ---
with st.sidebar:
    st.header("Adicionar Ingrediente")
    nome = st.text_input("Nome do Químico", "Ex: Ácido Sulfúrico")
    conc = st.number_input("Concentração (%)", 0.0, 100.0, step=0.1)
    
    with st.expander("Dados de Toxicidade (Saúde)"):
        ate_oral = st.number_input("DL50 Oral (mg/kg)", 0.0)
        cat_pele = st.selectbox("Categoria Pele", ["NC", "1A", "1B", "1C", "2", "3"])
        cat_olho = st.selectbox("Categoria Olhos", ["NC", "1", "2A", "2B"])
        cat_carc = st.selectbox("Carcinogenicidade", ["NC", "1A", "1B", "2"])

    with st.expander("Dados Ambientais"):
        cat_aq_agudo = st.selectbox("Aquático Agudo (Cat)", ["None", "1", "2", "3"])
        fator_m = st.number_input("Fator M (Agudo)", 1, 10000, 1)
        cat_aq_cronico = st.selectbox("Aquático Crônico (Cat)", ["None", "1", "2", "3", "4"])
        fator_m_cr = st.number_input("Fator M (Crônico)", 1, 10000, 1)

    if st.button("➕ Adicionar à Mistura"):
        # Converte selects para formato do motor
        c_aq_ag = int(cat_aq_agudo) if cat_aq_agudo != "None" else None
        c_aq_cr = int(cat_aq_cronico) if cat_aq_cronico != "None" else None
        
        novo_ingrediente = Ingrediente(
            nome=nome, concentracao=conc, ate_oral=ate_oral,
            cat_pele=cat_pele, cat_olho=cat_olho, cat_carc=cat_carc,
            cat_aquatico_agudo=c_aq_ag, cat_aquatico_cronico=c_aq_cr,
            fator_m_agudo=fator_m, fator_m_cronico=fator_m_cr
        )
        st.session_state.lista_ingredientes.append(novo_ingrediente)
        st.success(f"{nome} adicionado!")

# --- TELA PRINCIPAL (RESULTADOS) ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Composição da Mistura")
    if st.session_state.lista_ingredientes:
        dados_tabela = []
        soma_conc = 0
        for i in st.session_state.lista_ingredientes:
            dados_tabela.append([i.nome, f"{i.c}%", i.cat_pele, i.ate_oral])
            soma_conc += i.c
        
        st.table(dados_tabela)
        st.caption(f"Soma das concentrações: {soma_conc}%")
        
        if st.button("🗑️ Limpar Mistura"):
            st.session_state.lista_ingredientes = []
            st.rerun()
    else:
        st.info("Nenhum ingrediente adicionado ainda.")

with col2:
    st.subheader("Resultado da Classificação")
    if st.button("🚀 Calcular Classificação ABNT"):
        if st.session_state.lista_ingredientes:
            motor = ClassificadorGHS(st.session_state.lista_ingredientes)
            resultado = motor.executar_tudo()
            
            st.success("Cálculo Realizado!")
            for perigo, classif in resultado.items():
                st.metric(label=perigo, value=str(classif))
        else:
            st.error("Adicione ingredientes antes de calcular.")
