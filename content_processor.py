"""
Módulo de Processamento - Versão 15.0 (Universal Auto-Detect)
Foco: Identificação automática de QUALQUER produto para gerar conteúdo B2B/B2C de alta qualidade.
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

# --- AGENTE 1: O DETETIVE (IDENTIFICA O PRODUTO) ---

def detect_product_info(context_data, context_type):
    """
    Analisa a imagem ou texto para identificar O QUE está sendo vendido.
    Retorna um dicionário com Nome, Categoria e Público-Alvo.
    """
    client = get_client()
    
    prompt_detect = """
    ANALISE ESTE INPUT COM PRECISÃO.
    Identifique:
    1. Nome do Produto (Modelo específico se visível).
    2. Marca (Se visível).
    3. Categoria (Ex: Esteira, Scanner, Software, Café, Carro).
    4. Principal Diferencial Técnico visível.
    
    Responda APENAS JSON:
    {
        "nome": "...",
        "marca": "...",
        "categoria": "...",
        "diferencial": "..."
    }
    """
    
    try:
        messages = [{"role": "system", "content": "Você é um especialista em reconhecimento de produtos industriais e comerciais."}]
        
        content_payload = f"Texto:\n---\n{context_data[:10000]}\n---\n{prompt_detect}" if context_type == "text" else [
            {"type": "text", "text": prompt_detect},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{context_data}", "detail": "low"}} # Low detail é mais barato e rápido para detecção
        ]
        
        messages.append({"role": "user", "content": content_payload})
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=300
        )
        return json.loads(clean_json_response(response.choices[0].message.content))
    except:
        # Fallback se falhar
        return {"nome": "Equipamento Premium", "marca": "Sua Marca", "categoria": "Tecnologia", "diferencial": "Alta Performance"}

# --- AGENTE 2: O COPYWRITER (DYNAMIC SYSTEM PROMPT) ---

def get_dynamic_system_prompt(info):
    """
    Cria uma persona customizada baseada no produto detectado.
    """
    nome = info.get('nome', 'Produto')
    categoria = info.get('categoria', 'Equipamento')
    diferencial = info.get('diferencial', 'Tecnologia')
    
    return f"""
    ATUE COMO: Diretor de Marketing Especialista em {categoria}.
    PRODUTO EM FOCO: {nome} ({categoria}).
    DIFERENCIAL CHAVE: {diferencial}.
    
    === ESTRATÉGIA DE CANAL ===
    
    🔴 INSTAGRAM (B2C/Visual):
       - Foco: Desejo, Status e "Efeito Uau".
       - Use hashtags específicas do nicho de {categoria}.
       - Método AIDA (Atenção, Interesse, Desejo, Ação).
    
    🔵 LINKEDIN (B2B/Negócios):
       - OBRIGATÓRIO: Escreva um ARTIGO DE ANÁLISE TÉCNICA/COMERCIAL.
       - Estrutura Rígida: 
         1. Título (Impacto no Negócio)
         2. O Problema do Mercado (Sem esse produto)
         3. A Solução {nome} (Hardware/Tecnologia)
         4. O ROI (Lucro/Economia/Eficiência)
       - MÍNIMO 150 PALAVRAS.
       - Tom: Consultivo, sério, focado em dinheiro e eficiência.
       
    === EXEMPLO DE TOM (LINKEDIN) ===
    "Não invista em equipamentos, invista em ativos que geram retorno. A tecnologia X reduz o custo operacional em 20% e aumenta a retenção do cliente..."
    """

def get_json_structure_instruction(qtd_str):
    return f"""
    Responda JSON:
    {{
        "contents": [
            {{
                "angulo": "Nome do Ângulo",
                "instagram": "Legenda...",
                "linkedin": "Artigo B2B Robusto..."
            }}
            ... (x{qtd_str})
        ]
    }}
    """

# --- REGENERAÇÃO ---

def regenerate_single_platform(context_data, context_type, angle_name, target_platform, product_info):
    client = get_client()
    
    nome_produto = product_info.get('nome', 'O Produto')
    
    instruction = ""
    if target_platform == "instagram":
        instruction = f"CORREÇÃO INSTAGRAM: Quero algo mais VIBRANTE sobre {nome_produto}. Use gatilhos de exclusividade."
    else:
        instruction = f"CORREÇÃO LINKEDIN: Aprofunde na parte de NEGÓCIOS de {nome_produto}. Fale de ROI e Vantagem Competitiva. Texto longo."

    prompt_full = f"""
    REESCREVER: {target_platform.upper()}
    Contexto: "{angle_name}"
    {instruction}
    Retorne JSON: {{ "new_text": "..." }}
    """

    try:
        # Prompt dinâmico aqui também
        messages = [{"role": "system", "content": get_dynamic_system_prompt(product_info)}]
        
        content_payload = f"Contexto:\n---\n{context_data[:30000]}\n---\n{prompt_full}" if context_type == "text" else [
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

def process_image_direct(image_bytes):
    client = get_client()
    if not client: return {"error": "Sem API Key"}

    try:
        base64_image = encode_image_from_bytes(image_bytes)
        
        # 1. DETECÇÃO AUTOMÁTICA
        detected_info = detect_product_info(base64_image, "image")
        print(f"🕵️ Produto Detectado: {detected_info}")

        # 2. GERAÇÃO DE CONTEÚDO
        prompt_text = f"""
        Analise a imagem de {detected_info['nome']}.
        Crie 3 estratégias de conteúdo para vender este {detected_info['categoria']}.
        Para o LinkedIn, foque em como isso gera lucro para o comprador.
        """ + get_json_structure_instruction("3")
        
        user_message = [
            {"type": "text", "text": prompt_text},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "high"}}
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": get_dynamic_system_prompt(detected_info)}, 
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            max_tokens=4000
        )
        
        result = json.loads(clean_json_response(response.choices[0].message.content))
        result["raw_context"] = base64_image
        result["context_type"] = "image"
        result["detected_info"] = detected_info # Salva o que ele detectou para usar depois
        return result
        
    except Exception as e:
        return {"error": f"Erro: {str(e)}"}

def process_pdf_to_content(pdf_path):
    client = get_client()
    if not client: return {"error": "Sem API Key"}

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
        
        # Prepara contexto para detecção
        context_for_detection = ""
        context_type = "text"
        detection_payload = ""

        if not is_scanned:
            full_text = "\n".join(text_content)
            context_for_detection = full_text[:5000] # Primeiros 5k caracteres para detectar
            detection_payload = full_text
            context_type = "text"
        else:
            if not image_content: return {"error": "PDF vazio"}
            # Pega primeira imagem para detectar
            context_for_detection = image_content[0]['image_url']['url'].split(",")[1]
            context_type = "image"

        # 1. DETECÇÃO AUTOMÁTICA
        detected_info = detect_product_info(context_for_detection, context_type)
        print(f"🕵️ PDF Detectado: {detected_info}")

        # 2. GERAÇÃO
        prompt_instruction = f"""
        Analise o material de {detected_info['nome']}.
        Extraia 5 Pontos de Ouro.
        LinkedIn: Artigos de Negócio sobre {detected_info['categoria']}.
        """ + get_json_structure_instruction("5")

        result = {}
        content_raw = ""
        system_prompt = get_dynamic_system_prompt(detected_info)

        if not is_scanned:
            prompt = f"Material:\n---\n{full_text[:50000]}\n---\n{prompt_instruction}"
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
            
        result["detected_info"] = detected_info
        return result

    except Exception as e:
        return {"error": f"Erro processamento: {str(e)}"}
