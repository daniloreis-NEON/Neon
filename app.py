import streamlit as st
import pandas as pd

# ==============================================================================
# MÓDULO 1: ESTRUTURA DE DADOS (INGREDIENTES)
# Focado nas propriedades Físicas extraídas pelo NotebookLM
# ==============================================================================
class Ingrediente:
    def __init__(self, nome, concentracao, 
                 # Flags para Perigos que NÃO são calculáveis por soma (Seção 5.2.1, 5.2.9, etc.)
                 eh_inflamavel=False,        # Para sólidos/gases ou herança de líquidos
                 eh_oxidante=False,          # Sólidos/Líquidos Oxidantes
                 eh_explosivo=False,         # Explosivos
                 eh_piroforico=False,        # Pirofóricos
                 eh_autoaquecimento=False,   # Autoaquecimento (Caso do Ditionito)
                 eh_corrosivo_metais=False): # Corrosivo Metais (Caso do Ácido)
        
        self.nome = nome
        self.c = float(concentracao)
        
        # Propriedades declaratórias (O usuário diz se o ingrediente puro tem esse risco)
        self.eh_inflamavel = eh_inflamavel
        self.eh_oxidante = eh_oxidante
        self.eh_explosivo = eh_explosivo
        self.eh_piroforico = eh_piroforico
        self.eh_autoaquecimento = eh_autoaquecimento
        self.eh_corrosivo_metais = eh_corrosivo_metais

# ==============================================================================
# MÓDULO 2: MOTOR DE LÓGICA FÍSICA (ABNT NBR 14725 - SEÇÃO 5.2)
# Implementação rigorosa da extração do NotebookLM
# ==============================================================================
class MotorFisico:
    def __init__(self, ingredientes, dados_mistura):
        self.ingredientes = ingredientes
        self.mistura = dados_mistura # Dicionário com dados de laboratório da mistura

    # Lógica 1: Líquidos Inflamáveis (Seção 5.2.6)
    # Baseado na Tabela 6 e Figura 11
    def classificar_liquido_inflamavel(self):
        fp = self.mistura.get('flash_point')   # Ponto de Fulgor
        bp = self.mistura.get('boiling_point') # Ponto de Ebulição
        
        # Se o usuário não tem dados de teste, verificamos se há ingredientes inflamáveis
        if fp is None:
            if any(i.eh_inflamavel for i in self.ingredientes):
                return "ALERTA: Contém ingredientes inflamáveis. Requer teste de Ponto de Fulgor."
            return "Não Classificado (Faltam dados de PF)"

        # Lógica Matemática da Norma
        if bp is not None:
            if fp < 23.0 and bp <= 35.0: return "Categoria 1 (H224)"
            if fp < 23.0 and bp > 35.0:  return "Categoria 2 (H225)"
        
        # Categorias 3 e 4 dependem apenas do Flash Point (ou BP não informado)
        if 23.0 <= fp <= 60.0: return "Categoria 3 (H226)"
        if 60.0 < fp <= 93.0:  return "Categoria 4 (Líquido Combustível - H227)"
        
        if fp > 93.0: return "Não Classificado"
        
        return "Dados insuficientes para categorização exata"

    # Lógica 2: Corrosivo para Metais (Seção 5.2.16)
    # Baseado na Taxa de Corrosão > 6.25 mm/ano
    def classificar_corrosivo_metais(self):
        taxa = self.mistura.get('corrosion_rate') # mm/ano
        
        # Teste da Mistura (Prioridade Máxima)
        if taxa is not None:
            if taxa > 6.25: return "Categoria 1 (H290)"
            else: return "Não Classificado (Baseado na taxa informada)"
            
        # Lógica de Herança (Se não houver teste, mas tiver ingrediente corrosivo)
        # Ex: Ácido Sulfúrico puro ou concentrado
        soma_corrosivos = sum(i.c for i in self.ingredientes if i.eh_corrosivo_metais)
        if soma_corrosivos >= 1.0: # Limite de corte conservador para metais
            return "ALERTA: Contém ingredientes corrosivos a metais. Provável Categoria 1."
            
        return "Não Classificado"

    # Lógica 3: Outros Perigos Físicos (Validação de Misturas)
    # Conforme extração: Estes não somam, requerem teste ou herança direta.
    def verificar_outros_perigos(self):
        alertas = {}
        
        # Autoaquecimento (Ex: Ditionito de Sódio)
        if any(i.eh_autoaquecimento for i in self.ingredientes):
            alertas['Autoaquecimento'] = "ALERTA: Contém substância autoaquecida (Ex: Ditionito). Requer Teste N.4."
        else:
            alertas['Autoaquecimento'] = "NC"

        # Oxidantes
        if any(i.eh_oxidante for i in self.ingredientes):
            alertas['Oxidante'] = "ALERTA: Contém oxidantes. Requer Teste O.1 (Sólido) ou O.2 (Líquido)."
        else:
            alertas['Oxidante'] = "NC"
            
        return alertas

    def executar(self):
        resultado = {
            "Líquido Inflamável": self.classificar_liquido_inflamavel(),
            "Corrosivo p/ Metais": self.classificar_corrosivo_metais()
        }
        resultado.update(self.verificar_outros_perigos())
        return resultado

# ==============================================================================
# MÓDULO 3: INTERFACE STREAMLIT
# ==============================================================================
st.set_page_config(page_title="GHS Físico - Parte 1", layout="wide")
st.title("🛡️ Classificador GHS - Módulo: Perigos Físicos")
st.markdown("Implementação da **Seção 5.2** da ABNT NBR 14725.")

if 'lista_ingredientes' not in st.session_state:
    st.session_state.lista_ingredientes = []

# --- SIDEBAR: CADASTRO DE INGREDIENTES ---
with st.sidebar:
    st.header("1. Cadastro de Ingredientes")
    st.info("Aqui você define as propriedades intrínsecas da substância pura.")
    
    nome = st.text_input("Nome da Substância", "Ex: Ácido Sulfúrico")
    conc = st.number_input("Concentração (%)", 0.0, 100.0, 100.0)
    
    st.markdown("### Propriedades Físicas (Do Ingrediente)")
    # Checkboxes para "Flags" de perigo
    inflamavel = st.checkbox("É Inflamável? (Sólido/Líquido/Gás)")
    corrosivo = st.checkbox("É Corrosivo para Metais? (Ex: Ácidos)", value=True) # Padrão True para facilitar teste do Ácido
    autoaq = st.checkbox("Sofre Autoaquecimento? (Ex: Ditionito)")
    oxidante = st.checkbox("É Oxidante?")
    
    if st.button("➕ Adicionar Ingrediente"):
        novo = Ingrediente(nome, conc, 
                           eh_inflamavel=inflamavel, 
                           eh_corrosivo_metais=corrosivo,
                           eh_autoaquecimento=autoaq, 
                           eh_oxidante=oxidante)
        st.session_state.lista_ingredientes.append(novo)
        st.success(f"{nome} adicionado!")

# --- ÁREA PRINCIPAL: DADOS DA MISTURA ---
st.header("2. Dados da Mistura (Testes de Laboratório)")
st.warning("Para Perigos Físicos, os dados da mistura têm prioridade sobre a soma dos ingredientes.")

c1, c2, c3 = st.columns(3)
with c1:
    fp_input = st.number_input("Ponto de Fulgor (°C)", value=None, placeholder="Deixe vazio se não testou")
with c2:
    bp_input = st.number_input("Ponto de Ebulição (°C)", value=None, placeholder="Obrigatório para Cat 1/2")
with c3:
    corr_input = st.number_input("Taxa de Corrosão (mm/ano)", value=None, placeholder="> 6.25 é Cat 1")

# --- ÁREA PRINCIPAL: TABELA E CÁLCULO ---
st.write("---")
st.subheader("3. Composição e Resultado")

if st.session_state.lista_ingredientes:
    # Mostra tabela
    df = pd.DataFrame([vars(i) for i in st.session_state.lista_ingredientes])
    st.dataframe(df)
    
    if st.button("🚀 Classificar Perigos Físicos"):
        # Prepara dados
        dados_mix = {
            'flash_point': fp_input,
            'boiling_point': bp_input,
            'corrosion_rate': corr_input
        }
        
        # Instancia motor e calcula
        motor = MotorFisico(st.session_state.lista_ingredientes, dados_mix)
        resultados = motor.executar()
        
        # Mostra cards
        for perigo, classif in resultados.items():
            if "NC" in classif or "Não Classificado" in classif:
                st.success(f"**{perigo}:** {classif}")
            else:
                st.error(f"**{perigo}:** {classif}")
                
    if st.button("Limpar Lista"):
        st.session_state.lista_ingredientes = []
        st.rerun()
else:
    st.info("Cadastre ingredientes para começar.")

import streamlit as st
import pandas as pd

# ==============================================================================
# MÓDULO DE SAÚDE: CONSTANTES E TABELAS DE CONVERSÃO (TABELA 17)
# ==============================================================================
CONVERSAO_ATE = {
    'oral': {'1': 0.5, '2': 5, '3': 100, '4': 500, '5': 2500, 'NC': None},
    'dermica': {'1': 5, '2': 50, '3': 300, '4': 1100, '5': 2500, 'NC': None},
    'inalacao_gases': {'1': 10, '2': 100, '3': 700, '4': 4500, 'NC': None},
    'inalacao_vapores': {'1': 0.05, '2': 0.5, '3': 3, '4': 11, 'NC': None},
    'inalacao_poeiras': {'1': 0.005, '2': 0.05, '3': 0.5, '4': 1.5, 'NC': None}
}

# ==============================================================================
# CLASSE INGREDIENTE (ATUALIZADA PARA SAÚDE)
# ==============================================================================
class IngredienteSaude:
    def __init__(self, nome, concentracao, 
                 ate_oral=None, ate_dermica=None, ate_inalacao=None, tipo_inalacao='poeiras',
                 cat_pele='NC', cat_olho='NC',
                 cat_sens_resp='NC', cat_sens_pele='NC',
                 cat_muta='NC', cat_carc='NC', cat_repro='NC', cat_lact='NC',
                 cat_stot_se='NC', cat_stot_re='NC', cat_aspiracao='NC'):
        
        self.nome = nome
        self.c = float(concentracao)
        
        # Toxicidade Aguda (Valores Numéricos)
        self.ate_oral = ate_oral
        self.ate_dermica = ate_dermica
        self.ate_inalacao = ate_inalacao
        self.tipo_inalacao = tipo_inalacao # 'gases', 'vapores', 'poeiras'

        # Categorias (Strings padronizadas)
        self.cat_pele = str(cat_pele).upper()
        self.cat_olho = str(cat_olho).upper()
        self.cat_sens_resp = str(cat_sens_resp).upper()
        self.cat_sens_pele = str(cat_sens_pele).upper()
        self.cat_muta = str(cat_muta).upper()
        self.cat_carc = str(cat_carc).upper()
        self.cat_repro = str(cat_repro).upper()
        self.cat_lact = str(cat_lact).upper()
        self.cat_stot_se = str(cat_stot_se).upper()
        self.cat_stot_re = str(cat_stot_re).upper()
        self.cat_aspiracao = str(cat_aspiracao).upper()

# ==============================================================================
# MOTOR DE CÁLCULO DE SAÚDE (ABNT NBR 14725 - SEÇÃO 5.3)
# ==============================================================================
class MotorSaude:
    def __init__(self, ingredientes, dados_mistura):
        self.ingredientes = ingredientes
        self.mistura = dados_mistura # Dicionário com pH, viscosidade, etc.

    # --- 1. TOXICIDADE AGUDA (Cálculo ATEmix) ---
    def calcular_ate_mix(self, via):
        soma_fracao = 0
        concentracao_desconhecida = 0
        
        for ing in self.ingredientes:
            valor_ate = None
            if via == 'oral': valor_ate = ing.ate_oral
            elif via == 'dermica': valor_ate = ing.ate_dermica
            elif via == 'inalacao': valor_ate = ing.ate_inalacao # Simplificação: assume mesmo tipo físico
            
            if valor_ate is not None and valor_ate > 0:
                soma_fracao += (ing.c / valor_ate)
            else:
                concentracao_desconhecida += ing.c
        
        if soma_fracao == 0: return "NC (Dados Insuficientes)"

        # Fórmula ABNT: Ajuste se desconhecidos > 10%
        numerador = 100 - concentracao_desconhecida if concentracao_desconhecida > 10 else 100
        
        if numerator <= 0: return "NC (Dados Insuficientes - >90% desconhecido)"

        ate_mix = numerator / soma_fracao
        return round(ate_mix, 2)

    def classificar_toxicidade_aguda(self):
        res = {}
        # Oral
        ate_oral = self.calcular_ate_mix('oral')
        if isinstance(ate_oral, float):
            cat = 'NC'
            if ate_oral <= 5: cat = 'Categoria 1 (H300)'
            elif ate_oral <= 50: cat = 'Categoria 2 (H300)'
            elif ate_oral <= 300: cat = 'Categoria 3 (H301)'
            elif ate_oral <= 2000: cat = 'Categoria 4 (H302)'
            elif ate_oral <= 5000: cat = 'Categoria 5 (H303)'
            res['Tox. Aguda Oral'] = f"{cat} (ATEmix: {ate_oral})"
        else: res['Tox. Aguda Oral'] = str(ate_oral)
        
        # Repetir lógica para Dérmica e Inalação se necessário...
        return res

    # --- 2. CORROSÃO/IRRITAÇÃO (PELE E OLHOS) ---
    def classificar_corrosao_irritacao(self):
        res = {}
        ph = self.mistura.get('ph')
        
        # A. Regra de Precedência do pH (Override)
        if ph is not None and (ph <= 2 or ph >= 11.5):
            res['Pele'] = 'Categoria 1 (Baseado em pH Extremo - H314)'
            res['Olhos'] = 'Categoria 1 (Baseado em pH Extremo - H318)'
            return res # Sai da função pois pH domina

        # B. Aditividade Ponderada (Pele)
        soma_skin1 = sum(i.c for i in self.ingredientes if i.cat_pele in ['1', '1A', '1B', '1C'])
        soma_skin2 = sum(i.c for i in self.ingredientes if i.cat_pele == '2')
        soma_skin3 = sum(i.c for i in self.ingredientes if i.cat_pele == '3')

        if soma_skin1 >= 5.0:
            res['Pele'] = 'Categoria 1 (H314)'
        elif soma_skin1 >= 1.0 or soma_skin2 >= 10.0 or (10 * soma_skin1 + soma_skin2) >= 10.0:
            res['Pele'] = 'Categoria 2 (H315)'
        elif soma_skin3 >= 10.0 or (10 * soma_skin1 + soma_skin2 + soma_skin3) >= 10.0:
            res['Pele'] = 'Categoria 3 (H316)'
        else:
            res['Pele'] = 'NC'

        # C. Aditividade Ponderada (Olhos)
        # Nota: Pele Cat 1 conta como Olho Cat 1
        soma_eye1 = sum(i.c for i in self.ingredientes if i.cat_olho == '1' or i.cat_pele in ['1', '1A', '1B', '1C'])
        soma_eye2 = sum(i.c for i in self.ingredientes if i.cat_olho in ['2', '2A', '2B'])

        if soma_eye1 >= 3.0:
            res['Olhos'] = 'Categoria 1 (H318)'
        elif soma_eye1 >= 1.0 or soma_eye2 >= 10.0 or (10 * soma_eye1 + soma_eye2) >= 10.0:
            res['Olhos'] = 'Categoria 2/2A (H319)'
        else:
            res['Olhos'] = 'NC'
            
        return res

    # --- 3. PERIGOS CRÔNICOS (CMR E STOT) ---
    def classificar_cronicos(self):
        res = {}
        
        # Função auxiliar para verificar limites de corte
        def check_cutoff(attr, target_cats, limit):
            return any(getattr(i, attr) in target_cats and i.c >= limit for i in self.ingredientes)

        # Sensibilização
        if check_cutoff('cat_sens_resp', ['1', '1A', '1B'], 1.0): res['Sens. Respiratória'] = 'Categoria 1 (H334)' # Simplificado 1.0%
        else: res['Sens. Respiratória'] = 'NC'
        
        if check_cutoff('cat_sens_pele', ['1', '1A', '1B'], 1.0): res['Sens. Pele'] = 'Categoria 1 (H317)'
        else: res['Sens. Pele'] = 'NC'

        # Mutagenicidade
        if check_cutoff('cat_muta', ['1', '1A', '1B'], 0.1): res['Mutagenicidade'] = 'Categoria 1 (H340)'
        elif check_cutoff('cat_muta', ['2'], 1.0): res['Mutagenicidade'] = 'Categoria 2 (H341)'
        else: res['Mutagenicidade'] = 'NC'

        # Carcinogenicidade
        if check_cutoff('cat_carc', ['1', '1A', '1B'], 0.1): res['Carcinogenicidade'] = 'Categoria 1 (H350)'
        elif check_cutoff('cat_carc', ['2'], 1.0): res['Carcinogenicidade'] = 'Categoria 2 (H351)' # Nota: Pode configurar para 0.1%
        else: res['Carcinogenicidade'] = 'NC'

        # Reprodução
        if check_cutoff('cat_repro', ['1', '1A', '1B'], 0.3): res['Reprodução'] = 'Categoria 1 (H360)'
        elif check_cutoff('cat_repro', ['2'], 3.0): res['Reprodução'] = 'Categoria 2 (H361)'
        else: res['Reprodução'] = 'NC'
        
        # Lactação
        if any(i.cat_lact != 'NC' and i.c >= 0.3 for i in self.ingredientes): res['Lactação'] = 'Efeitos sobre a Lactação (H362)'
        else: res['Lactação'] = 'NC'

        # STOT SE (Órgãos Alvo - Única)
        if check_cutoff('cat_stot_se', ['1'], 10.0): res['STOT SE'] = 'Categoria 1 (H370)'
        elif check_cutoff('cat_stot_se', ['2'], 10.0) or \
             any(i.cat_stot_se == '1' and 1.0 <= i.c < 10.0 for i in self.ingredientes):
             res['STOT SE'] = 'Categoria 2 (H371)'
        elif check_cutoff('cat_stot_se', ['3'], 20.0): res['STOT SE'] = 'Categoria 3 (H335/H336)'
        else: res['STOT SE'] = 'NC'

        # STOT RE (Órgãos Alvo - Repetida)
        if check_cutoff('cat_stot_re', ['1'], 10.0): res['STOT RE'] = 'Categoria 1 (H372)'
        elif check_cutoff('cat_stot_re', ['2'], 10.0) or \
             any(i.cat_stot_re == '1' and 1.0 <= i.c < 10.0 for i in self.ingredientes):
             res['STOT RE'] = 'Categoria 2 (H373)'
        else: res['STOT RE'] = 'NC'
        
        # Aspiração (Requer viscosidade da mistura)
        visc = self.mistura.get('viscosidade_40c') # mm2/s
        soma_asp = sum(i.c for i in self.ingredientes if i.cat_aspiracao == '1')
        if visc is not None and visc <= 20.5 and soma_asp >= 10.0:
            res['Perigo por Aspiração'] = 'Categoria 1 (H304)'
        else:
            res['Perigo por Aspiração'] = 'NC'

        return res

    def executar(self):
        r1 = self.classificar_toxicidade_aguda()
        r2 = self.classificar_corrosao_irritacao()
        r3 = self.classificar_cronicos()
        return {**r1, **r2, **r3}

# ==============================================================================
    # MÓDULO 3: MOTOR AMBIENTAL (ABNT NBR 14725 - SEÇÃO 5.4)
    # Implementação do Método de Somatória com Fator M
    # ==============================================================================
    
    def classificar_ambiental(self):
        res = {}
        
        # --- 1. PREPARAÇÃO DOS DADOS (FILTRO DE CUT-OFF) ---
        # A norma diz (Seção 5.4.1.9):
        # - Ingredientes Cat 1: Considerar se concentração >= 0.1%
        # - Outras Categorias: Considerar se concentração >= 1.0%
        
        # Listas filtradas para cálculo Agudo
        aguda_1 = [i for i in self.ingredientes if i.cat_aq_agudo == 1 and i.c >= 0.1]
        aguda_2 = [i for i in self.ingredientes if i.cat_aq_agudo == 2 and i.c >= 1.0]
        aguda_3 = [i for i in self.ingredientes if i.cat_aq_agudo == 3 and i.c >= 1.0]
        
        # Listas filtradas para cálculo Crônico
        cron_1 = [i for i in self.ingredientes if i.cat_aq_cronico == 1 and i.c >= 0.1]
        cron_2 = [i for i in self.ingredientes if i.cat_aq_cronico == 2 and i.c >= 1.0]
        cron_3 = [i for i in self.ingredientes if i.cat_aq_cronico == 3 and i.c >= 1.0]
        cron_4 = [i for i in self.ingredientes if i.cat_aq_cronico == 4 and i.c >= 1.0]

        # --- 2. CÁLCULO TOXICIDADE AQUÁTICA AGUDA (TABELA 47) ---
        # Soma Ponderada Aguda 1: Soma(Conc * M)
        soma_aguda_1_M = sum(i.c * i.fator_m_agudo for i in aguda_1)
        soma_aguda_2 = sum(i.c for i in aguda_2)
        soma_aguda_3 = sum(i.c for i in aguda_3)

        # Lógica em Cascata (Se atende 1, para. Se não, testa 2...)
        if soma_aguda_1_M >= 25.0:
            res['Aquático Agudo'] = 'Categoria 1 (H400) [Atenção]'
            
        elif (soma_aguda_1_M * 10.0) + soma_aguda_2 >= 25.0:
            res['Aquático Agudo'] = 'Categoria 2 (H401)'
            
        elif (soma_aguda_1_M * 100.0) + (soma_aguda_2 * 10.0) + soma_aguda_3 >= 25.0:
            res['Aquático Agudo'] = 'Categoria 3 (H402)'
            
        else:
            res['Aquático Agudo'] = 'NC'

        # --- 3. CÁLCULO TOXICIDADE AQUÁTICA CRÔNICA (TABELA 48) ---
        # Soma Ponderada Crônica 1: Soma(Conc * M_Cronico)
        soma_cron_1_M = sum(i.c * i.fator_m_cronico for i in cron_1)
        soma_cron_2 = sum(i.c for i in cron_2)
        soma_cron_3 = sum(i.c for i in cron_3)
        # Nota: Para Crônica 4, somamos todas as categorias crônicas como se fossem peso 1
        # Isso é uma simplificação segura da "Rede de Segurança" da norma
        soma_cron_4_total = sum(i.c for i in self.ingredientes if i.cat_aq_cronico in [1, 2, 3, 4] and i.c >= 1.0)

        # Lógica em Cascata
        if soma_cron_1_M >= 25.0:
            res['Aquático Crônico'] = 'Categoria 1 (H410) [Atenção]'
            
        elif (soma_cron_1_M * 10.0) + soma_cron_2 >= 25.0:
            res['Aquático Crônico'] = 'Categoria 2 (H411)'
            
        elif (soma_cron_1_M * 100.0) + (soma_cron_2 * 10.0) + soma_cron_3 >= 25.0:
            res['Aquático Crônico'] = 'Categoria 3 (H412)'
            
        elif soma_cron_4_total >= 25.0:
            res['Aquático Crônico'] = 'Categoria 4 (H413)'
            
        else:
            res['Aquático Crônico'] = 'NC'

        return res
