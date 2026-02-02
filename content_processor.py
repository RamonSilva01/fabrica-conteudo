"""
Módulo de Processamento - Versão 13.0 (Anti-Preguiça / Few-Shot Prompting)
Foco: Forçar textos longos e densos no LinkedIn usando Exemplos Reais.
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

# --- O EXEMPLO DE OURO (A REFERÊNCIA) ---

LINKEDIN_GOLDEN_EXAMPLE = """
exemplo_post_linkedin: "
**Título: Por que academias 'Low Cost' estão perdendo alunos para estúdios de experiência?**

A era da 'esteira alugada' acabou. Dados recentes mostram que a taxa de cancelamento (Churn) é 40% menor em academias que oferecem gamificação e experiências imersivas. O aluno moderno não paga para correr; ele paga para *sentir*.

**O Problema da Monotonia**
O maior inimigo da retenção não é o preço, é o tédio. Uma esteira padrão, onde o aluno encara uma parede por 30 minutos, cria uma percepção de esforço negativo. O resultado? Ele falta, desanima e cancela.

**A Virada Tecnológica: Creator 600**
É aqui que entra a biomecânica aliada à imersão. A Creator 600 não é apenas hardware; é um ecossistema. Com simulação de cenários reais (Real-world Scene) em 4K, ela dissocia a dor do esforço. O aluno corre nos Alpes Suíços enquanto sua frequência cardíaca é monitorada por sensores de precisão clínica.

**Impacto no ROI**
Para o gestor, a conta é simples: Equipamentos de alta experiência permitem cobrar um ticket médio 20% superior e aumentam a vida útil do cliente (LTV). Não é um gasto em equipamento, é um investimento em blindagem de base de clientes.

Você está vendendo treino ou experiência? 🚀
"
"""

# --- O CÉREBRO DA OPERAÇÃO ---

def get_system_prompt_by_mode(mode):
    product_context = ""
    if mode == "esteira":
        product_context = "PRODUTO: Esteira Profissional (Creator 600). Ignore scanners."
    elif mode == "scanner":
        product_context = "PRODUTO: Body Scanner 3D (Visbody). Ignore esteiras."
    else:
        product_context = "PRODUTO: Equipamento de Alta Tecnologia Visbody."

    return f"""
    ATUE COMO: Consultor Sênior de Negócios Fitness (B2B).
    {product_context}
    
    === REGRAS DE CANAL (INEGOCIÁVEIS) ===

    🔴 INSTAGRAM (B2C - Visual):
       - Curto, impactante, visual.
       - Use AIDA (Atenção, Interesse, Desejo, Ação).
       - Hashtags: #Visbody + Produto.
    
    🔵 LINKEDIN (B2B - Profundo):
       - PROIBIDO ESCREVER MENOS DE 150 PALAVRAS.
       - PROIBIDO TEXTO DE "VENDEDOR".
       - O texto DEVE seguir a estrutura do EXEMPLO ABAIXO.
       - Use Títulos em Negrito. Separe por parágrafos.
       - Fale de ROI (Retorno sobre Investimento), Retenção e Tecnologia.
       
    === EXEMPLO DE POST PERFEITO NO LINKEDIN (COPIE ESTA ESTRUTURA) ===
    {LINKEDIN_GOLDEN_EXAMPLE}
    ===================================================================
    """

def get_json_structure_instruction(qtd_str):
    return f"""
    Responda ESTRITAMENTE com este JSON:
    {{
        "contents": [
            {{
                "angulo": "Nome do Ângulo",
                "instagram": "Legenda Insta...",
                "linkedin": "Artigo ROBUSTO para LinkedIn (Mínimo 3 parágrafos)..."
            }}
            ... (x{qtd_str})
        ]
    }}
    """

# --- REGENERAÇÃO FORÇADA ---

def regenerate_single_platform(context_data, context_type, angle_name, target_platform, product_mode="auto"):
    client = get_client()
    if not client: return {"error": "Sem API Key"}

    instruction = ""
    if target_platform == "instagram":
        instruction = "CORREÇÃO INSTAGRAM: Seja mais polêmico e visual. Use emojis."
    else:
        instruction = f"""
        CORREÇÃO LINKEDIN (IMPORTANTE):
        - O texto anterior estava MUITO CURTO.
        - Quero um ARTIGO DE OPINIÃO, não uma legenda.
        - Escreva no MÍNIMO 150 palavras.
        - Estruture em: Título -> Contexto de Mercado -> Solução Visbody -> Conclusão Financeira.
        - Use o tom de um Consultor de Negócios experiente.
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
        
        prompt_text = f"""
        Analise esta imagem.
        Crie 3 estratégias de conteúdo.
        
        PARA O LINKEDIN:
        Quero 3 MINI-ARTIGOS (não posts curtos).
        Cada um deve ter Título, Problema, Solução Técnica e ROI.
        Use o EXEMPLO fornecido no prompt do sistema como base de qualidade.
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
        Analise este material.
        Extraia 5 Pontos de Ouro.
        
        PARA O LINKEDIN: Transforme cada ponto em um ARTIGO DE LIDERANÇA DE PENSAMENTO.
        Siga a estrutura: Título -> Contexto -> Solução Técnica -> ROI.
        Mínimo de 150 palavras por post.
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
