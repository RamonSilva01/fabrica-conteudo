"""
Módulo de Processamento - Versão 11.0 (Com Trava Manual de Produto)
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
    if not content: return None
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, content, re.DOTALL)
    if match: return match.group(1)
    return content.strip().replace("```json", "").replace("```", "")

# --- PROMPTS ADAPTÁVEIS ---

def get_system_prompt_by_mode(mode):
    """
    Retorna o prompt exato para o tipo de produto selecionado.
    mode: 'auto', 'esteira', 'scanner'
    """
    
    base_prompt = """
    ATUE COMO: Diretor de Marketing Global da VISBODY.
    SUA MISSÃO: Criar conteúdo B2B (LinkedIn) e B2C (Instagram) de alta conversão.
    """
    
    # TRAVA DE CONTEXTO
    if mode == "esteira":
        context_rule = """
        === PRODUTO DEFINIDO: ESTEIRA (TREADMILL) ===
        - Você ESTÁ vendo uma ESTEIRA (Provavelmente a Creator 600).
        - GÊNERO OBRIGATÓRIO: FEMININO ("A Creator 600", "A esteira").
        - FOCO: Corrida, Treino, Biomecânica, Lona, Amortecimento, Prevenção de Lesões.
        - PROIBIDO: Falar de "escaneamento corporal" ou "análise 3D" como função principal (a menos que seja um recurso da tela da esteira).
        """
    elif mode == "scanner":
        context_rule = """
        === PRODUTO DEFINIDO: BODY SCANNER 3D ===
        - Você ESTÁ vendo um SCANNER CORPORAL (Visbody R6, S30, etc).
        - GÊNERO OBRIGATÓRIO: MASCULINO ("O Visbody", "O scanner").
        - FOCO: Avaliação Física, Bioimpedância, Postura, Precisão Clínica.
        - PROIBIDO: Falar de "corrida" ou "treino aeróbico".
        """
    else: # Auto
        context_rule = """
        === IDENTIFICAÇÃO AUTOMÁTICA ===
        - Analise a imagem/texto para identificar se é ESTEIRA ou SCANNER.
        - SE ESTEIRA -> Use Feminino ("A Creator"). Foco em Treino.
        - SE SCANNER -> Use Masculino ("O Visbody"). Foco em Avaliação.
        """

    style_rules = """
    === ESTILO DE ESCRITA ===
    1. LINKEDIN (Autoridade B2B):
       - Escreva para donos de academia/clínicas.
       - Foco em ROI, Retenção, Tecnologia e Diferencial Competitivo.
       - Tom: CEO para CEO.
       
    2. INSTAGRAM (Desejo Visual):
       - Use o método AIDA (Atenção, Interesse, Desejo, Ação).
       - Hashtags OBRIGATÓRIAS: #Visbody + Nome do Produto.
       - Tom: Magnético, Futurista.
    """
    
    return base_prompt + context_rule + style_rules

def get_json_structure_instruction(qtd_str):
    return f"""
    Responda ESTRITAMENTE com este JSON:
    {{
        "contents": [
            {{
                "angulo": "Nome do Ângulo",
                "instagram": "Texto...",
                "linkedin": "Texto..."
            }}
            ... (x{qtd_str})
        ]
    }}
    """

# --- REGENERAÇÃO ---

def regenerate_single_platform(context_data, context_type, angle_name, target_platform, product_mode="auto"):
    client = get_client()
    if not client: return {"error": "Sem API Key"}

    instruction = ""
    if target_platform == "instagram":
        instruction = "CORREÇÃO INSTAGRAM: Quero algo MAIS MAGNÉTICO e VISUAL. Use AIDA."
    else:
        instruction = "CORREÇÃO LINKEDIN: Quero algo MAIS TÉCNICO e DE NEGÓCIOS. Foco em ROI."

    prompt_full = f"""
    REESCREVER: {target_platform.upper()}
    Contexto: "{angle_name}"
    {instruction}
    Retorne APENAS JSON: {{ "new_text": "..." }}
    """

    try:
        # Usa o prompt correto baseado no modo escolhido
        messages = [{"role": "system", "content": get_system_prompt_by_mode(product_mode)}]
        
        content_payload = f"Contexto:\n---\n{context_data[:35000]}\n---\n{prompt_full}" if context_type == "text" else [
            {"type": "text", "text": prompt_full},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{context_data}", "detail": "high"}}
        ]
        
        messages.append({"role": "user", "content": content_payload})

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={"type": "json_object"}
        )
        return json.loads(clean_json_response(response.choices[0].message.content))
    except Exception as e:
        return {"error": str(e)}

# --- PROCESSAMENTO PRINCIPAL ---

def process_image_direct(image_bytes, product_mode="auto"):
    client = get_client()
    if not client: return {"error": "API Key não configurada"}

    try:
        base64_image = encode_image_from_bytes(image_bytes)
        
        # Reforço no prompt do usuário também
        product_instruction = ""
        if product_mode == "esteira":
            product_instruction = "ISSO É UMA ESTEIRA. Ignore qualquer semelhança com scanner. Venda os benefícios da CORRIDA."
        elif product_mode == "scanner":
            product_instruction = "ISSO É UM SCANNER. Ignore qualquer semelhança com esteira. Venda os benefícios da AVALIAÇÃO."

        prompt_text = f"""
        Analise esta imagem. {product_instruction}
        Crie 3 estratégias de conteúdo PREMIUM (B2B e B2C).
        Identifique o modelo exato para as hashtags.
        """ + get_json_structure_instruction("3")
        
        user_message = [
            {"type": "text", "text": prompt_text},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "high"}}
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": get_system_prompt_by_mode(product_mode)}, {"role": "user", "content": user_message}],
            response_format={"type": "json_object"},
            max_tokens=4000
        )
        
        result = json.loads(clean_json_response(response.choices[0].message.content))
        result["raw_context"] = base64_image
        result["context_type"] = "image"
        # Importante: Salvar o modo usado para a regeneração saber depois
        result["product_mode"] = product_mode 
        return result
        
    except Exception as e:
        return {"error": f"Erro imagem: {str(e)}"}

def process_pdf_to_content(pdf_path, product_mode="auto"):
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

        prompt_instruction = f"""
        Analise este material.
        Extraia 5 Pontos de Ouro (Golden Nuggets) de negócio e tecnologia.
        Modo de Produto: {product_mode.upper()}.
        """ + get_json_structure_instruction("5")

        result = {}
        content_raw = ""
        system_prompt = get_system_prompt_by_mode(product_mode)

        if not is_scanned:
            full_text = "\n".join(text_content)
            prompt = f"Material Técnico:\n---\n{full_text[:50000]}\n---\n{prompt_instruction}"
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            content_raw = response.choices[0].message.content
            result = json.loads(clean_json_response(content_raw))
            result["raw_context"] = full_text
            result["context_type"] = "text"
        else:
            if not image_content: return {"error": "PDF vazio"}
            user_message = [{"type": "text", "text": prompt_instruction}]
            user_message.extend(image_content)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}],
                response_format={"type": "json_object"},
                max_tokens=4000
            )
            content_raw = response.choices[0].message.content
            result = json.loads(clean_json_response(content_raw))
            result["raw_context"] = None
            result["context_type"] = "scanned_pdf"
            
        result["product_mode"] = product_mode
        return result

    except Exception as e:
        return {"error": f"Erro processamento: {str(e)}"}
