from pydantic import BaseModel
from typing import Optional, AsyncIterator
import edge_tts
from log import log
import time
from .base_engine import TTSEngine

class EdgeConfig(BaseModel):
    voice: str = "zh-CN-XiaoxiaoNeural"
    rate: str = "+13%"
    volume: str = "+12%"
    pitch: str = "+37Hz"

class EdgeEngine(TTSEngine):
    def __init__(self, config: Optional[EdgeConfig] = None):
        self.config = config or EdgeConfig()

    async def synthesize(self, text: str) -> AsyncIterator[bytes]:
        """返回异步迭代器"""
        synthesis_start = time.time()
        first_chunk = True
        try:
            comm = edge_tts.Communicate(
                text, self.config.voice,
                rate=self.config.rate,
                volume=self.config.volume,
                pitch=self.config.pitch
            )
            
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    if first_chunk:
                        log.info(f"接收首个音频chunk")
                        first_chunk = False
                    yield chunk["data"]
                    
            log.info(f"TTS合成完成 耗时:{time.time()-synthesis_start:.3f}s")
        except Exception as e:
            log.error(f"TTS合成失败: {str(e)}")
            return
