from typing import Dict, Generator, Optional, Any, Tuple
import openai
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall
from log import log
from pathlib import Path
import time

class OpenAILLM:
    """OpenAI LLM客户端封装类"""
    def __init__(self):
        """
        初始化OpenAI LLM客户端
        """

        self.model_name = "deepseek-chat"
        self.api_key = "sk-123"
        self.base_url = "https://api.deepseek.com"
        self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)

    def response(self, dialogue: list) -> Generator[str, None, None]:
        """
        生成对话响应
        """
        try:
            responses = self.client.chat.completions.create(
                model=self.model_name,
                messages=dialogue,
                stream=True
            )
            for chunk in responses:
                if content := chunk.choices[0].delta.content:
                    yield content
        except Exception as e:
            log.error(f"Response generation error: {str(e)}")
            yield f"Error: {str(e)}"

    def response_call(
        self, dialogue: list, functions_call: list
    ) -> Generator[Tuple[Optional[str], Optional[ChoiceDeltaToolCall]], None, None]:
        """
        生成带函数调用的对话响应
        """
        try:
            responses = self.client.chat.completions.create(
                model=self.model_name,
                messages=dialogue,
                stream=True,
                tools=functions_call
            )
            for chunk in responses:
                content = chunk.choices[0].delta.content
                tool_calls = chunk.choices[0].delta.tool_calls
                yield content, tool_calls
        except Exception as e:
            log.error(f"Function call response error: {str(e)}")
            yield f"Error: {str(e)}", None
    def fake_response(self, dialogue: list) -> Generator[str, None, None]:
        """
        模拟对话响应生成器
        """
        text = "星光洒满夜空，思绪随风飘散，我心支离破碎。"
        
        time.sleep(0.5)
        for char in text:
            yield char
            # time.sleep(0.01)  # 只保留字符间延时，使输出更流畅