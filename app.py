import streamlit as st
import pandas as pd

# --- 1. ESTRUTURA DE DADOS (EXPANDIDA PARA TODOS OS RISCOS) ---
class Ingrediente:
    def __init__(self, nome, concentracao, 
                 # Saúde - Toxicidade Aguda
                 ate_oral=None, ate_dermica=None, ate_inalacao=None,
                 # Saúde - Corrosão/Irritação
                 cat_pele=None, cat_olho=None,
                 # Saúde - Sensibilização e Crônicos
                 cat_resp_sens=None, cat_pele_sens=None,
                 cat_muta=None, cat_carc=None, cat_repro=None, 
                 cat_stot_se=None, cat_stot_re=None, cat_aspiracao=None,
                 # Ambiental
                 cat_aquatico_agudo=None, cat_aquatico_cronico=None,
                 fator_m_agudo=1, fator_m_cronico=1,
                 # Físicos (Novos!)
                 fisico_autoaquecimento=None, fisico_solido_inflamavel=None,
                 fisico_oxidante=None, fisico_corrosivo_metais=None):
        
        self.nome = nome
        self.c = float(concentracao)
        
        # Dados Numéricos
        self.ate_oral = ate_oral
        self.ate_dermica = ate_dermica
        self.ate_inalacao = ate_inalacao
        
        # Categorias de Saúde (Strings padronizadas)
        self.cat_pele = str(cat_pele).upper() if cat_pele else 'NC'
        self.cat_olho = str(cat_olho).upper() if cat_olho else 'NC'
        self.cat_resp_sens = str(cat_resp_sens).upper() if cat_resp_sens else 'NC'
        self.cat_pele_sens = str(cat_pele_sens).upper() if cat_pele_sens else 'NC'
        self.cat_muta = str(cat_muta).upper() if cat_muta else 'NC'
        self.cat_carc = str(cat_carc).upper() if cat_carc else 'NC'
        self.cat_repro = str(cat_repro).upper() if cat_repro else 'NC'
        self.cat_stot_se = str(cat_stot_se).upper() if cat_stot_se else 'NC'
        self.cat_stot_re = str(cat_stot_re).upper() if cat_stot_re else 'NC'
        self.cat_aspiracao = str(cat_aspiracao).upper() if cat_aspiracao else 'NC'

        # Categorias Físicas (Novas)
        self.fisico_autoaquecimento = str(fisico_autoaquecimento).upper() if fisico_autoaquecimento else 'NC'
        self.fisico_solido_inflamavel = str(fisico_solido_inflamavel).upper() if fisico_solido_inflamavel else 'NC'
        self.fisico_oxidante = str(fisico_oxidante).upper() if fisico_oxidante else 'NC'
        self.fisico_corrosivo_metais = str(fisico_corrosivo_metais).upper() if fisico_corrosivo_metais else 'NC'

        # Ambiental
        self.cat_aquatico_agudo = int(cat_aquatico_agudo) if cat_aquatico_agudo else None
        self.cat_aquatico_cronico = int(cat_aquatico_cronico) if cat_aquatico_cronico else None
        self.fator_m_agudo = int(fator_m_agudo)
        self.fator_m_cronico = int(fator_m_cronico)

# --- 2. O MOTOR DE CÁLCULO GHS (ATUALIZADO) ---
class ClassificadorGHS:
    def __init__(self, mistura):
        self.ingredientes = mistura

    # --- LÓGICA 1: TOXICIDADE AGUDA (Fórmula ABNT) ---
    def calcular_ate_mix(self, via):
        soma_fracao = 0
        concentracao_desconhecida = 0
        
        for ing in self.ingredientes:
            valor_ate = getattr(ing, f'ate_{via}')
            if valor_ate is not None and valor_ate > 0:
                soma_fracao += (ing.c / valor_ate)
            else:
                concentracao_desconhecida += ing.c
        
        if soma_fracao == 0: return "Não Classificado (Dados Insuficientes)"
        
        base_calculo = 100 - concentracao_desconhecida if concentracao_desconhecida > 10 else 100
        ate_mix = base_calculo / soma_fracao
        ate_final = round(ate_mix, 2)

        # Classificação baseada na Tabela 16 da ABNT
        cat = "Não Classificado"
        if via == 'oral':
            if ate_final <= 5: cat = "Categoria 1"
            elif ate_final <= 50: cat = "Categoria 2"
            elif ate_final <= 300: cat = "Categoria 3"
            elif ate_final <= 2000: cat = "Categoria 4"
            elif ate_final <= 5000: cat = "Categoria 5"
        
        return f"{cat} (ATEmix: {ate_final})"

    # --- LÓGICA 2: PELE E OLHOS ---
    def classificar_pele(self):
        soma_cat1 = sum([i.c for i in self.ingredientes if i.cat_pele in ['1', '1A', '1B', '1C']])
        soma_cat2 = sum([i.c for i in self.ingredientes if i.cat_pele == '2'])
        soma_cat3 = sum([i.c for i in self.ingredientes if i.cat_pele == '3'])

        if soma_cat1 >= 5.0: return "Categoria 1 (Corrosivo)"
        if soma_cat1 >= 1.0 or soma_cat2 >= 10.0 or (10*soma_cat1 + soma_cat2) >= 10.0: return "Categoria 2 (Irritante)"
        if soma_cat3 >= 10.0 or (10*soma_cat1 + soma_cat2 + soma_cat3) >= 10.0: return "Categoria 3 (Irritante Leve)"
        return "Não Classificado"

    def classificar_olhos(self):
        # Pele Cat 1 conta como Olho Cat 1 na maioria dos casos
        soma_cat1 = sum([i.c for i in self.ingredientes if i.cat_olho == '1' or i.cat_pele in ['1', '1A', '1B', '1C']])
        soma_cat2 = sum([i.c for i in self.ingredientes if i.cat_olho in ['2', '2A', '2B']])

        if soma_cat1 >= 3.0: return "Categoria 1 (Lesão Grave)"
        if soma_cat1 >= 1.0 or soma_cat2 >= 10.0 or (10*soma_cat1 + soma_cat2) >= 10.0: return "Categoria 2/2A (Irritante Ocular)"
        return "Não Classificado"

    # --- LÓGICA 3: PERIGOS FÍSICOS (HERANÇA DE RISCO) ---
    # Nota: Para mistura física, a norma exige teste, mas o software alerta a presença.
    def classificar_fisicos(self):
        res = {}
        # Autoaquecimento (Baseado na sua FDS de Ditionito)
        if any(i.fisico_autoaquecimento == '1' for i in self.ingredientes):
            res['Autoaquecimento'] = "Categoria 1 (Contém ingrediente Cat 1 - Requer Atenção)"
        elif any(i.fisico_autoaquecimento == '2' for i in self.ingredientes):
            res['Autoaquecimento'] = "Categoria 2 (Contém ingrediente Cat 2)"
        else:
            res['Autoaquecimento'] = "Não Classificado"

        # Sólidos Inflamáveis
        if any(i.fisico_solido_inflamavel in ['1', '2'] for i in self.ingredientes):
            res['Sólido Inflamável'] = "Alerta: Contém sólido inflamável"
        else:
            res['Sólido Inflamável'] = "NC"
            
        # Oxidantes
        if any(i.fisico_oxidante in ['1', '2', '3'] for i in self.ingredientes):
            res['Oxidante'] = "Alerta: Contém substância oxidante"
        else:
            res['Oxidante'] = "NC"

        return res

    # --- LÓGICA 4: AMBIENTAL ---
    def classificar_ambiental(self):
        # Agudo
        soma_aguda_1 = sum([i.c * i.fator_m_agudo for i in self.ingredientes if i.cat_aquatico_agudo == 1])
        soma_aguda_2 = sum([i.c for i in self.ingredientes if i.cat_aquatico_agudo == 2])
        soma_aguda_3 = sum([i.c for i in self.ingredientes if i.cat_aquatico_agudo == 3])
        
        res_agudo = "NC"
        if soma_aguda_1 >= 25.0: res_agudo = "Agudo 1"
        elif (soma_aguda_1 * 10 + soma_aguda_2) >= 25.0: res_agudo = "Agudo 2"
        elif (soma_aguda_1 * 100 + soma_aguda_2 * 10 + soma_aguda_3) >= 25.0: res_agudo = "Agudo 3"

        return res_agudo

    def executar_tudo(self):
        fisicos = self.classificar_fisicos()
        return {
            "--- PERIGOS FÍSICOS ---": "",
            "Autoaquecimento": fisicos['Autoaquecimento'],
            "Sólido Inflamável": fisicos['Sólido Inflamável'],
            "Oxidante": fisicos['Oxidante'],
            "--- PERIGOS À SAÚDE ---": "",
            "Toxicidade Aguda (Oral)": self.calcular_ate_mix('oral'),
            "Corrosão/Irritação Pele": self.classificar_pele(),
            "Lesões/Irritação Ocular": self.classificar_olhos(),
            "--- PERIGOS AO MEIO AMBIENTE ---": "",
            "Aquático Agudo": self.classificar_ambiental()
        }

# --- INTERFACE VISUAL STREAMLIT ---
st.set_page_config(page_title="GHS Pro", layout="wide", page_icon="🧪")

st.title("🧪 Classificador GHS - ABNT NBR 14725")
st.markdown("### Ferramenta de Classificação de Misturas (Inclui Riscos Físicos)")

if 'lista_ingredientes' not in st.session_state:
    st.session_state.lista_ingredientes = []

# --- SIDEBAR: ENTRADA DE DADOS ---
with st.sidebar:
    st.header("1. Adicionar Ingrediente")
    nome = st.text_input("Nome Química", "Ex: Ditionito de Sódio")
    conc = st.number_input("Concentração (%)", 0.0, 100.0, 100.0, step=0.1)
    
    # Abas para organizar os muitos perigos
    tab1, tab2, tab3 = st.tabs(["🔥 Físicos", "☠️ Saúde", "🐟 Ambiental"])
    
    with tab1:
        st.caption("Perigos Físicos (Baseado na FDS do ingrediente)")
        fis_auto = st.selectbox("Autoaquecimento", ["NC", "1", "2"], help="H251 ou H252")
        fis_sol_inf = st.selectbox("Sólido Inflamável", ["NC", "1", "2"], help="H228")
        fis_ox = st.selectbox("Sólido Oxidante", ["NC", "1", "2", "3"], help="H271/H272")
        fis_corr_met = st.selectbox("Corrosivo p/ Metais", ["NC", "1"], help="H290")

    with tab2:
        st.caption("Perigos à Saúde")
        ate_oral = st.number_input("DL50 Oral (mg/kg)", 0.0, value=500.0, help="Deixe 0 se desconhecido")
        cat_pele = st.selectbox("Pele", ["NC", "1A", "1B", "1C", "2", "3"])
        cat_olho = st.selectbox("Olhos", ["NC", "1", "2A", "2B"])
        cat_sens_resp = st.selectbox("Sens. Respiratória", ["NC", "1", "1A", "1B"])
        cat_carc = st.selectbox("Carcinogenicidade", ["NC", "1A", "1B", "2"])

    with tab3:
        st.caption("Perigos ao Meio Ambiente")
        cat_aq_ag = st.selectbox("Aquático Agudo", ["None", "1", "2", "3"])
        fator_m = st.number_input("Fator M (Agudo)", 1, 10000, 1)

    if st.button("➕ Adicionar à Mistura"):
        # Conversão de inputs da UI para o formato da Classe
        c_aq_ag = int(cat_aq_ag) if cat_aq_ag != "None" else None
        
        novo = Ingrediente(
            nome=nome, concentracao=conc,
            ate_oral=ate_oral,
            cat_pele=cat_pele, cat_olho=cat_olho,
            cat_resp_sens=cat_sens_resp, cat_carc=cat_carc,
            cat_aquatico_agudo=c_aq_ag, fator_m_agudo=fator_m,
            # Físicos
            fisico_autoaquecimento=fis_auto,
            fisico_solido_inflamavel=fis_sol_inf,
            fisico_oxidante=fis_ox,
            fisico_corrosivo_metais=fis_corr_met
        )
        st.session_state.lista_ingredientes.append(novo)
        st.success(f"{nome} adicionado!")

# --- ÁREA PRINCIPAL ---
col_table, col_result = st.columns([1.5, 1])

with col_table:
    st.subheader("📋 Composição Atual")
    if st.session_state.lista_ingredientes:
        df_data = []
        soma_conc = 0
        for i in st.session_state.lista_ingredientes:
            df_data.append({
                "Nome": i.nome,
                "%": i.c,
                "DL50 Oral": i.ate_oral,
                "Autoaq.": i.fisico_autoaquecimento
            })
            soma_conc += i.c
        
        st.dataframe(pd.DataFrame(df_data), use_container_width=True)
        
        if soma_conc != 100:
            st.warning(f"⚠️ Soma das concentrações: {soma_conc:.2f}% (Ideal: 100%)")
        
        if st.button("Limpar Tudo"):
            st.session_state.lista_ingredientes = []
            st.rerun()
    else:
        st.info("Cadastre os ingredientes na barra lateral.")

with col_result:
    st.subheader("📊 Classificação da Mistura")
    if st.button("Calcular GHS", type="primary"):
        if st.session_state.lista_ingredientes:
            motor = ClassificadorGHS(st.session_state.lista_ingredientes)
            resultado = motor.executar_tudo()
            
            with st.container():
                st.write("---")
                for k, v in resultado.items():
                    if "---" in k:
                        st.markdown(f"**{k}**")
                    else:
                        # Destaque visual se houver perigo
                        if "Categoria" in str(v) or "Agudo" in str(v) or "Alerta" in str(v):
                            st.error(f"**{k}:** {v}")
                        else:
                            st.success(f"**{k}:** {v}")
        else:
            st.warning("Adicione ingredientes para calcular.")
