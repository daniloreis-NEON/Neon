Compreendo sua frustração. Você tem razão: para Ácido Sulfúrico (e ácidos em geral), a classificação não depende apenas da soma de toxicidade, mas crucialmente do pH e da Taxa de Corrosão em Metais. Se o código não olhar para isso, ele erra feio.

O código anterior estava focado demais na lógica de "soma de ingredientes" (que serve para Ditionito), mas a ABNT NBR 14725 exige uma Abordagem em Etapas (Tiered Approach).

Para funcionar para 3.000 substâncias, o sistema precisa aceitar dois tipos de dados:

Dados da Mistura (Prioridade Máxima): pH, Ponto de Fulgor, Taxa de Corrosão. (Isso resolve o Ácido Sulfúrico).

Dados dos Ingredientes (Cálculo): Para quando você não tem o teste da mistura.

Reescrevi o código COMPLETO. Ele agora contempla Corrosivo para Metais, a Regra do pH Extremo (fundamental para ácidos) e os Fatores M ambientais.

Copie e substitua no seu app.py.

Python
import streamlit as st
import pandas as pd

# ==========================================
# 1. TABELAS E CONSTANTES (ABNT NBR 14725)
# ==========================================

# Tabela 17 - Conversão de Categoria para Estimativa Pontual (ATE)
# Usado quando você só sabe a categoria do ingrediente, mas precisa calcular a mistura
CONVERSAO_ATE = {
    'oral': {'1': 0.5, '2': 5, '3': 100, '4': 500, '5': 2500, 'NC': None},
    'dermica': {'1': 5, '2': 50, '3': 300, '4': 1100, '5': 2500, 'NC': None},
    'inalacao_vapores': {'1': 0.05, '2': 0.5, '3': 3, '4': 11, 'NC': None},
    'inalacao_poeiras': {'1': 0.005, '2': 0.05, '3': 0.5, '4': 1.5, 'NC': None}
}

# ==========================================
# 2. CLASSE DE DADOS DO INGREDIENTE
# ==========================================
class Ingrediente:
    def __init__(self, nome, concentracao, 
                 # Saúde
                 ate_oral=None, ate_dermica=None, 
                 cat_pele='NC', cat_olho='NC',
                 cat_sens_resp='NC', cat_sens_pele='NC',
                 cat_muta='NC', cat_carc='NC', cat_repro='NC', cat_lact='NC',
                 cat_stot_se='NC', cat_stot_re='NC', cat_aspiracao='NC',
                 # Ambiental
                 cat_aq_agudo='None', cat_aq_cronico='None',
                 fator_m_agudo=1, fator_m_cronico=1,
                 # Físicos (Propriedades intrínsecas para herança de risco)
                 fisico_autoaquecimento='NC', fisico_solido_inf='NC', fisico_oxidante='NC'):
        
        self.nome = nome
        self.c = float(concentracao)
        
        # Normalização de Toxicidade Aguda
        self.ate_oral = ate_oral if ate_oral and ate_oral > 0 else None
        self.ate_dermica = ate_dermica if ate_dermica and ate_dermica > 0 else None
        
        # Categorias Saúde
        self.cat_pele = str(cat_pele).upper()
        self.cat_olho = str(cat_olho).upper()
        self.cat_sens_resp = cat_sens_resp
        self.cat_sens_pele = cat_sens_pele
        self.cat_muta = cat_muta
        self.cat_carc = cat_carc
        self.cat_repro = cat_repro
        self.cat_lact = cat_lact
        self.cat_stot_se = cat_stot_se
        self.cat_stot_re = cat_stot_re
        self.cat_aspiracao = cat_aspiracao

        # Categorias Ambientais (Convertendo para Inteiro para facilitar soma)
        self.cat_aq_agudo = int(cat_aq_agudo) if cat_aq_agudo != 'None' else None
        self.cat_aq_cronico = int(cat_aq_cronico) if cat_aq_cronico != 'None' else None
        self.fator_m_agudo = int(fator_m_agudo)
        self.fator_m_cronico = int(fator_m_cronico)
        
        # Físicos
        self.fisico_autoaquecimento = fisico_autoaquecimento
        self.fisico_solido_inf = fisico_solido_inf
        self.fisico_oxidante = fisico_oxidante

# ==========================================
# 3. MOTOR DE CÁLCULO (CORE LOGIC)
# ==========================================
class MotorGHS:
    def __init__(self, ingredientes, dados_mistura):
        self.ingredientes = ingredientes
        self.mistura = dados_mistura # Dicionário com dados físicos da mistura

    # --- BLOCO 1: PERIGOS FÍSICOS (Baseado na Mistura) ---
    def classificar_fisicos(self):
        res = {}
        
        # 1. Líquidos Inflamáveis (Seção 5.2.6 - Tabela 6)
        fp = self.mistura.get('flash_point')
        bp = self.mistura.get('boiling_point')
        
        if fp is not None and bp is not None:
            if fp < 23 and bp <= 35: res['Líquido Inflamável'] = 'Categoria 1 (H224)'
            elif fp < 23 and bp > 35: res['Líquido Inflamável'] = 'Categoria 2 (H225)'
            elif 23 <= fp <= 60: res['Líquido Inflamável'] = 'Categoria 3 (H226)'
            elif 60 < fp <= 93: res['Líquido Inflamável'] = 'Categoria 4 (H227)'
            else: res['Líquido Inflamável'] = 'NC'
        else:
            res['Líquido Inflamável'] = 'NC (Requer dados de FP e PE)'

        # 2. Corrosivo para Metais (Seção 5.2.16)
        # CRITÉRIO DA NORMA: Taxa de corrosão > 6.25 mm/ano a 55°C
        corr_rate = self.mistura.get('corrosion_rate')
        if corr_rate is not None and corr_rate > 6.25:
            res['Corrosivo p/ Metais'] = 'Categoria 1 (H290)'
        else:
            res['Corrosivo p/ Metais'] = 'NC'

        # 3. Herança de Riscos (Sólidos, Autoaquecimento, Oxidantes)
        # Como não há cálculo de mistura para estes, verificamos se há ingrediente perigoso presente
        if any(i.fisico_autoaquecimento != 'NC' for i in self.ingredientes):
            res['Autoaquecimento'] = 'ALERTA: Contém ingrediente Autoaquecido (Requer Teste N.4)'
        
        if any(i.fisico_solido_inf != 'NC' for i in self.ingredientes):
            res['Sólido Inflamável'] = 'ALERTA: Contém sólido inflamável (Requer Teste N.1)'
            
        if any(i.fisico_oxidante != 'NC' for i in self.ingredientes):
            res['Oxidante'] = 'ALERTA: Contém substância oxidante (Requer Teste O.1/O.2)'

        return res

    # --- BLOCO 2: PERIGOS À SAÚDE (Cálculos e Limites) ---
    def classificar_saude(self):
        res = {}

        # A. Toxicidade Aguda (Fórmula Harmônica)
        def calc_ate_mix(via):
            soma_inv = 0
            conc_desc = 0
            for i in self.ingredientes:
                val = getattr(i, f'ate_{via}')
                if val: soma_inv += (i.c / val)
                else: conc_desc += i.c
            
            if soma_inv == 0: return "NC"
            
            # Fórmula ABNT: Ajuste se desconhecidos > 10%
            numerador = 100 - conc_desc if conc_desc > 10 else 100
            if numerador <= 0: return "NC (Dados insuficientes)"
            
            ate_mix = numerador / soma_inv
            return ate_mix

        # Oral
        ate_oral = calc_ate_mix('oral')
        if isinstance(ate_oral, float):
            cat = 'NC'
            if ate_oral <= 5: cat = 'Categoria 1 (H300)'
            elif ate_oral <= 50: cat = 'Categoria 2 (H300)'
            elif ate_oral <= 300: cat = 'Categoria 3 (H301)'
            elif ate_oral <= 2000: cat = 'Categoria 4 (H302)'
            elif ate_oral <= 5000: cat = 'Categoria 5 (H303)'
            res['Tox. Aguda Oral'] = f"{cat} (ATEmix: {ate_oral:.1f})"
        else:
            res['Tox. Aguda Oral'] = "NC"

        # B. Corrosão/Irritação (Regras de Prioridade e Soma)
        ph = self.mistura.get('ph')
        
        # 1. REGRA DO PH EXTREMO (Crucial para Ácidos/Bases)
        if ph is not None and (ph <= 2 or ph >= 11.5):
            res['Pele'] = 'Categoria 1 (Baseado em pH Extremo - H314)'
            res['Olhos'] = 'Categoria 1 (Baseado em pH Extremo - H318)'
        else:
            # 2. Soma Ponderada Pele
            s1 = sum(i.c for i in self.ingredientes if i.cat_pele in ['1', '1A', '1B', '1C'])
            s2 = sum(i.c for i in self.ingredientes if i.cat_pele == '2')
            
            if s1 >= 5: res['Pele'] = 'Categoria 1 (H314)'
            elif s1 >= 1 or s2 >= 10 or (10*s1 + s2) >= 10: res['Pele'] = 'Categoria 2 (H315)'
            elif (10*s1 + s2) >= 10: res['Pele'] = 'Categoria 3 (H316)' 
            else: res['Pele'] = 'NC'

            # 3. Soma Ponderada Olhos (Pele Cat 1 conta como Olho Cat 1)
            s_eye1 = sum(i.c for i in self.ingredientes if i.cat_olho == '1' or i.cat_pele in ['1', '1A', '1B', '1C'])
            s_eye2 = sum(i.c for i in self.ingredientes if i.cat_olho in ['2', '2A', '2B'])
            
            if s_eye1 >= 3: res['Olhos'] = 'Categoria 1 (H318)'
            elif s_eye1 >= 1 or s_eye2 >= 10 or (10*s_eye1 + s_eye2) >= 10: res['Olhos'] = 'Categoria 2A (H319)'
            else: res['Olhos'] = 'NC'

        # C. Crônicos (Limites de Corte / Cut-off)
        def check_cutoff(attr, target_cats, limit):
            return any(getattr(i, attr) in target_cats and i.c >= limit for i in self.ingredientes)

        # Carcinogenicidade
        if check_cutoff('cat_carc', ['1', '1A', '1B'], 0.1): res['Carcinogenicidade'] = 'Categoria 1 (H350)'
        elif check_cutoff('cat_carc', ['2'], 1.0): res['Carcinogenicidade'] = 'Categoria 2 (H351)' 
        else: res['Carcinogenicidade'] = 'NC'

        # Mutagenicidade
        if check_cutoff('cat_muta', ['1', '1A', '1B'], 0.1): res['Mutagenicidade'] = 'Categoria 1 (H340)'
        elif check_cutoff('cat_muta', ['2'], 1.0): res['Mutagenicidade'] = 'Categoria 2 (H341)'
        else: res['Mutagenicidade'] = 'NC'

        # Reprodução
        if check_cutoff('cat_repro', ['1', '1A', '1B'], 0.3): res['Reprodução'] = 'Categoria 1 (H360)'
        elif check_cutoff('cat_repro', ['2'], 3.0): res['Reprodução'] = 'Categoria 2 (H361)'
        else: res['Reprodução'] = 'NC'

        # STOT SE (Órgãos Alvo Única)
        if check_cutoff('cat_stot_se', ['1'], 10): res['STOT SE'] = 'Categoria 1 (H370)'
        elif check_cutoff('cat_stot_se', ['2'], 10) or \
             any(i.cat_stot_se == '1' and 1.0 <= i.c < 10 for i in self.ingredientes):
             res['STOT SE'] = 'Categoria 2 (H371)'
        elif check_cutoff('cat_stot_se', ['3'], 20): res['STOT SE'] = 'Categoria 3 (H335/H336)'
        else: res['STOT SE'] = 'NC'

        return res

    # --- BLOCO 3: PERIGOS AO MEIO AMBIENTE (Fator M) ---
    def classificar_ambiental(self):
        res = {}
        
        # Agudo: Soma(Conc * M) >= 25%
        soma_aguda_1 = sum(i.c * i.fator_m_agudo for i in self.ingredientes if i.cat_aq_agudo == 1)
        soma_aguda_2 = sum(i.c for i in self.ingredientes if i.cat_aq_agudo == 2)
        soma_aguda_3 = sum(i.c for i in self.ingredientes if i.cat_aq_agudo == 3)

        if soma_aguda_1 >= 25: res['Aquático Agudo'] = 'Categoria 1 (H400)'
        elif (soma_aguda_1 * 10 + soma_aguda_2) >= 25: res['Aquático Agudo'] = 'Categoria 2 (H401)'
        elif (soma_aguda_1 * 100 + soma_aguda_2 * 10 + soma_aguda_3) >= 25: res['Aquático Agudo'] = 'Categoria 3 (H402)'
        else: res['Aquático Agudo'] = 'NC'

        # Crônico
        soma_cron_1 = sum(i.c * i.fator_m_cronico for i in self.ingredientes if i.cat_aq_cronico == 1)
        soma_cron_2 = sum(i.c for i in self.ingredientes if i.cat_aq_cronico == 2)
        soma_cron_3 = sum(i.c for i in self.ingredientes if i.cat_aq_cronico == 3)
        soma_cron_4 = sum(i.c for i in self.ingredientes if i.cat_aq_cronico == 4)

        if soma_cron_1 >= 25: res['Aquático Crônico'] = 'Categoria 1 (H410)'
        elif (soma_cron_1 * 10 + soma_cron_2) >= 25: res['Aquático Crônico'] = 'Categoria 2 (H411)'
        elif (soma_cron_1 * 100 + soma_cron_2 * 10 + soma_cron_3) >= 25: res['Aquático Crônico'] = 'Categoria 3 (H412)'
        elif (soma_cron_1 + soma_cron_2 + soma_cron_3 + soma_cron_4) >= 25: res['Aquático Crônico'] = 'Categoria 4 (H413)'
        else: res['Aquático Crônico'] = 'NC'

        return res

    def executar_analise(self):
        r1 = self.classificar_fisicos()
        r2 = self.classificar_saude()
        r3 = self.classificar_ambiental()
        return {**r1, **r2, **r3}

# ==========================================
# 4. INTERFACE GRÁFICA (STREAMLIT)
# ==========================================
st.set_page_config(page_title="GHS Master ABNT", layout="wide", page_icon="🧪")

st.title("🛡️ Classificador GHS Profissional - ABNT NBR 14725")
st.markdown("### Classificação Automática de Misturas e Substâncias")

# Inicialização de Estado
if 'ingredientes' not in st.session_state:
    st.session_state.ingredientes = []

# --- PAINEL ESQUERDO: CADASTRO ---
with st.sidebar:
    st.header("1. Cadastro de Ingrediente")
    with st.form("form_ingrediente", clear_on_submit=True):
        nome = st.text_input("Nome Química", "Ex: Ditionito de Sódio / Ácido Sulfúrico")
        conc = st.number_input("Concentração na Mistura (%)", 0.0, 100.0, 10.0, step=0.1)
        
        st.markdown("---")
        st.markdown("#### ☠️ Dados de Saúde")
        tipo_ate = st.radio("Toxicidade Aguda", ["Valor DL50", "Categoria GHS"])
        
        ate_o_val = 0.0
        if tipo_ate == "Valor DL50":
            ate_o_val = st.number_input("DL50 Oral (mg/kg)", 0.0)
        else:
            cat_ate = st.selectbox("Cat. Oral", ['NC', '1', '2', '3', '4', '5'])
            ate_o_val = CONVERSAO_ATE['oral'].get(cat_ate)

        c1, c2 = st.columns(2)
        with c1:
            cat_pele = st.selectbox("Pele", ['NC', '1A', '1B', '1C', '2', '3'])
            cat_carc = st.selectbox("Carcinogênico", ['NC', '1A', '1B', '2'])
            cat_stot = st.selectbox("STOT Única", ['NC', '1', '2', '3'])
        with c2:
            cat_olho = st.selectbox("Olhos", ['NC', '1', '2A', '2B'])
            cat_muta = st.selectbox("Mutagênico", ['NC', '1A', '1B', '2'])
            cat_repro = st.selectbox("Reprodutivo", ['NC', '1A', '1B', '2'])

        st.markdown("#### 🐟 Dados Ambientais")
        ac1, ac2 = st.columns(2)
        with ac1:
            cat_aq_ag = st.selectbox("Aq. Agudo", ['None', '1', '2', '3'])
            fator_ag = st.number_input("Fator M Agudo", 1, 10000, 1)
        with ac2:
            cat_aq_cr = st.selectbox("Aq. Crônico", ['None', '1', '2', '3', '4'])
            fator_cr = st.number_input("Fator M Crônico", 1, 10000, 1)

        st.markdown("#### 🔥 Dados Físicos (Ingrediente)")
        fis_auto = st.selectbox("Autoaquecimento", ['NC', '1', '2'])
        fis_sol = st.selectbox("Sólido Inflamável", ['NC', '1', '2'])
        fis_ox = st.selectbox("Sólido Oxidante", ['NC', '1', '2', '3'])

        btn_add = st.form_submit_button("➕ Adicionar à Mistura")
        
        if btn_add:
            novo = Ingrediente(
                nome, conc, ate_oral=ate_o_val,
                cat_pele=cat_pele, cat_olho=cat_olho,
                cat_carc=cat_carc, cat_muta=cat_muta, cat_repro=cat_repro, cat_stot_se=cat_stot,
                cat_aq_agudo=cat_aq_ag, cat_aq_cronico=cat_aq_cr,
                fator_m_agudo=fator_ag, fator_m_cronico=fator_cr,
                fisico_autoaquecimento=fis_auto, fisico_solido_inf=fis_sol, fisico_oxidante=fis_ox
            )
            st.session_state.ingredientes.append(novo)
            st.success("Adicionado!")

# --- PAINEL PRINCIPAL ---
st.header("2. Definição da Mistura e Resultados")

# Tabela de Ingredientes
if st.session_state.ingredientes:
    data = []
    total_conc = 0
    for i in st.session_state.ingredientes:
        data.append({
            "Ingrediente": i.nome,
            "%": i.c,
            "DL50 Oral": i.ate_oral,
            "Pele": i.cat_pele,
            "Aq. Agudo": i.cat_aq_agudo,
            "Fator M": i.fator_m_agudo
        })
        total_conc += i.c
    
    st.dataframe(pd.DataFrame(data), use_container_width=True)
    
    if abs(total_conc - 100) > 0.1:
        st.warning(f"⚠️ Soma das concentrações: {total_conc:.1f}% (Ideal: 100%)")
    
    if st.button("Limpar Lista"):
        st.session_state.ingredientes = []
        st.rerun()

    st.write("---")
    
    # --- DADOS DA MISTURA (CRUCIAL PARA ÁCIDOS) ---
    st.subheader("3. Dados de Ensaio da Mistura (Físico-Químicos)")
    st.info("Preencha estes dados para classificar **Ácidos, Corrosivos a Metais e Inflamáveis** corretamente.")
    
    with st.container():
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            ph = st.number_input("pH (Solução)", 0.0, 14.0, 7.0, help="pH <= 2 ou >= 11.5 classifica automaticamente como Corrosivo Cat 1")
        with c2:
            fp = st.number_input("Ponto de Fulgor (°C)", value=None, placeholder="Vazio se não inflamável")
        with c3:
            bp = st.number_input("Ponto de Ebulição (°C)", value=None, placeholder="Vazio")
        with c4:
            corr = st.number_input("Taxa Corrosão Aço/Alum (mm/ano)", 0.0, help="Se > 6.25 mm/ano a 55°C = Cat 1")

    # Botão de Cálculo
    if st.button("🚀 CLASSIFICAR AGORA", type="primary"):
        # Prepara dados
        dados_mix = {
            'ph': ph, 'flash_point': fp, 'boiling_point': bp, 'corrosion_rate': corr
        }
        
        motor = MotorGHS(st.session_state.ingredientes, dados_mix)
        
        # Executa
        r_fis = motor.classificar_fisicos()
        r_sau = motor.classificar_saude()
        r_amb = motor.classificar_ambiental()
        
        # Exibe Resultados
        st.write("### 📝 Relatório de Classificação GHS")
        
        c_res1, c_res2, c_res3 = st.columns(3)
        
        with c_res1:
            st.info("🔥 Perigos Físicos")
            for k, v in r_fis.items():
                if "NC" not in v: st.markdown(f"**{k}:** 🔴 {v}")
                else: st.markdown(f"**{k}:** 🟢 {v}")
                
        with c_res2:
            st.warning("☠️ Perigos à Saúde")
            for k, v in r_sau.items():
                if "NC" not in v and "Não" not in v: st.markdown(f"**{k}:** 🔴 {v}")
                else: st.markdown(f"**{k}:** 🟢 {v}")
                
        with c_res3:
            st.success("🐟 Perigos Ambientais")
            for k, v in r_amb.items():
                if "NC" not in v and "Não" not in v: st.markdown(f"**{k}:** 🔴 {v}")
                else: st.markdown(f"**{k}:** 🟢 {v}")

else:
    st.info("👈 Comece adicionando ingredientes na barra lateral.")
