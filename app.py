import streamlit as st
import pandas as pd

# ==========================================
# 1. TABELAS DE CONVERSÃO (NORMA ABNT)
# ==========================================
# Tabela 17 - Conversão de Categoria para Valor Numérico (Estimativa Pontual)
CONVERSAO_ATE = {
    'oral': {'1': 0.5, '2': 5, '3': 100, '4': 500, '5': 2500, 'NC': None},
    'dermica': {'1': 5, '2': 50, '3': 300, '4': 1100, '5': 2500, 'NC': None},
    'inalacao': {'1': 0.05, '2': 0.5, '3': 3, '4': 11, 'NC': None} # Vapores
}

# ==========================================
# 2. ESTRUTURA DE DADOS
# ==========================================
class Ingrediente:
    def __init__(self, nome, concentracao, 
                 # Saúde
                 ate_oral_val=None, ate_oral_cat='NC', # Valor ou Categoria
                 cat_pele='NC', cat_olho='NC',
                 cat_resp_sens='NC', cat_pele_sens='NC',
                 cat_muta='NC', cat_carc='NC', cat_repro='NC', 
                 cat_stot_se='NC', cat_stot_re='NC',
                 # Ambiental
                 cat_aq_agudo='None', cat_aq_cronico='None',
                 fator_m_agudo=1, fator_m_cronico=1,
                 # Físicos (Propriedades intrínsecas para alerta)
                 fisico_autoaquecimento='NC'):
        
        self.nome = nome
        self.c = float(concentracao)
        
        # Lógica Híbrida para ATE: Se usuário deu valor, usa valor. Se deu Categoria, converte.
        if ate_oral_val and ate_oral_val > 0:
            self.ate_oral = ate_oral_val
        else:
            self.ate_oral = CONVERSAO_ATE['oral'].get(ate_oral_cat)

        self.cat_pele = cat_pele
        self.cat_olho = cat_olho
        self.cat_resp_sens = cat_resp_sens
        self.cat_pele_sens = cat_pele_sens
        self.cat_muta = cat_muta
        self.cat_carc = cat_carc
        self.cat_repro = cat_repro
        self.cat_stot_se = cat_stot_se
        self.cat_stot_re = cat_stot_re
        
        # Conversão de categorias ambientais para números inteiros para cálculo
        self.cat_aq_agudo = int(cat_aq_agudo) if cat_aq_agudo != 'None' else None
        self.cat_aq_cronico = int(cat_aq_cronico) if cat_aq_cronico != 'None' else None
        self.fator_m_agudo = int(fator_m_agudo)
        self.fator_m_cronico = int(fator_m_cronico)
        
        self.fisico_autoaquecimento = fisico_autoaquecimento

# ==========================================
# 3. MOTOR GHS (LÓGICA EXTRAÍDA DA NORMA)
# ==========================================
class MotorGHS:
    def __init__(self, ingredientes, dados_mistura):
        self.ingredientes = ingredientes
        self.mistura = dados_mistura

    # --- PERIGOS FÍSICOS (Seção 5.2) ---
    def classificar_fisicos(self):
        res = {}
        
        # 1. Líquidos Inflamáveis (Tabela 6)
        fp = self.mistura.get('flash_point')
        bp = self.mistura.get('boiling_point')
        
        if fp is not None and bp is not None:
            if fp < 23 and bp <= 35: res['Líquido Inflamável'] = 'Categoria 1'
            elif fp < 23 and bp > 35: res['Líquido Inflamável'] = 'Categoria 2'
            elif 23 <= fp <= 60: res['Líquido Inflamável'] = 'Categoria 3'
            elif 60 < fp <= 93: res['Líquido Inflamável'] = 'Categoria 4'
            else: res['Líquido Inflamável'] = 'NC'
        else:
            res['Líquido Inflamável'] = 'NC (Dados insuficientes)'

        # 2. Corrosivo Metais (Taxa > 6.25mm/ano)
        corr = self.mistura.get('corrosion_rate')
        if corr and corr > 6.25:
            res['Corrosivo p/ Metais'] = 'Categoria 1'
        else:
            res['Corrosivo p/ Metais'] = 'NC'
            
        # 3. Autoaquecimento (Herança de Risco - Ditionito)
        if any(i.fisico_autoaquecimento == '1' for i in self.ingredientes):
            res['Autoaquecimento'] = 'Categoria 1 (Alerta: Ingrediente Cat 1 presente)'
        else:
            res['Autoaquecimento'] = 'NC'

        return res

    # --- PERIGOS À SAÚDE (Seção 5.3) ---
    def classificar_saude(self):
        res = {}
        
        # 1. Toxicidade Aguda Oral (Fórmula Harmônica)
        soma_fracao = 0
        conc_desconhecida = 0
        for i in self.ingredientes:
            if i.ate_oral:
                soma_fracao += (i.c / i.ate_oral)
            else:
                conc_desconhecida += i.c
        
        if soma_fracao > 0:
            base = 100 - conc_desconhecida if conc_desconhecida > 10 else 100
            ate_mix = base / soma_fracao
            
            # Tabela 16 - Faixas
            cat = 'NC'
            if ate_mix <= 5: cat = 'Categoria 1'
            elif ate_mix <= 50: cat = 'Categoria 2'
            elif ate_mix <= 300: cat = 'Categoria 3'
            elif ate_mix <= 2000: cat = 'Categoria 4'
            elif ate_mix <= 5000: cat = 'Categoria 5'
            res['Tox. Aguda Oral'] = f"{cat} (ATEmix: {ate_mix:.1f} mg/kg)"
        else:
            res['Tox. Aguda Oral'] = "NC"

        # 2. Corrosão Pele (Soma Ponderada)
        ph = self.mistura.get('ph')
        if ph is not None and (ph <= 2 or ph >= 11.5):
            res['Pele'] = 'Categoria 1 (pH Extremo)'
        else:
            # Filtra somas
            s1 = sum(i.c for i in self.ingredientes if i.cat_pele in ['1', '1A', '1B', '1C'])
            s2 = sum(i.c for i in self.ingredientes if i.cat_pele == '2')
            s3 = sum(i.c for i in self.ingredientes if i.cat_pele == '3')
            
            if s1 >= 5: res['Pele'] = 'Categoria 1'
            elif s1 >= 1 or s2 >= 10 or (10*s1 + s2) >= 10: res['Pele'] = 'Categoria 2'
            elif s3 >= 10 or (10*s1 + s2 + s3) >= 10: res['Pele'] = 'Categoria 3'
            else: res['Pele'] = 'NC'

        # 3. Olhos (Precedência Pele Cat 1)
        if 'Categoria 1' in res.get('Pele', ''):
            res['Olhos'] = 'Categoria 1 (Devido à Pele)'
        else:
            # Soma: Pele Cat 1 conta como Olho Cat 1
            s1 = sum(i.c for i in self.ingredientes if i.cat_olho == '1' or i.cat_pele in ['1', '1A', '1B', '1C'])
            s2 = sum(i.c for i in self.ingredientes if i.cat_olho in ['2', '2A', '2B'])
            
            if s1 >= 3: res['Olhos'] = 'Categoria 1'
            elif s1 >= 1 or s2 >= 10 or (10*s1 + s2) >= 10: res['Olhos'] = 'Categoria 2A'
            else: res['Olhos'] = 'NC'

        # 4. CMR e STOT (Limites de Corte)
        # Carcinogenicidade
        if any(i.cat_carc in ['1', '1A', '1B'] and i.c >= 0.1 for i in self.ingredientes): res['Carcinogenicidade'] = 'Categoria 1'
        elif any(i.cat_carc == '2' and i.c >= 1.0 for i in self.ingredientes): res['Carcinogenicidade'] = 'Categoria 2' # Pode configurar para 0.1%
        else: res['Carcinogenicidade'] = 'NC'
        
        # STOT Única
        if any(i.cat_stot_se == '1' and i.c >= 10.0 for i in self.ingredientes): res['STOT SE'] = 'Categoria 1'
        elif any((i.cat_stot_se == '1' and 1.0 <= i.c < 10.0) or (i.cat_stot_se == '2' and i.c >= 10.0) for i in self.ingredientes): res['STOT SE'] = 'Categoria 2'
        elif any(i.cat_stot_se == '3' and i.c >= 20.0 for i in self.ingredientes): res['STOT SE'] = 'Categoria 3'
        else: res['STOT SE'] = 'NC'

        return res

    # --- PERIGOS AMBIENTAIS (Seção 5.4 - Fator M) ---
    def classificar_ambiental(self):
        res = {}
        
        # Agudo: Soma(Conc * M) >= 25%
        soma_aguda_1 = sum(i.c * i.fator_m_agudo for i in self.ingredientes if i.cat_aq_agudo == 1)
        soma_aguda_2 = sum(i.c for i in self.ingredientes if i.cat_aq_agudo == 2)
        soma_aguda_3 = sum(i.c for i in self.ingredientes if i.cat_aq_agudo == 3)

        if soma_aguda_1 >= 25: res['Aquático Agudo'] = 'Categoria 1'
        elif (soma_aguda_1 * 10 + soma_aguda_2) >= 25: res['Aquático Agudo'] = 'Categoria 2'
        elif (soma_aguda_1 * 100 + soma_aguda_2 * 10 + soma_aguda_3) >= 25: res['Aquático Agudo'] = 'Categoria 3'
        else: res['Aquático Agudo'] = 'NC'

        # Crônico
        soma_cron_1 = sum(i.c * i.fator_m_cronico for i in self.ingredientes if i.cat_aq_cronico == 1)
        soma_cron_2 = sum(i.c for i in self.ingredientes if i.cat_aq_cronico == 2)
        soma_cron_3 = sum(i.c for i in self.ingredientes if i.cat_aq_cronico == 3)
        soma_cron_4 = sum(i.c for i in self.ingredientes if i.cat_aq_cronico == 4)

        if soma_cron_1 >= 25: res['Aquático Crônico'] = 'Categoria 1'
        elif (soma_cron_1 * 10 + soma_cron_2) >= 25: res['Aquático Crônico'] = 'Categoria 2'
        elif (soma_cron_1 * 100 + soma_cron_2 * 10 + soma_cron_3) >= 25: res['Aquático Crônico'] = 'Categoria 3'
        elif (soma_cron_1 + soma_cron_2 + soma_cron_3 + soma_cron_4) >= 25: res['Aquático Crônico'] = 'Categoria 4'
        else: res['Aquático Crônico'] = 'NC'

        return res

    def executar_analise(self):
        r1 = self.classificar_fisicos()
        r2 = self.classificar_saude()
        r3 = self.classificar_ambiental()
        return {**r1, **r2, **r3}

# ==========================================
# 4. INTERFACE STREAMLIT
# ==========================================
st.set_page_config(page_title="GHS Pro ABNT", layout="wide")
st.title("🛡️ Classificador GHS Profissional - ABNT NBR 14725")

if 'ingredientes' not in st.session_state:
    st.session_state.ingredientes = []

# --- COLUNA LATERAL: CADASTRO ---
with st.sidebar:
    st.header("1. Cadastro de Ingrediente")
    nome = st.text_input("Nome da Substância", "Ex: Ditionito de Sódio")
    conc = st.number_input("Concentração (%)", 0.0, 100.0, 10.0, step=0.1)
    
    t1, t2, t3 = st.tabs(["☠️ Saúde", "🐟 Ambiental", "🔥 Físicos"])
    
    with t1:
        st.markdown("**Toxicidade Aguda**")
        tipo_dado = st.radio("Dado disponível:", ["Categoria GHS", "Valor Numérico (DL50)"])
        
        ate_o_val = 0.0
        ate_o_cat = 'NC'
        
        if tipo_dado == "Valor Numérico (DL50)":
            ate_o_val = st.number_input("DL50 Oral (mg/kg)", 0.0)
        else:
            ate_o_cat = st.selectbox("Categoria Oral", ['NC', '1', '2', '3', '4', '5'])
            
        st.markdown("**Outros Perigos**")
        pele = st.selectbox("Pele", ['NC', '1A', '1B', '1C', '2', '3'])
        olho = st.selectbox("Olhos", ['NC', '1', '2A', '2B'])
        carc = st.selectbox("Carcinogenicidade", ['NC', '1A', '1B', '2'])
        stot = st.selectbox("STOT Única", ['NC', '1', '2', '3'])

    with t2:
        agudo = st.selectbox("Aq. Agudo", ['None', '1', '2', '3'])
        m_ag = st.number_input("Fator M (Agudo)", 1, 10000, 1)
        cronico = st.selectbox("Aq. Crônico", ['None', '1', '2', '3', '4'])
        m_cr = st.number_input("Fator M (Crônico)", 1, 10000, 1)

    with t3:
        autoaq = st.selectbox("Autoaquecimento", ['NC', '1', '2'])

    if st.button("➕ Adicionar Ingrediente"):
        novo = Ingrediente(
            nome, conc, 
            ate_oral_val=ate_o_val, ate_oral_cat=ate_o_cat,
            cat_pele=pele, cat_olho=olho, cat_carc=carc, cat_stot_se=stot,
            cat_aq_agudo=agudo, cat_aq_cronico=cronico, 
            fator_m_agudo=m_ag, fator_m_cronico=m_cr,
            fisico_autoaquecimento=autoaq
        )
        st.session_state.ingredientes.append(novo)
        st.success("Adicionado!")

# --- ÁREA PRINCIPAL ---
c1, c2 = st.columns([1.5, 1])

with c1:
    st.subheader("2. Composição da Mistura")
    if st.session_state.ingredientes:
        df = pd.DataFrame([{
            'Nome': i.nome, 
            '%': i.c, 
            'Pele': i.cat_pele, 
            'Aq. Agudo': i.cat_aq_agudo,
            'Fator M': i.fator_m_agudo
        } for i in st.session_state.ingredientes])
        st.dataframe(df, use_container_width=True)
        
        if st.button("Limpar Lista"):
            st.session_state.ingredientes = []
            st.rerun()
            
    st.subheader("3. Dados Físicos da Mistura (Opcional)")
    with st.expander("Preencher se houver testes da mistura"):
        ph = st.number_input("pH", 0.0, 14.0, 7.0)
        fp = st.number_input("Ponto de Fulgor (°C)", value=None, placeholder="Vazio se não testado")
        bp = st.number_input("Ponto de Ebulição (°C)", value=None)
        corr = st.number_input("Taxa Corrosão Aço (mm/ano)", 0.0)

with c2:
    st.subheader("4. Classificação Final")
    if st.button("🚀 Processar ABNT 14725", type="primary"):
        if not st.session_state.ingredientes:
            st.warning("Adicione ingredientes.")
        else:
            # Monta dados da mistura
            dados_mix = {
                'ph': ph, 
                'flash_point': fp, 
                'boiling_point': bp, 
                'corrosion_rate': corr
            }
            
            motor = MotorGHS(st.session_state.ingredientes, dados_mix)
            resultado = motor.executar_analise()
            
            for perigo, classe in resultado.items():
                cor = "green" if "NC" in classe else "red"
                st.markdown(f"**{perigo}:** :{cor}[{classe}]")
