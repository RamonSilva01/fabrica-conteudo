"""
Aplicação Streamlit: Fábrica de IA - v11.0 (Seletor Manual de Produto)
"""

import streamlit as st
import os
import json
from datetime import datetime
from content_processor import process_pdf_to_content, process_image_direct, regenerate_single_platform

# --- STATE MANAGEMENT ---
def reset_session_state():
    keys = ["last_result", "last_filename", "contents"]
    for key in keys:
        if key in st.session_state: del st.session_state[key]

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="🏭 Fábrica de IA", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .main { padding: 2rem; }
    .streamlit-expanderHeader { background-color: #f0f2f6 !important; color: #000 !important; font-weight: bold; }
    .stTextArea textarea { background-color: #fff !important; color: #333 !important; }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] { background-color: #e1f5fe; color: #0077b5; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🏭 Fábrica de IA: Editor Chefe")

# SIDEBAR
with st.sidebar:
    st.header("Configuração")
    api_key = st.text_input("API Key OpenAI", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    if api_key: os.environ["OPENAI_API_KEY"] = api_key
    
    st.divider()
    
    # --- NOVO: SELETOR DE PRODUTO ---
    st.subheader("🛠️ Tipo de Produto")
    product_mapping = {"Detectar Automático": "auto", "🏃 Esteira (Creator)": "esteira", "🧍 Scanner (Visbody)": "scanner"}
    product_selection = st.radio(
        "O que estamos analisando?",
        options=list(product_mapping.keys()),
        index=0,
        help="Force a IA a reconhecer o produto correto se ela estiver confusa."
    )
    selected_mode = product_mapping[product_selection]
    # --------------------------------

    st.divider()
    if "total_processed" in st.session_state:
        st.metric("Arquivos", st.session_state.total_processed)

if "total_processed" not in st.session_state: st.session_state.total_processed = 0

# ABAS GERAIS
tab_up, tab_res = st.tabs(["📤 Upload", "📚 Resultados"])

with tab_up:
    col_up, col_info = st.columns([2, 1])
    with col_up:
        uploaded_file = st.file_uploader("Arquivo (PDF/Img)", type=["pdf","png","jpg"], on_change=reset_session_state)
    
    with col_info:
        if selected_mode == "esteira":
            st.success("✅ Modo ESTEIRA Ativado. A IA vai focar em corrida e treino.")
        elif selected_mode == "scanner":
            st.info("✅ Modo SCANNER Ativado. A IA vai focar em avaliação 3D.")
        else:
            st.warning("⚠️ Modo Automático. Se a IA errar, selecione o produto na esquerda.")

    if uploaded_file and st.button("🚀 Gerar Estratégia", type="primary", use_container_width=True):
        if not os.getenv("OPENAI_API_KEY"):
            st.error("Sem API Key!")
        else:
            reset_session_state()
            prog = st.progress(0)
            status = st.empty()
            
            try:
                content_data = None
                if uploaded_file.type == "application/pdf":
                    status.text(f"Lendo PDF (Modo: {selected_mode})...")
                    prog.progress(20)
                    temp = f"temp_{datetime.now().timestamp()}.pdf"
                    with open(temp, "wb") as f: f.write(uploaded_file.getbuffer())
                    
                    # Passando o modo selecionado
                    content_data = process_pdf_to_content(temp, product_mode=selected_mode)
                    
                    if os.path.exists(temp): os.remove(temp)
                else:
                    status.text(f"Analisando Imagem (Modo: {selected_mode})...")
                    prog.progress(40)
                    
                    # Passando o modo selecionado
                    content_data = process_image_direct(uploaded_file.getvalue(), product_mode=selected_mode)

                if content_data and "contents" in content_data:
                    prog.progress(100)
                    status.text("Sucesso!")
                    st.session_state.last_result = content_data
                    st.session_state.last_filename = uploaded_file.name
                    st.session_state.total_processed += 1
                    st.rerun()
                else:
                    st.error(f"Erro: {content_data.get('error')}")
            except Exception as e:
                st.error(f"Erro: {e}")

with tab_res:
    if "last_result" in st.session_state and st.session_state.last_result:
        data = st.session_state.last_result
        contents = data.get("contents", [])
        raw_context = data.get("raw_context")
        context_type = data.get("context_type")
        # Recupera o modo que foi usado na geração original
        saved_mode = data.get("product_mode", "auto")

        st.subheader(f"Estratégia: {st.session_state.last_filename}")
        
        for i, item in enumerate(contents):
            angulo = item.get('angulo', f'Opção {i+1}')
            
            with st.expander(f"📌 {angulo}", expanded=True):
                tab_insta, tab_linked = st.tabs(["📸 Instagram", "💼 LinkedIn"])
                
                with tab_insta:
                    st.text_area("Legenda", item.get('instagram',''), height=300, key=f"txt_inst_{i}")
                    if raw_context:
                        if st.button("🔄 Refazer Insta", key=f"btn_inst_{i}"):
                            with st.spinner("Reescrevendo..."):
                                # Passa o saved_mode para garantir consistência
                                new_content = regenerate_single_platform(raw_context, context_type, angulo, "instagram", saved_mode)
                                if "new_text" in new_content:
                                    st.session_state.last_result['contents'][i]['instagram'] = new_content['new_text']
                                    st.rerun()
                
                with tab_linked:
                    st.text_area("Post", item.get('linkedin',''), height=300, key=f"txt_link_{i}")
                    if raw_context:
                        if st.button("🔄 Refazer LinkedIn", key=f"btn_link_{i}"):
                            with st.spinner("Reescrevendo..."):
                                # Passa o saved_mode para garantir consistência
                                new_content = regenerate_single_platform(raw_context, context_type, angulo, "linkedin", saved_mode)
                                if "new_text" in new_content:
                                    st.session_state.last_result['contents'][i]['linkedin'] = new_content['new_text']
                                    st.rerun()

    else:
        st.info("Aguardando geração...")
