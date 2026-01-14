import streamlit as st
import pandas as pd
from fpdf import FPDF
import tempfile
from datetime import timedelta, date, datetime
import plotly.express as px
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from PIL import Image

# Configuração da Página
st.set_page_config(page_title="Relatório Oficial DBV", page_icon="📊", layout="wide")

# ARQUIVO BANCO DE DADOS
DB_FILE = "tarefas_dbv.csv"

# --- FUNÇÕES AUXILIARES ---
def salvar_imagem_temporaria(uploaded_file):
    """Salva o upload convertendo corretamente para JPG usando Pillow"""
    if uploaded_file is None:
        return None
    try:
        image = Image.open(uploaded_file)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            image.save(tmp.name, format="JPEG")
            return tmp.name
    except Exception as e:
        return None

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_dados():
    colunas_padrao = ["Area", "Projeto", "Tarefa", "Responsavel", "Inicio", "Fim", "Status", "Observacao"]
    
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=colunas_padrao)
        df.to_csv(DB_FILE, index=False)
        return df
    
    df = pd.read_csv(DB_FILE)
    if "Observacao" not in df.columns: df["Observacao"] = ""
    if "Responsavel" not in df.columns: df["Responsavel"] = ""
    
    if not df.empty:
        df["Inicio"] = pd.to_datetime(df["Inicio"], errors='coerce').dt.date
        df["Fim"] = pd.to_datetime(df["Fim"], errors='coerce').dt.date
        df["Observacao"] = df["Observacao"].fillna("")
        df["Responsavel"] = df["Responsavel"].fillna("-")
    return df

def salvar_alteracoes(df_novo):
    df_novo.to_csv(DB_FILE, index=False)
    return True

def adicionar_tarefa(dado):
    df = carregar_dados()
    df = pd.concat([df, pd.DataFrame([dado])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

def gerar_imagem_gantt(area_filtro):
    df = carregar_dados()
    if df.empty: return None
    df['Area_Upper'] = df['Area'].astype(str).str.upper()
    area_upper = area_filtro.upper()
    df_area = df[df['Area_Upper'] == area_upper].copy()
    if df_area.empty: return None
    df_area = df_area.sort_values(by="Inicio")
    
    fig, ax = plt.subplots(figsize=(11, 7))
    cores = {"Não Iniciado": "gray", "Em Andamento": "blue", "Bloqueado": "red", "Concluído": "green"}
    y_labels, y_pos = [], []
    
    for i, (idx, row) in enumerate(df_area.iterrows()):
        start = mdates.date2num(row['Inicio'])
        end = mdates.date2num(row['Fim'])
        width = end - start
        cor = cores.get(row['Status'], "blue")
        ax.barh(i, width, left=start, height=0.6, color=cor, alpha=0.8)
        y_labels.append(f"{row['Projeto'][:15]}.. - {row['Tarefa'][:15]}..")
        y_pos.append(i)
        
        resp_nome = str(row['Responsavel'])
        ax.text(start + width/2, i, resp_nome, ha='center', va='center', color='white', fontsize=7, fontweight='bold')
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(y_labels, fontsize=8)
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    plt.title(f"CRONOGRAMA: {area_filtro.upper()}", fontsize=14, fontweight='bold')
    plt.grid(axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    
    temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(temp_img.name, dpi=100)
    plt.close()
    return temp_img.name

# --- CARREGAR DADOS ---
df_geral = carregar_dados()

# --- INTERFACE ---
st.title("📊 Relatório Semanal & Gestão de Projetos")

tab1, tab2 = st.tabs(["📝 Relatório Oficial", "🔨 Gestão de Projetos (Gantt)"])

# ==============================================================================
# ABA 1: RELATÓRIO OFICIAL
# ==============================================================================
with tab1:
    st.markdown("### 1. Cabeçalho")
    
    col_d1, col_d2 = st.columns(2)
    data_inicio = col_d1.date_input("Início da Semana Analisada", date.today())
    
    sem_analisada = f"{data_inicio.strftime('%d/%m')} a {(data_inicio + timedelta(days=4)).strftime('%d/%m')}"
    sem_planejada = f"{(data_inicio + timedelta(days=7)).strftime('%d/%m')} a {(data_inicio + timedelta(days=11)).strftime('%d/%m')}"
    col_d2.info(f"**Analisada:** {sem_analisada} | **Planejada:** {sem_planejada}")

    c1, c2 = st.columns(2)
    listas_areas = ["Comercial", "Marketing", "Tech", "Ops", "Financeiro", "RH"]
    area_selecionada = c1.selectbox("Selecione a Área", listas_areas)
    resp = c2.text_input("Responsável pela entrega")

    st.markdown("---")
    st.markdown("### 2. Resumo Executivo")
    res_vitoria = st.text_input("🏆 Vitória da semana")
    res_risco = st.text_input("⚠️ Principal risco/gargalo")
    res_decisao = st.text_input("🛑 Pontos que exigem decisão")
    res_dependencia = st.text_input("🔗 Dependências com outras áreas")

    st.markdown("---")
    st.markdown("### 3. Projetos da Área")
    upload_visao_geral = st.file_uploader("📸 Print Visão Geral dos Projetos", type=['png', 'jpg', 'jpeg'])

    st.subheader("Detalhamento por Projeto")
    
    if 'n_proj' not in st.session_state: st.session_state.n_proj = 1
    def add_p(): st.session_state.n_proj += 1
    def rem_p(): 
        if st.session_state.n_proj > 1: st.session_state.n_proj -= 1
    
    if not df_geral.empty:
        projetos_da_area = df_geral[df_geral["Area"] == area_selecionada]["Projeto"].unique().tolist()
        lista_opcoes = ["-- Selecione --"] + projetos_da_area
    else:
        lista_opcoes = ["-- Selecione --"]

    for i in range(st.session_state.n_proj):
        with st.container(border=True):
            st.markdown(f"**📂 Projeto {i+1}**")
            p_nome = st.selectbox(f"Selecione o Projeto:", options=lista_opcoes, key=f"p_n_{i}")
            
            if p_nome and p_nome != "-- Selecione --":
                st.markdown("🔹 **Status das Tarefas (Visualização):**")
                tarefas_proj = df_geral[df_geral["Projeto"] == p_nome]
                if not tarefas_proj.empty:
                    hoje = date.today()
                    for idx, row in tarefas_proj.iterrows():
                        t_str = f"**{row['Tarefa']}** (Resp: {row['Responsavel']})"
                        if (row['Fim'] < hoje) and (row['Status'] != "Concluído"):
                            st.error(f"⚠️ {t_str} - Atrasado\nObs: {row['Observacao']}")
                        elif row['Status'] == "Concluído":
                            st.success(f"✅ {t_str} - Concluído")
                        else:
                            st.info(f"▶️ {t_str} - Em Andamento")

            c_img1, c_img2 = st.columns(2)
            p_img_card = c_img1.file_uploader("Print do Card", key=f"img_c_{i}", type=['png', 'jpg', 'jpeg'])
            p_img_ativ = c_img2.file_uploader("Print das Atividades", key=f"img_a_{i}", type=['png', 'jpg', 'jpeg'])
            
            p_entregas = st.text_area("Entregas concluídas semana anterior", height=60, key=f"txt_e_{i}")
            p_acao = st.text_input("Ação mais importante da próxima semana", key=f"txt_ac_{i}")

    col_b1, col_b2 = st.columns([1,5])
    col_b1.button("➕ Mais Projeto", on_click=add_p)
    col_b2.button("➖ Menos", on_click=rem_p)

    st.markdown("---")
    st.markdown("### 4. Indicadores (KPIs)")
    c_kpi1, c_kpi2 = st.columns(2)
    with c_kpi1:
        st.markdown("**KPIs Comerciais**")
        if 'df_kpi_com' not in st.session_state:
            st.session_state.df_kpi_com = pd.DataFrame([{"KPI": "Vendas", "Meta": "100k", "Realizado": "80k", "Var(%)": "-20%", "Leitura": "Abaixo"}, {"KPI": "Leads", "Meta": "50", "Realizado": "60", "Var(%)": "+20%", "Leitura": "Bom"}])
        edited_kpi_com = st.data_editor(st.session_state.df_kpi_com, num_rows="dynamic", key="editor_kpi_com")
    with c_kpi2:
        st.markdown("**KPIs Operacionais**")
        if 'df_kpi_ops' not in st.session_state:
            st.session_state.df_kpi_ops = pd.DataFrame([{"KPI": "SLA Atend.", "Meta": "2h", "Realizado": "1h", "Var(%)": "Ok", "Leitura": "Estável"}])
        edited_kpi_ops = st.data_editor(st.session_state.df_kpi_ops, num_rows="dynamic", key="editor_kpi_ops")
    
    st.markdown("---")
    rotina_obs = st.text_input("Observações Gerais / Rotina")

    # --- GERADOR PDF ---
    def gerar_pdf_final():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=10)

        # Cabeçalho
        pdf.set_fill_color(220, 220, 220)
        pdf.rect(10, 10, 190, 25, 'F')
        pdf.set_y(12)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 8, f"RELATÓRIO: {area_selecionada.upper()}", ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 5, f"Resp: {resp} | Semana: {sem_analisada}", ln=True, align='C')
        pdf.ln(10)

        # Resumo
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, "RESUMO EXECUTIVO", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 6, f"Vitoria: {res_vitoria}\nRisco: {res_risco}\nDecisao: {res_decisao}", border=1)
        pdf.ln(5)

        # Print Geral
        if upload_visao_geral:
            path_geral = salvar_imagem_temporaria(upload_visao_geral)
            if path_geral:
                if pdf.get_y() > 200: pdf.add_page()
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(0, 8, "VISÃO GERAL (BOARD)", ln=True)
                pdf.image(path_geral, w=180)
                pdf.ln(5)

        # Projetos
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, "DETALHAMENTO POR PROJETO", ln=True)
        
        encontrou_projeto = False
        for k in range(st.session_state.n_proj):
            pk_nome = st.session_state.get(f"p_n_{k}")
            if pk_nome and pk_nome != "-- Selecione --":
                encontrou_projeto = True
                
                # Quebra página se estiver no fim
                if pdf.get_y() > 220: pdf.add_page()
                pdf.ln(2)
                
                # 1. TÍTULO DO PROJETO
                pdf.set_font("Arial", 'B', 12)
                pdf.set_fill_color(240, 240, 240)
                pdf.cell(0, 8, f"Projeto: {pk_nome}", ln=True, fill=True)
                
                # 2. IMAGENS (AGORA FICAM EM CIMA, ANTES DO TEXTO)
                img_c = st.session_state.get(f"img_c_{k}")
                img_a = st.session_state.get(f"img_a_{k}")
                
                altura_imagens = 0
                if img_c or img_a:
                    # Verifica se cabe na página, senão pula
                    if pdf.get_y() > 180: pdf.add_page()
                    
                    y_start = pdf.get_y() + 2 # Pega posição Y atual + margem
                    
                    # Imagem 1 (Esquerda)
                    if img_c:
                        path_c = salvar_imagem_temporaria(img_c)
                        if path_c: pdf.image(path_c, x=10, y=y_start, w=90, h=50) # Altura fixa 50 para alinhar
                    
                    # Imagem 2 (Direita)
                    if img_a:
                        path_a = salvar_imagem_temporaria(img_a)
                        if path_a:
                            x_pos = 105
                            pdf.image(path_a, x=x_pos, y=y_start, w=90, h=50)
                    
                    # O PULO DO GATO: Força o cursor a descer a altura das imagens + margem
                    # Assim o texto NUNCA vai ficar por cima
                    altura_imagens = 55 
                    pdf.set_y(y_start + altura_imagens)

                # 3. TEXTO (TAREFAS E STATUS) - Agora vem embaixo das imagens
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(0, 6, "Status das Tarefas e Entregas:", ln=True)
                pdf.set_font("Arial", size=10)
                
                # Lista Tarefas
                ts = df_geral[df_geral["Projeto"] == pk_nome]
                if not ts.empty:
                    hj = date.today()
                    for _, t_row in ts.iterrows():
                        t_nome = t_row['Tarefa']
                        t_status = t_row['Status']
                        t_obs = t_row['Observacao']
                        t_fim = t_row['Fim']
                        t_resp = t_row['Responsavel']
                        
                        is_late = (t_fim < hj) and (t_status != "Concluído")
                        texto_formatado = f"{t_nome} (Resp: {t_resp})"
                        
                        if is_late:
                            pdf.set_text_color(200, 0, 0)
                            pdf.multi_cell(0, 5, f"[ATRASADO] {texto_formatado}: {t_obs if t_obs else 'Sem justificativa'}")
                            pdf.set_text_color(0, 0, 0)
                        elif t_status == "Concluído":
                            pdf.set_text_color(0, 100, 0)
                            pdf.multi_cell(0, 5, f"[OK] {texto_formatado} - Concluído")
                            pdf.set_text_color(0, 0, 0)
                        else:
                            pdf.multi_cell(0, 5, f"[EM ANDAMENTO] {texto_formatado}")
                else:
                    pdf.cell(0, 5, "Sem tarefas cadastradas.", ln=True)
                
                pdf.ln(2)
                pk_ent = st.session_state.get(f"txt_e_{k}", "")
                pk_acao = st.session_state.get(f"txt_ac_{k}", "")
                
                pdf.set_font("Arial", 'I', 9)
                pdf.multi_cell(0, 5, f"Entregas Passadas: {pk_ent}\nProxima Acao: {pk_acao}", border="T")
                pdf.ln(5)

        if not encontrou_projeto:
            pdf.cell(0, 10, "Nenhum projeto selecionado.", ln=True)

        # KPIs e Gantt Final
        pdf.add_page()
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, "INDICADORES (KPIs)", ln=True)
        
        def print_table_pdf(df_table, titulo):
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 8, titulo, ln=True)
            pdf.set_font("Arial", size=9)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(40, 6, "KPI", 1, 0, 'L', True)
            pdf.cell(30, 6, "Meta", 1, 0, 'C', True)
            pdf.cell(30, 6, "Real", 1, 0, 'C', True)
            pdf.cell(30, 6, "Var(%)", 1, 0, 'C', True)
            pdf.cell(60, 6, "Leitura", 1, 1, 'L', True)
            for _, r in df_table.iterrows():
                if r["KPI"]:
                    pdf.cell(40, 6, str(r["KPI"]), 1)
                    pdf.cell(30, 6, str(r["Meta"]), 1, 0, 'C')
                    pdf.cell(30, 6, str(r["Realizado"]), 1, 0, 'C')
                    pdf.cell(30, 6, str(r["Var(%)"]), 1, 0, 'C')
                    pdf.cell(60, 6, str(r["Leitura"]), 1, 1)
            pdf.ln(5)

        print_table_pdf(edited_kpi_com, "Comercial")
        print_table_pdf(edited_kpi_ops, "Operacional")
        pdf.ln(5)
        pdf.multi_cell(0, 5, f"Obs Gerais: {rotina_obs}")

        img_gantt = gerar_imagem_gantt(area_selecionada)
        if img_gantt:
            pdf.add_page()
            pdf.image(img_gantt, x=10, y=10, w=190)

        return pdf.output(dest='S').encode('latin-1', 'replace')

    st.markdown("---")
    if area_selecionada and resp:
        pdf_data = gerar_pdf_final()
        st.download_button("📥 BAIXAR RELATÓRIO OFICIAL (PDF)", data=pdf_data, file_name=f"Relatorio_{area_selecionada}.pdf", mime="application/pdf", type="primary")
    else:
        st.warning("Preencha Área e Responsável para baixar.")

# ==============================================================================
# ABA 2: GESTÃO DE PROJETOS
# ==============================================================================
with tab2:
    st.markdown("### 🔨 Central de Projetos & Gantt")
    col_esq, col_dir = st.columns(2)
    with col_esq:
        with st.expander("🆕 CRIAR NOVO PROJETO"):
            n_proj = st.text_input("Novo Projeto")
            n_resp = st.text_input("Dono")
            n_area = st.selectbox("Área do Projeto", ["Comercial", "Marketing", "Tech", "Ops", "Financeiro", "RH"])
            if st.button("Criar"):
                if n_proj:
                    adicionar_tarefa({"Area": n_area, "Projeto": n_proj, "Tarefa": "Kick-off", "Responsavel": n_resp, "Inicio": date.today(), "Fim": date.today(), "Status": "Não Iniciado", "Observacao": "Início do projeto"})
                    st.success("Criado!")
                    st.rerun()
    with col_dir:
        with st.expander("➕ ADICIONAR TAREFA"):
            l_projs = df_geral["Projeto"].unique().tolist()
            if l_projs:
                p_sel = st.selectbox("Projeto", l_projs)
                t_nome = st.text_input("Tarefa")
                t_resp = st.text_input("Quem?")
                d1 = st.date_input("Início")
                d2 = st.date_input("Fim")
                stat = st.selectbox("Status", ["Não Iniciado", "Em Andamento", "Bloqueado", "Concluído"])
                obs = st.text_input("Observação / Justificativa")
                if st.button("Add Tarefa"):
                    origem_area = df_geral[df_geral["Projeto"] == p_sel].iloc[0]["Area"]
                    adicionar_tarefa({"Area": origem_area, "Projeto": p_sel, "Tarefa": t_nome, "Responsavel": t_resp, "Inicio": d1, "Fim": d2, "Status": stat, "Observacao": obs})
                    st.success("Adicionado!")
                    st.rerun()

    if not df_geral.empty:
        st.markdown("---")
        p_foco = st.selectbox("Visualizar Projeto:", df_geral["Projeto"].unique())
        df_foco = df_geral[df_geral["Projeto"] == p_foco].sort_values("Inicio")
        if not df_foco.empty:
            fig = px.timeline(df_foco, x_start="Inicio", x_end="Fim", y="Tarefa", color="Status", title=p_foco)
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
            df_foco["Inicio"] = pd.to_datetime(df_foco["Inicio"]).dt.date
            df_foco["Fim"] = pd.to_datetime(df_foco["Fim"]).dt.date
            df_edit = st.data_editor(df_foco, use_container_width=True, num_rows="dynamic", key="edit_gantt", column_config={"Inicio": st.column_config.DateColumn(format="DD/MM/YYYY"), "Fim": st.column_config.DateColumn(format="DD/MM/YYYY"), "Observacao": st.column_config.TextColumn("Justificativa"), "Responsavel": st.column_config.TextColumn("Responsável")})
            if st.button("💾 Salvar Edições"):
                df_banco = carregar_dados()
                df_banco = df_banco[df_banco["Projeto"] != p_foco]
                df_final = pd.concat([df_banco, df_edit], ignore_index=True)
                salvar_alteracoes(df_final)
                st.success("Salvo!")
                st.rerun()