"""
Módulo de Processamento - Versão 10.0 (Prompts Ultra-Premium B2B)
Foco: LinkedIn de Autoridade Técnica & Instagram de Desejo Visual
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

# --- O CORAÇÃO DA MUDANÇA: PROMPTS DE ELITE ---

def get_common_system_prompt():
    return """
    ATUE COMO: Diretor de Marketing Global da VISBODY e Consultor de Negócios Fitness/Médico.
    
    SUA AUDIÊNCIA B2B (LinkedIn): Donos de grandes redes de academia, fisioterapeutas de elite e médicos nutrólogos. Eles odeiam "papinho de vendedor". Eles buscam dados, tecnologia e retorno financeiro.
    SUA AUDIÊNCIA B2C/B2B (Instagram): Personal trainers e o público final que valoriza tecnologia de ponta e estética futurista.
    
    === REGRAS DE GÊNERO (INEGOCIÁVEL) ===
    - ESTEIRA (Treadmill, Creator) -> FEMININO ("A Creator 600", "A esteira inteligente").
    - SCANNER (Body Scanner, Visbody R6/S30) -> MASCULINO ("O Visbody", "O scanner 3D").
    
    === ESTILO DE ESCRITA ===
    
    1. LINKEDIN (AUTORIDADE & ROI):
       - PROIBIDO: Textos curtos, genéricos ou com "cara de anúncio".
       - OBRIGATÓRIO: Estrutura de artigo técnico/consultivo.
       - Use "Bullet Points" para dados técnicos.
       - Fale de "Retenção de alunos", "Aumento de ticket médio", "Precisão clínica" e "Biomecânica".
       - Tom: Sofisticado, Especialista, Provocativo.
       
    2. INSTAGRAM (DESEJO & VISUAL):
       - OBRIGATÓRIO: Hook visual (ex: "Parece ficção científica, mas é sua nova avaliação").
       - Use emojis estratégicos (💎, 🧬, 🚀) mas mantenha a classe.
       - Hashtags: #Visbody #TecnologiaFitness #Bioimpedancia #AvaliacaoFisica + Nome do Produto.
    """

def get_json_structure_instruction(qtd_str):
    return f"""
    Responda ESTRITAMENTE com este JSON (sem markdown em volta):
    {{
        "contents": [
            {{
                "angulo": "Nome do Ângulo (Ex: Foco em Retenção, Foco em Tecnologia 3D)",
                "instagram": "Texto...",
                "linkedin": "Texto..."
            }}
            ... (x{qtd_str})
        ]
    }}
    """

# --- REGENERAÇÃO COM INSTRUÇÕES DE CORREÇÃO ---

def regenerate_single_platform(context_data, context_type, angle_name, target_platform):
    client = get_client()
    if not client: return {"error": "Sem API Key"}

    instruction = ""
    if target_platform == "instagram":
        instruction = """
        CORREÇÃO PARA INSTAGRAM:
        - O texto anterior estava morno. Quero algo MAGNÉTICO.
        - Use o modelo AIDA (Atenção, Interesse, Desejo, Ação).
        - Enfatize a exclusividade e o design futurista da Visbody.
        - Faça o leitor sentir que está ficando para trás se não tiver isso.
        """
    else:
        instruction = """
        CORREÇÃO PARA LINKEDIN (NÍVEL EXPERT):
        - O texto anterior estava muito simples/comercial.
        - Escreva como um CEO falando com outro CEO.
        - Traga dados, fale sobre dor de mercado (ex: rotatividade de alunos, imprecisão de avaliações antigas).
        - Aumente o tamanho do texto. Desenvolva o raciocínio.
        - Termine com uma pergunta reflexiva de negócios.
        """

    prompt_full = f"""
    REESCREVER: {target_platform.upper()}
    Contexto do Ângulo: "{angle_name}"
    
    {instruction}
    
    Retorne APENAS JSON: {{ "new_text": "..." }}
    """

    try:
        messages = [{"role": "system", "content": get_common_system_prompt()}]
        
        # Monta contexto (Texto ou Imagem)
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
        
        res = clean_json_response(response.choices[0].message.content)
        return json.loads(res)

    except Exception as e:
        return {"error": str(e)}

# --- PROCESSAMENTO PRINCIPAL ---

def process_image_direct(image_bytes):
    client = get_client()
    if not client: return {"error": "API Key não configurada"}

    try:
        base64_image = encode_image_from_bytes(image_bytes)
        
        prompt_text = """
        Analise esta imagem da VISBODY com "olhar de raio-x".
        Identifique: Design, Tecnologia visível, Interface, Ergonomia.
        
        Crie 3 estratégias de conteúdo PREMIUM:
        1. Foco em Autoridade Técnica (Para convencer o dono da clínica/academia).
        2. Foco em Experiência do Cliente (O "Efeito Uau" para o aluno).
        3. Foco em Diferenciação de Mercado (Por que isso vence a concorrência).
        
        """ + get_json_structure_instruction("3")
        
        user_message = [
            {"type": "text", "text": prompt_text},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "high"}}
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": get_common_system_prompt()}, {"role": "user", "content": user_message}],
            response_format={"type": "json_object"},
            max_tokens=4000
        )
        
        content = clean_json_response(response.choices[0].message.content)
        result = json.loads(content)
        result["raw_context"] = base64_image
        result["context_type"] = "image"
        return result
        
    except Exception as e:
        return {"error": f"Erro imagem: {str(e)}"}

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
        Analise este documento técnico. Não quero resumo, quero ESTRATÉGIA.
        Extraia 5 "Golden Nuggets" (Pontos de Ouro) deste material.
        
        Para o LinkedIn: Transforme cada ponto em uma lição de negócios/tecnologia robusta. Use dados, cite especificações como vantagens competitivas.
        Para o Instagram: Transforme cada ponto em desejo visual e status.
        
        """ + get_json_structure_instruction("5")

        result = {}
        content_raw = ""

        if not is_scanned:
            full_text = "\n".join(text_content)
            prompt = f"Material Visbody:\n---\n{full_text[:50000]}\n---\n{prompt_instruction}"
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": get_common_system_prompt()}, {"role": "user", "content": prompt}],
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
                messages=[{"role": "system", "content": get_common_system_prompt()}, {"role": "user", "content": user_message}],
                response_format={"type": "json_object"},
                max_tokens=4000
            )
            content_raw = response.choices[0].message.content
            result = json.loads(clean_json_response(content_raw))
            result["raw_context"] = None
            result["context_type"] = "scanned_pdf"

        return result

    except Exception as e:
        return {"error": f"Erro processamento: {str(e)}"}
