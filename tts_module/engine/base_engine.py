from pydantic import BaseModel
from typing import Optional, AsyncIterator, Tuple
import edge_tts
from log import log
import time
import asyncio
from abc import ABC, abstractmethod



class TTSEngine(ABC):
    """TTS引擎的抽象基类"""
    @abstractmethod
    async def synthesize(self, text: str) -> AsyncIterator[bytes]:
        """
        将文本转换为语音
        Args:
            text: 要转换的文本
        Returns:
            AsyncIterator[bytes]: 音频数据的异步迭代器
        """
        pass


