"""
Aplicação Streamlit: Fábrica de IA - v15.0 (Auto-Detect Universal)
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
st.set_page_config(page_title="🏭 Fábrica de IA Universal", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .main { padding: 2rem; }
    .streamlit-expanderHeader { background-color: #f0f2f6 !important; color: #000 !important; font-weight: bold; }
    .stTextArea textarea { background-color: #fff !important; color: #333 !important; }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] { background-color: #e1f5fe; color: #0077b5; font-weight: bold; }
    .detect-box { border: 1px solid #28a745; background-color: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

st.title("🏭 Fábrica de IA: Multi-Produto Universal")
st.markdown("Suba qualquer imagem ou PDF. A IA identificará o produto automaticamente e criará a estratégia B2B/B2C ideal.")

# SIDEBAR
with st.sidebar:
    st.header("Configuração")
    api_key = st.text_input("API Key OpenAI", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    if api_key: os.environ["OPENAI_API_KEY"] = api_key
    
    st.divider()
    if "total_processed" in st.session_state:
        st.metric("Arquivos", st.session_state.total_processed)

if "total_processed" not in st.session_state: st.session_state.total_processed = 0

# ABAS
tab_up, tab_res = st.tabs(["📤 Upload Inteligente", "📚 Resultados"])

with tab_up:
    col_up, col_info = st.columns([2, 1])
    with col_up:
        uploaded_file = st.file_uploader("Arquivo (PDF/Img)", type=["pdf","png","jpg"], on_change=reset_session_state)
    
    with col_info:
        st.info("💡 **Dica:** O sistema agora detecta marca e modelo sozinho. Teste com esteiras, scanners, tênis ou qualquer produto!")

    if uploaded_file and st.button("🚀 Identificar e Gerar", type="primary", use_container_width=True):
        if not os.getenv("OPENAI_API_KEY"):
            st.error("Sem API Key!")
        else:
            reset_session_state()
            prog = st.progress(0)
            status = st.empty()
            
            try:
                content_data = None
                status.text("🕵️ IA analisando o produto...")
                prog.progress(20)

                if uploaded_file.type == "application/pdf":
                    temp = f"temp_{datetime.now().timestamp()}.pdf"
                    with open(temp, "wb") as f: f.write(uploaded_file.getbuffer())
                    content_data = process_pdf_to_content(temp)
                    if os.path.exists(temp): os.remove(temp)
                else:
                    content_data = process_image_direct(uploaded_file.getvalue())

                if content_data and "contents" in content_data:
                    prog.progress(100)
                    status.text("✅ Concluído!")
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
        
        # MOSTRA O QUE FOI DETECTADO
        detected = data.get("detected_info", {})
        prod_nome = detected.get('nome', 'Produto')
        prod_cat = detected.get('categoria', 'Geral')
        
        st.markdown(f"""
        <div class="detect-box">
            <strong>🕵️ Produto Identificado:</strong> {prod_nome} <br>
            <strong>📂 Categoria:</strong> {prod_cat}
        </div>
        """, unsafe_allow_html=True)

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
                                new_content = regenerate_single_platform(raw_context, context_type, angulo, "instagram", detected)
                                if "new_text" in new_content:
                                    st.session_state.last_result['contents'][i]['instagram'] = new_content['new_text']
                                    st.rerun()
                
                with tab_linked:
                    st.text_area("Post", item.get('linkedin',''), height=300, key=f"txt_link_{i}")
                    if raw_context:
                        if st.button("🔄 Refazer LinkedIn", key=f"btn_link_{i}"):
                            with st.spinner("Reescrevendo..."):
                                new_content = regenerate_single_platform(raw_context, context_type, angulo, "linkedin", detected)
                                if "new_text" in new_content:
                                    st.session_state.last_result['contents'][i]['linkedin'] = new_content['new_text']
                                    st.rerun()

    else:
        st.info("Faça o upload para começar.")
