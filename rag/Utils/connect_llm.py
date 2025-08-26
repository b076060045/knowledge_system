from json import load
from attr import dataclass
import requests, os
from knowledge_system.settings import OLLAMA_URL
from knowledge_system.errors import KMsystemError, KMsystemException
from openai import OpenAI

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

@dataclass
class LlmConfig:
    provider: str
    model: str

def call_llm(prompt: str, cfg: LlmConfig):
    if cfg.provider == "ollama":
        _call_ollama(prompt, cfg.model)
    elif cfg.provider == 'openai':
        _call_openai(prompt, cfg.model)

def _call_ollama(prompt, model):
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": model,
            "prompt": prompt
        }, stream=False)

        return resp.json()['response']
    except Exception as e: 
        raise KMsystemException(KMsystemError.OPENAI_SERVER_ERROR, e)

def _call_openai(prompt, model):
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        resp = client.chat.completions.create(
            model=model,  # 模型名稱
            messages=[
                {"role": "system", "content": "你是個很毒舌的AI助理"},
                {"role": "user", "content": prompt}
            ]
        )
        return resp.choices[0].message.content
    except Exception as e:
        raise KMsystemException(KMsystemError.OPENAI_SERVER_ERROR, e)
