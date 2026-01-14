import streamlit as st
import pandas as pd
from fpdf import FPDF
import tempfile
from datetime import timedelta

# Configuração da Página
st.set_page_config(page_title="Relatório Semanal", page_icon="📊", layout="wide")

# Título e Estilo
st.title("📊 Gerador de Relatório Semanal")
st.markdown("Preencha os dados abaixo e baixe o PDF pronto.")

# --- LÓGICA DE DATA (CALENDÁRIO) ---
st.sidebar.header("📅 Seleção de Data")
data_selecionada = st.sidebar.date_input("Selecione a segunda-feira da semana analisada")

# Cálculo automático das datas (Segunda a Sexta)
inicio_analise = data_selecionada
fim_analise = data_selecionada + timedelta(days=4)
# Semana Planejada (Próxima semana)
inicio_plan = data_selecionada + timedelta(days=7)
fim_plan =inicio_plan + timedelta(days=4)

# Formatação para string (ex: 13/01 a 17/01)
str_semana_analisada = f"{inicio_analise.strftime('%d/%m')} a {fim_analise.strftime('%d/%m')}"
str_semana_planejada = f"{inicio_plan.strftime('%d/%m')} a {fim_plan.strftime('%d/%m')}"

st.sidebar.info(f"**Semana Analisada:** {str_semana_analisada}")
st.sidebar.info(f"**Semana Planejada:** {str_semana_planejada}")

# --- FORMULÁRIO ---

with st.container():
    st.subheader("1. Identificação")
    col1, col2 = st.columns(2)
    area = col1.text_input("Área")
    responsavel = col2.text_input("Responsável")

    st.subheader("2. Resumo Executivo")
    vitoria = st.text_area("🏆 Vitória da semana", height=70)
    risco = st.text_area("⚠️ Principal risco/gargalo", height=70)
    decisao = st.text_area("🛑 Necessita Decisão/Direção", height=70)

    st.subheader("3. Evidências (Prints)")
    st.info("Tire prints do Notion e cole aqui.")
    
    upload_geral = st.file_uploader("Visão Geral (Board)", type=['png', 'jpg', 'jpeg'])
    
    col_proj1, col_proj2 = st.columns(2)
    with col_proj1:
        st.markdown("**Projeto Destaque 1**")
        p1_nome = st.text_input("Nome Projeto 1")
        p1_status = st.text_area("Status P1")
        p1_img = st.file_uploader("Print P1", type=['png', 'jpg'], key="p1")
    
    with col_proj2:
        st.markdown("**Projeto Destaque 2**")
        p2_nome = st.text_input("Nome Projeto 2")
        p2_status = st.text_area("Status P2")
        p2_img = st.file_uploader("Print P2", type=['png', 'jpg'], key="p2")

    st.subheader("4. KPIs (Tabela Editável)")
    
    # Tabela padrão
    if 'df_kpi' not in st.session_state:
        st.session_state.df_kpi = pd.DataFrame({
            "Indicador": ["Faturamento", "Leads/Vendas", "Operacional", "Outro"],
            "Meta": ["-", "-", "-", "-"],
            "Realizado": ["-", "-", "-", "-"],
            "Var (%)": ["0%", "0%", "0%", "0%"]
        })
    
    kpi_result = st.data_editor(st.session_state.df_kpi, num_rows="dynamic", use_container_width=True)

    st.subheader("5. Pauta para Reunião")
    pauta = st.text_area("Tópicos para discutir na reunião (Listar itens)", height=100)

# --- GERADOR DE PDF ---
def gerar_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Cabeçalho
    pdf.set_fill_color(240, 240, 240)
    pdf.rect(0, 0, 210, 30, 'F')
    pdf.set_y(10)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"RELATÓRIO SEMANAL: {area.upper()}", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, f"Responsável: {responsavel} | Período: {str_semana_analisada}", ln=True, align='C')
    pdf.ln(10)

    # Resumo
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. RESUMO EXECUTIVO", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 5, f"Vitoria: {vitoria}\n\nRisco: {risco}\n\nDecisao: {decisao}")
    pdf.ln(5)

    # KPIs
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. INDICADORES", ln=True)
    pdf.set_font("Arial", size=9)
    # Cabeçalho Tabela
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(60, 7, "Indicador", 1, 0, 'L', True)
    pdf.cell(40, 7, "Meta", 1, 0, 'C', True)
    pdf.cell(40, 7, "Real", 1, 0, 'C', True)
    pdf.cell(40, 7, "Var", 1, 1, 'C', True)
    # Dados
    for idx, row in kpi_result.iterrows():
        pdf.cell(60, 7, str(row['Indicador']), 1)
        pdf.cell(40, 7, str(row['Meta']), 1, 0, 'C')
        pdf.cell(40, 7, str(row['Realizado']), 1, 0, 'C')
        pdf.cell(40, 7, str(row['Var (%)']), 1, 1, 'C')
    pdf.ln(5)

    # Função auxiliar imagens
    def add_img(file, title):
        if file:
            pdf.ln(2)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 8, title, ln=True)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(file.getvalue())
                try:
                    pdf.image(tmp.name, w=170)
                except:
                    pdf.cell(0, 10, "[Erro na imagem]", ln=True)
            pdf.ln(5)

    # Imagens
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "3. PROJETOS E EVIDÊNCIAS", ln=True)
    
    add_img(upload_geral, "Visão Geral")
    
    if p1_nome:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, f"Projeto: {p1_nome}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 5, f"Status: {p1_status}")
        add_img(p1_img, "")

    if p2_nome:
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, f"Projeto: {p2_nome}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 5, f"Status: {p2_status}")
        add_img(p2_img, "")

    # Pauta
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "4. PAUTA / PRÓXIMOS PASSOS", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 5, pauta)

    return pdf.output(dest='S').encode('latin-1', 'replace')

st.markdown("---")
if st.button("📥 GERAR PDF DO RELATÓRIO", type="primary"):
    if not area:
        st.error("Preencha o nome da Área.")
    else:
        pdf_bytes = gerar_pdf()
        st.success("Relatório gerado!")
        st.download_button(
            label="Baixar PDF Agora",
            data=pdf_bytes,
            file_name=f"Relatorio_{area}_{inicio_analise}.pdf",
            mime="application/pdf"
        )