"""
Módulo de Processamento - Versão 12.0 (Hardcore B2B - LinkedIn Profundo)
Foco: Eliminar frases curtas e forçar artigos de liderança de pensamento.
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

# --- O CÉREBRO DA OPERAÇÃO ---

def get_system_prompt_by_mode(mode):
    """
    Define a personalidade e as REGRAS RÍGIDAS de estrutura.
    """
    
    product_context = ""
    if mode == "esteira":
        product_context = "PRODUTO: Esteira Profissional (Creator 600). Foco: Biomecânica, Durabilidade, Tecnologia de Treino."
    elif mode == "scanner":
        product_context = "PRODUTO: Body Scanner 3D (Visbody). Foco: Precisão Clínica, Avaliação Postural, Bioimpedância."
    else:
        product_context = "PRODUTO: Equipamento de Alta Tecnologia Visbody."

    return f"""
    ATUE COMO: Consultor Sênior de Negócios Fitness e Tecnologia Médica.
    {product_context}
    
    === DIFERENCIAÇÃO RADICAL DE CANAIS ===

    🔴 PARA O INSTAGRAM (B2C/Visual):
       - Objetivo: Desejo e Curiosidade.
       - Estrutura: Gancho forte ("Você nunca correu assim") -> Benefício Visual -> CTA.
       - Use Emojis e Hashtags (#Visbody).
    
    🔵 PARA O LINKEDIN (B2B/Negócios) - LEIA COM ATENÇÃO:
       - PROIBIDO: Frases curtas, slogans vazios ("Treine com propósito"), ou linguagem de "vendedor de loja".
       - OBRIGATÓRIO: O texto deve parecer um MINI-ARTIGO ou UMA ANÁLISE DE MERCADO.
       - ESTRUTURA RÍGIDA:
         1. **A Dor do Mercado**: Comece falando de um problema do dono da academia/clínica (ex: rotatividade, equipamentos que quebram, avaliações imprecisas).
         2. **A Virada Tecnológica**: Apresente a tecnologia da Visbody como a solução técnica para esse problema. Use termos técnicos.
         3. **O Resultado (ROI)**: Fale de retenção de alunos, aumento de ticket médio ou economia operacional.
       - TAMANHO: Mínimo de 3 parágrafos bem construídos.
       - TOM: Sobrio, Analítico, "Thought Leader".
    """

def get_json_structure_instruction(qtd_str):
    return f"""
    Responda ESTRITAMENTE com este JSON:
    {{
        "contents": [
            {{
                "angulo": "Nome do Ângulo (Ex: Foco em ROI, Foco em Tecnologia)",
                "instagram": "Legenda vibrante para Insta...",
                "linkedin": "Artigo denso e estruturado para LinkedIn (Mínimo 100 palavras)..."
            }}
            ... (x{qtd_str})
        ]
    }}
    """

# --- REGENERAÇÃO COM INSTRUÇÃO DE EXPANSÃO ---

def regenerate_single_platform(context_data, context_type, angle_name, target_platform, product_mode="auto"):
    client = get_client()
    if not client: return {"error": "Sem API Key"}

    instruction = ""
    if target_platform == "instagram":
        instruction = """
        CORREÇÃO INSTAGRAM:
        - O texto anterior estava chato. Quero algo VIBRANTE.
        - Use Gatilhos Mentais de Exclusividade e Novidade.
        - Curto, direto e visual.
        """
    else:
        instruction = """
        CORREÇÃO LINKEDIN (CRÍTICO):
        - O texto anterior estava MUITO CURTO e RASO. Parecia Twitter.
        - Quero um texto DENSO, focado em NEGÓCIOS.
        - Aprofunde: Como isso ajuda o gestor a ganhar mais dinheiro ou perder menos alunos?
        - Cite especificações técnicas como vantagens competitivas.
        - Escreva pelo menos 3 parágrafos robustos.
        """

    prompt_full = f"""
    REESCREVER: {target_platform.upper()}
    Contexto do Ângulo: "{angle_name}"
    {instruction}
    Retorne APENAS JSON: {{ "new_text": "..." }}
    """

    try:
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
        
        product_instruction = ""
        if product_mode == "esteira":
            product_instruction = "Foco TOTAL na Esteira Creator 600. Ignore scanners."
        elif product_mode == "scanner":
            product_instruction = "Foco TOTAL no Body Scanner Visbody. Ignore esteiras."

        prompt_text = f"""
        Analise esta imagem. {product_instruction}
        
        Crie 3 estratégias de conteúdo.
        IMPORTANTE: O LinkedIn deve ser um conteúdo de CONSULTORIA, não de propaganda. Ensine algo ao leitor.
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
        Analise este material técnico.
        Extraia 5 Pontos de Negócio (Golden Nuggets).
        
        PARA O LINKEDIN: Transforme cada ponto em uma análise de mercado. 
        Explique POR QUE essa tecnologia específica gera mais lucro ou eficiência para o dono do negócio.
        NÃO escreva frases motivacionais. Escreva sobre NEGÓCIOS.
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
