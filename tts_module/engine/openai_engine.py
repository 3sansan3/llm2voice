from openai import OpenAI
from pydantic import BaseModel
from typing import Optional, AsyncIterator
import asyncio
from log import log
import time
import io
from .base_engine import TTSEngine

class OpenAIConfig(BaseModel):
    base_url: str = "http://xxxxxxx:3000/v1"
    api_key: str = "sk-123123"
    voice: str = "hoshino"
    model: str = "tts-1"
    audio_format: str = "wav"  # 新增音频格式配置

class OpenAIEngine(TTSEngine):
    def __init__(self, config: Optional[OpenAIConfig] = None):
        self.config = config or OpenAIConfig()
        self.client = OpenAI(
            base_url=self.config.base_url,
            api_key=self.config.api_key
        )
        self.chunk_size = 720

    async def synthesize(self, text: str) -> AsyncIterator[bytes]:
        synthesis_start = time.time()
        first_chunk = True
        
        try:
            response = self.client.audio.speech.create(
                input=text,
                voice=self.config.voice,
                response_format=self.config.audio_format,
                model=self.config.model,
            )

            buffer = io.BytesIO(response.content)
            while chunk := buffer.read(self.chunk_size):
                if first_chunk:
                    log.info(f"接收首个音频chunk: {len(chunk)} 字节")
                    first_chunk = False
                yield chunk

            
            log.info(f"TTS合成完成 耗时:{time.time()-synthesis_start:.3f}s")

        except Exception as e:
            log.error(f"OpenAI TTS合成失败: {str(e)}")
            return
