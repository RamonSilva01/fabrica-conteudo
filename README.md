# 🏭 Fábrica de IA — Editor Chefe (Streamlit + OpenAI + PyMuPDF)

Uma aplicação **prática e “produção-friendly”** para transformar **PDFs/manuais técnicos** e **imagens de produto** em estratégias completas de conteúdo, gerando automaticamente:

- **Legenda para Instagram** (vibrante, “scroll-stopper”, com hashtags obrigatórias)
- **Texto/artigo para LinkedIn** (robusto, técnico, com foco em valor e ROI)
- E ainda permite **regenerar cirurgicamente** apenas o Instagram ou apenas o LinkedIn por ângulo ✅

> Este projeto foi desenhado para um fluxo de marketing moderno: você sobe um PDF/Imagem, a IA entende o contexto, gera múltiplos ângulos e você edita/refaz por plataforma sem reprocessar tudo.

---

## ✨ Principais recursos

- **Upload de PDF / PNG / JPG** via Streamlit
- **Detecção inteligente de PDF digital vs. PDF escaneado**
  - PDF com texto: extrai texto e usa como base
  - PDF escaneado: renderiza páginas como imagens e envia para visão do modelo
- **Geração em JSON (response_format)**
  - Retorno padronizado e fácil de salvar/editar
- **3 ângulos por imagem** (ex.: Visual, Técnico, Vendas)
- **5 tópicos de alto valor por PDF** (com Instagram + LinkedIn para cada tópico)
- **Regeneração “cirúrgica”**
  - Refaz **somente** o Instagram **ou** somente o LinkedIn de um ângulo específico
- **Blindagem contra erros comuns**
  - Limpeza de resposta com Markdown (```json)
  - Tratamento de JSON vazio/inválido
  - Limites de páginas e cortes de texto para evitar payload gigante

---

## 🧠 Como funciona (visão técnica)

### 1) Backend (`content_processor.py`)
- Lê PDF com **PyMuPDF (fitz)**
- Detecta se há texto relevante nas primeiras páginas
- Se tiver texto:
  - Junta o conteúdo e envia ao modelo para gerar tópicos/ângulos
- Se for escaneado:
  - Renderiza páginas em imagem (pixmap) e envia como `image_url`
- Faz parsing seguro do JSON retornado
- Guarda `raw_context` + `context_type` para permitir **regeneração depois**

### 2) Frontend (`app.py`)
- Interface Streamlit com duas abas:
  - **Upload**
  - **Resultados**
- Para cada ângulo, exibe:
  - Aba **Instagram** com textarea + botão “Refazer só Instagram”
  - Aba **LinkedIn** com textarea + botão “Refazer só LinkedIn”
- Gerencia estado com `st.session_state`

---

## 🧰 Stack

- **Python 3.10+**
- **Streamlit**
- **OpenAI Python SDK**
- **PyMuPDF (fitz)**
- Regex/JSON/Base64 (stdlib)

---

## 🗂️ Estrutura sugerida do repositório

> Ajuste conforme seu repo atual, mas este é o formato mais limpo para GitHub.

fabbrica-ia/
├─ app.py
├─ content_processor.py
├─ requirements.txt
├─ .env.example
├─ .gitignore
└─ README.md

yaml
Copiar código

---

## ✅ Pré-requisitos

- Python **3.10 ou superior**
- Uma **OpenAI API Key**
- (Opcional) `virtualenv`/`venv`

---

## ⚙️ Instalação

### 1) Clone do projeto
```bash
git clone https://github.com/SEU_USUARIO/SEU_REPO.git
cd SEU_REPO
2) Crie e ative um ambiente virtual
Windows (PowerShell)

bash
Copiar código
python -m venv .venv
.venv\Scripts\Activate.ps1
macOS/Linux

bash
Copiar código
python3 -m venv .venv
source .venv/bin/activate
3) Instale as dependências
bash
Copiar código
pip install -r requirements.txt
🔐 Variáveis de ambiente
Você pode configurar a API Key de duas formas:

Opção A) Pelo próprio app (Sidebar)
O app possui um campo “API Key OpenAI” no sidebar e seta OPENAI_API_KEY em runtime.

Opção B) Via .env (recomendado para dev)
Crie um arquivo .env baseado no exemplo:

.env.example

env
Copiar código
OPENAI_API_KEY="SUA_CHAVE_AQUI"
Importante: nunca commite .env no GitHub.

▶️ Como rodar
bash
Copiar código
streamlit run app.py
Abra no navegador:

http://localhost:8501

🧪 Como usar (passo a passo)
Vá na aba 📤 Upload

Envie um arquivo PDF/PNG/JPG

Clique em 🚀 Gerar Estratégia

Vá para a aba 📚 Resultados

Abra os ângulos e:

Copie/edite o texto

Clique em 🔄 Refazer SÓ Instagram ou 🔄 Refazer SÓ LinkedIn quando quiser melhorar apenas uma plataforma

🧾 Formato do JSON retornado
O backend força a IA a responder assim:

json
Copiar código
{
  "contents": [
    {
      "angulo": "Nome Criativo do Ângulo",
      "instagram": "Legenda completa para Insta...",
      "linkedin": "Artigo completo para LinkedIn..."
    }
  ]
}
🛠️ Configurações importantes (do seu código)
Limite de páginas do PDF
No backend:

limit_pages = 15

Isso controla custo e velocidade.

Corte de texto para payload
context_data[:35000] / full_text[:45000]

Evita exceder limites de entrada.

Modelo usado
No seu código está:

model="gpt-4o"

Você pode facilmente parametrizar isso por variável de ambiente, se quiser.

🧯 Troubleshooting
“Sem API Key!”
Configure OPENAI_API_KEY no ambiente ou cole na sidebar do app.

“Erro ao ler JSON da IA”
Normalmente é ruído de formatação.

Seu clean_json_response() já resolve a maioria.

Se ocorrer com frequência, aumente rigidez do prompt (“retorne somente JSON”) e mantenha response_format={"type":"json_object"}.

PDFs escaneados pesados ficam lentos
Reduza limit_pages

Reduza o fitz.Matrix(2, 2) para fitz.Matrix(1.5, 1.5) (menos resolução = mais rápido)

🔒 Boas práticas de segurança
Nunca suba sua API Key no GitHub

Adicione ao .gitignore:

.env

*.pdf temporários (se preferir)

Se for hospedar publicamente, proteja com autenticação (ou ao menos senha)

🗺️ Roadmap (ideias que combinam muito com esse projeto)
 Exportar resultados para .json e .md

 Botão “Copiar” por seção (Instagram/LinkedIn)

 Seleção de idioma/país (pt-BR, es-AR, en-US)

 “Banco de prompts” editável no frontend

 Cache por arquivo (evitar pagar duas vezes pelo mesmo upload)

 Suporte a vídeo (extrair frames / transcrição)

👤 Autor

Projeto desenvolvido por Ramon Silva.
