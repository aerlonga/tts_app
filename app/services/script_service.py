from __future__ import annotations

import json
import re

from newspaper import Article

from app.core.runtime import STICKFIGURE_STYLE_SUFFIX, get_system_prompt
from app.services.gemini_service import GeminiService, gemini_service


class ScriptService:
    def __init__(self, gemini: GeminiService | None = None) -> None:
        self.gemini = gemini or gemini_service

    def _parse_script_response(self, full_response: str) -> tuple[str, list[dict]]:
        script_part = full_response
        image_raw = full_response
        image_prompts: list[dict] = []

        if "===IMAGE_PROMPTS===" in full_response:
            parts = full_response.split("===IMAGE_PROMPTS===", 1)
            script_part = parts[0].strip()
            image_raw = parts[1].strip()

        start = image_raw.find("[")
        end = image_raw.rfind("]") + 1
        if start != -1 and end > start:
            json_str = image_raw[start:end]
            json_str = re.sub(r",\s*]", "]", json_str)
            try:
                image_prompts = json.loads(json_str)
                if "===IMAGE_PROMPTS===" not in full_response:
                    script_part = full_response[: full_response.rfind("[")].strip()
            except json.JSONDecodeError:
                image_prompts = []

        parsed_prompts = []
        for item in image_prompts:
            if isinstance(item, dict) and "prompt" in item:
                parsed_prompts.append(item)
            elif isinstance(item, str):
                parsed_prompts.append({"timestamp": "00:00", "cue": "", "prompt": item})

        return script_part, parsed_prompts

    def _enhance_instruction(self, language: str, *, generate_image_prompts: bool, style: str = "cinematic") -> str:
        base_instruction = get_system_prompt("enhance", language)
        if not generate_image_prompts:
            return base_instruction

        if style == "stickfigure":
            image_prompt_rules = f"""

VISUAL COMPOSITION RULES (critical - read before writing any image prompt):
- Characters are always the same plain stick figure design across the whole video (it is a fixed, pre-defined art style, not something you invent per scene). NEVER describe a character's appearance, clothing, accessories, color, or any physical/wardrobe detail (e.g. do not write things like "wearing an orange scarf", "a tall figure", "a bearded man"). Refer to characters only by their generic role or story function: "a prisoner", "the guard", "one of the prisoners", "the other prisoner", "a soldier". Keep the character reference as open/generic as possible.
- Every "prompt" must follow this formula: [characters' action, using expressive verbs of intent such as "looking in awe", "pointing urgently", "shielding his eyes", "turning away stubbornly"] + [narrative elements and the scene's light source, e.g. "warm firelight glow", "bright daylight spilling from the exit"] + the fixed style suffix.
- Keep narrative props and atmosphere (fire, shadows, projected silhouettes, mountains, tunnels, etc.) - they carry the story. Do not strip them out for the sake of simplicity.
- STRICTLY FORBIDDEN over-simplification terms in "prompt": "plain circle head(s)", "no face(s)", "no color", "no clothing details", "geometric lines/shapes only", or any instruction that empties the scene's props/atmosphere of detail. Only the character description itself stays generic.

IMAGE PROMPTS RULES (append AFTER the annotated script):
- Generate strictly between 5 and 7 image prompts, covering only the beginning, conflict, turning point, and resolution.
- This is for an image-to-video workflow (Google Flow): each scene needs a STATIC image prompt AND a separate MOTION prompt that will animate that exact image.
- Each prompt MUST be a JSON object with four fields:
  - "timestamp": the [MM:SS] timestamp from the script where this image should appear
  - "cue": a one-sentence summary of the narrative beat
  - "prompt": the full static image generation prompt in English, following the composition formula above and always ending with the style suffix below
  - "video_prompt": a short image-to-video motion prompt in English describing ONLY the camera/subject motion to apply to that static image. Do not re-describe the full scene, no style suffix, no dialogue, no sound/music/camera-brand terms.
- STRICTLY FORBIDDEN in "prompt" and "video_prompt": "dramatic", "photo-realistic", "cinematic lighting", "high contrast black and white", "grit", or any 3D/realistic style terms.
- Format as a JSON array at the very end, after the marker: ===IMAGE_PROMPTS===
"""
            if language == "pt":
                image_prompt_rules = f"""

REGRAS DE COMPOSICAO VISUAL (critico - ler antes de escrever qualquer prompt de imagem):
- Os personagens sao sempre o mesmo boneco palito simples ao longo de todo o video (e um estilo visual fixo e pre-definido, nao algo que voce inventa a cada cena). NUNCA descreva aparencia, roupa, acessorio, cor ou qualquer detalhe fisico/figurino do personagem (ex: nao escreva coisas como "usando um cachecol laranja", "uma figura alta", "um homem barbudo"). Refira-se aos personagens apenas pelo papel/funcao generica na historia: "um prisioneiro", "o guarda", "um dos prisioneiros", "o outro prisioneiro", "um soldado". Mantenha a referencia ao personagem o mais aberta/generica possivel.
- Todo "prompt" deve seguir esta formula: [acao dos personagens, usando verbos expressivos de intencao como "olhando maravilhado", "apontando urgentemente", "protegendo os olhos", "virando-se teimosamente"] + [elementos narrativos e a fonte de luz da cena, ex: "brilho quente da fogueira", "luz do dia forte entrando pela saida"] + o sufixo de estilo fixo.
- Mantenha adereços narrativos e atmosfera (fogo, sombras, silhuetas projetadas, montanhas, tuneis, etc.) - eles carregam a historia. Nao remova isso em nome da simplicidade.
- ESTRITAMENTE PROIBIDO usar termos de simplificacao excessiva no "prompt": "cabeca(s) em circulo liso", "sem rosto(s)", "sem cor", "sem detalhes de roupa", "apenas formas/linhas geometricas", ou qualquer instrucao que esvazie a cena/adereços/atmosfera de detalhes. Apenas a descricao do personagem em si fica generica.

REGRAS DOS PROMPTS DE IMAGEM (adicionar APOS o roteiro anotado):
- Gere estritamente entre 5 e 7 prompts de imagem, cobrindo apenas inicio, conflito, virada e desfecho.
- Isso e para um fluxo image-to-video (Google Flow): cada cena precisa de um prompt de imagem ESTATICA e de um prompt de MOVIMENTO separado, que vai animar exatamente essa imagem.
- Cada prompt DEVE ser um objeto JSON com quatro campos:
  - "timestamp": o timestamp [MM:SS] do roteiro onde esta imagem deve aparecer
  - "cue": um resumo em 1 frase do beat narrativo
  - "prompt": o prompt completo de imagem estatica em ingles, seguindo a formula de composicao acima e sempre terminando com o sufixo de estilo abaixo
  - "video_prompt": um prompt curto de movimento (image-to-video) em ingles, descrevendo APENAS o movimento de camera/personagem a aplicar naquela imagem estatica. Nao redescreva a cena inteira, sem sufixo de estilo, sem dialogo, sem termos de som/musica/marca de camera.
- ESTRITAMENTE PROIBIDO em "prompt" e "video_prompt": "dramatic", "photo-realistic", "cinematic lighting", "high contrast black and white", "grit", ou qualquer termo de estilo 3D/realista.
- Formate como um array JSON ao final, apos o marcador: ===IMAGE_PROMPTS===
"""
            return f"{base_instruction}{image_prompt_rules}"

        image_prompt_rules = """

IMAGE PROMPTS RULES (append AFTER the annotated script):
- Generate exactly 26 image prompts, one approximately every 34 seconds of narration.
- Each prompt MUST be a JSON object with three fields:
  - "timestamp": the [MM:SS] timestamp from the script where this image should appear
  - "cue": a short editorial label
  - "prompt": the full image generation prompt in English
- Style: dramatic black and white photorealistic photography, 16:9 aspect ratio, cinematic lighting.
- Each prompt should describe a specific scene from the script at that timestamp.
- Image prompt timestamps must not go beyond [15:00].
- Format as a JSON array at the very end, after the marker: ===IMAGE_PROMPTS===
"""
        if language == "pt":
            image_prompt_rules = """

REGRAS DOS PROMPTS DE IMAGEM (adicionar APOS o roteiro anotado):
- Gere exatamente 26 prompts de imagem, um aproximadamente a cada 34 segundos de narracao.
- Cada prompt DEVE ser um objeto JSON com tres campos:
  - "timestamp": o timestamp [MM:SS] do roteiro onde esta imagem deve aparecer
  - "cue": um rotulo editorial curto
  - "prompt": o prompt completo de geracao de imagem em ingles
- Estilo: fotografia fotorrealistica dramatica em preto e branco, proporcao 16:9, iluminacao cinematografica.
- Cada prompt deve descrever uma cena especifica do roteiro naquele timestamp.
- Os timestamps dos prompts de imagem nao devem ultrapassar [15:00].
- Formate como um array JSON ao final, apos o marcador: ===IMAGE_PROMPTS===
"""
        return f"{base_instruction}{image_prompt_rules}"

    def enhance_script(
        self,
        *,
        text: str,
        api_key: str | None = None,
        language: str = "pt",
        generate_image_prompts: bool = False,
        style: str = "cinematic",
    ) -> dict:
        result = self.gemini.generate_text(
            feature="enhance_script",
            contents=text,
            api_key=api_key,
            system_instruction=self._enhance_instruction(
                language, generate_image_prompts=generate_image_prompts, style=style
            ),
            temperature=0.4,
        )
        if generate_image_prompts:
            enhanced_text, image_prompts = self._parse_script_response(result["text"])
        else:
            enhanced_text = result["text"]
            image_prompts = []
        return {"enhanced_text": enhanced_text, "image_prompts": image_prompts, "usage": result["usage"]}

    def generate_script_from_url(
        self, *, url: str, api_key: str | None = None, language: str = "pt", style: str = "cinematic"
    ) -> dict:
        article = Article(url)
        article.download()
        article.parse()
        raw_text = article.text

        if len(raw_text) < 200:
            raise ValueError("Nao foi possivel extrair conteudo da URL. Tente outra URL.")

        result = self.gemini.generate_text(
            feature="video_script",
            contents=raw_text,
            api_key=api_key,
            system_instruction=get_system_prompt("scriptify", language, style),
            temperature=0.7,
        )
        script_part, parsed_prompts = self._parse_script_response(result["text"])

        return {
            "script": script_part,
            "image_prompts": parsed_prompts,
            "source_chars": len(raw_text),
            "usage": result["usage"],
        }


script_service = ScriptService()
