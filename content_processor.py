"""
Módulo de Processamento - Versão 9.0 (Blindada contra Erros + Prompts Premium)
"""

import os
import json
import fitz  # PyMuPDF
import base64
import re
from openai import OpenAI

def get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key: return None
    return OpenAI(api_key=api_key)

def encode_image_from_bytes(image_bytes):
    return base64.b64encode(image_bytes).decode("utf-8")

def encode_pixmap(pix):
    return base64.b64encode(pix.tobytes("png")).decode("utf-8")

def clean_json_response(content):
    """
    Remove blocos de código Markdown (```json ... ```) se a IA incluir.
    Garante que o json.loads funcione.
    """
    if not content: return None
    # Remove ```json no início e ``` no final
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1)
    # Tenta remover apenas ``` se o formato for diferente
    return content.strip().replace("```json", "").replace("```", "")

# --- PROMPTS DE ALTA PERFORMANCE (Mantidos) ---

def get_common_system_prompt():
    return """
    Você é um Estrategista de Conteúdo Sênior e Copywriter de Elite para a marca VISBODY.
    Sua missão: Criar conteúdo que posiciona a marca como líder tecnológica no mercado fitness/médico.
    
    === SUAS REGRAS DE GÊNERO (Obrigatorio) ===
    - SE ESTEIRA (Treadmill, Creator) -> FEMININO ("A Creator 600", "A esteira").
    - SE SCANNER (Body Scanner, Visbody) -> MASCULINO ("O Visbody", "O scanner").
    
    === PERFIL DE REDE SOCIAL (RIGOROSO) ===
    
    1. INSTAGRAM (Ousado & Visual):
       - O texto DEVE ser chamativo ("scroll-stopper"). Comece com uma frase de impacto.
       - Use emojis para quebrar o texto e dar ritmo ⚡🔥🚀.
       - HASHTAGS OBRIGATÓRIAS: Use SEMPRE #Visbody e #[NomeDoEquipamento] (Ex: #Creator600, #VisbodyR6). Adicione tags de nicho.
       - Tom: Inspirador, enérgico, focado em lifestyle e inovação.
       
    2. LINKEDIN (Robusto & Autoridade):
       - O texto DEVE ser denso e valioso. Nada de frases curtas e rasas.
       - Estrutura: Título provocativo -> Contexto de Mercado/Dor -> Solução Técnica Profunda -> Impacto no ROI/Negócio.
       - Foco: Tecnologia, Biomecânica, Retorno sobre Investimento, Diferencial Competitivo.
       - Tom: Profissional, Especialista, "Thought Leader".
    """

def get_json_structure_instruction(qtd_str):
    return f"""
    Responda ESTRITAMENTE com este JSON:
    {{
        "contents": [
            {{
                "angulo": "Nome Criativo do Ângulo",
                "instagram": "Legenda completa para Insta...",
                "linkedin": "Artigo completo para LinkedIn..."
            }}
            ... (Gere exatamente {qtd_str} variações)
        ]
    }}
    """

# --- REGENERAÇÃO CIRÚRGICA ---

def regenerate_single_platform(context_data, context_type, angle_name, target_platform):
    client = get_client()
    if not client: return {"error": "Sem API Key"}

    instruction = ""
    if target_platform == "instagram":
        instruction = """
        FOCO NO INSTAGRAM:
        - Quero algo MAIS CHAMATIVO que a versão anterior.
        - Comece com uma pergunta ou afirmação polêmica/forte.
        - Destaque o design e a experiência.
        - Use emojis e hashtags (#Visbody).
        """
    else:
        instruction = """
        FOCO NO LINKEDIN:
        - Quero algo MAIS ROBUSTO e PROFISSIONAL.
        - Aprofunde na parte técnica ou de negócios.
        - Escreva parágrafos bem construídos.
        - Foque em como isso revoluciona o mercado.
        """

    prompt_full = f"""
    REESCREVER CONTEÚDO PARA: {target_platform.upper()}
    Ângulo: "{angle_name}"
    
    {instruction}
    
    Retorne APENAS JSON: {{ "new_text": "..." }}
    """

    try:
        messages = [{"role": "system", "content": get_common_system_prompt()}]
        
        if context_type == "text":
            messages.append({
                "role": "user", 
                "content": f"Base Técnica:\n---\n{context_data[:35000]}\n---\n{prompt_full}"
            })
        else:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_full},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{context_data}", "detail": "high"}}
                ]
            })

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if not content: return {"error": "IA retornou vazio."}
        
        return json.loads(clean_json_response(content))

    except Exception as e:
        return {"error": str(e)}

# --- FUNÇÕES PRINCIPAIS ---

def process_image_direct(image_bytes):
    client = get_client()
    if not client: return {"error": "API Key não configurada"}

    try:
        base64_image = encode_image_from_bytes(image_bytes)
        
        prompt_text = """
        Analise esta imagem da VISBODY.
        Crie 3 estratégias de conteúdo distintas (Ex: Visual, Técnico, Vendas).
        Lembre-se: Instagram deve ser VIBRANTE e LinkedIn deve ser ROBUSTO/TÉCNICO.
        Identifique o nome do produto na imagem para usar nas hashtags.
        """ + get_json_structure_instruction("3")
        
        user_message = [
            {"type": "text", "text": prompt_text},
            # Ajuste: Header genérico jpeg funciona para png/jpg na maioria dos casos com GPT-4o
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "high"}}
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": get_common_system_prompt()}, {"role": "user", "content": user_message}],
            response_format={"type": "json_object"},
            max_tokens=3500
        )
        
        # --- SEGURANÇA ADICIONADA AQUI ---
        content = response.choices[0].message.content
        
        if not content:
            return {"error": "A IA retornou uma resposta vazia. Tente novamente."}
            
        try:
            # Limpa e converte
            clean_content = clean_json_response(content)
            result = json.loads(clean_content)
        except json.JSONDecodeError:
            return {"error": "Erro ao ler JSON da IA. Tente novamente."}
            
        result["raw_context"] = base64_image
        result["context_type"] = "image"
        return result
        
    except Exception as e:
        return {"error": f"Erro processamento imagem: {str(e)}"}

def process_pdf_to_content(pdf_path):
    client = get_client()
    if not client: return {"error": "API Key não configurada"}

    try:
        doc = fitz.open(pdf_path)
        is_scanned = True 
        limit_pages = 15 
        text_content = []
        image_content = []

        for i, page in enumerate(doc):
            if i >= limit_pages: break
            text = page.get_text()
            if len(text.strip()) > 50:
                is_scanned = False
                text_content.append(text)
            if is_scanned:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                image_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{encode_pixmap(pix)}", "detail": "high"}
                })
        doc.close()

        prompt_instruction = """
        Analise este manual/documento técnico da VISBODY.
        Extraia 5 Tópicos de Alto Valor.
        Para cada tópico, crie um post de Instagram (Vibrante/Hashtags Certas) e um artigo LinkedIn (Profundo/Técnico).
        """ + get_json_structure_instruction("5")

        result = {}
        
        if not is_scanned:
            full_text = "\n".join(text_content)
            prompt = f"Material Técnico:\n---\n{full_text[:45000]}\n---\n{prompt_instruction}"
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": get_common_system_prompt()}, {"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
        else:
            if not image_content: return {"error": "PDF vazio"}
            user_message = [{"type": "text", "text": prompt_instruction}]
            user_message.extend(image_content)
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": get_common_system_prompt()}, {"role": "user", "content": user_message}],
                response_format={"type": "json_object"},
                max_tokens=4000
            )
            content = response.choices[0].message.content

        # --- SEGURANÇA ---
        if not content:
            return {"error": "A IA retornou resposta vazia."}
            
        result = json.loads(clean_json_response(content))
        
        if not is_scanned:
            result["raw_context"] = full_text
            result["context_type"] = "text"
        else:
            result["raw_context"] = None 
            result["context_type"] = "scanned_pdf"

        return result

    except Exception as e:
        return {"error": f"Erro processamento: {str(e)}"}