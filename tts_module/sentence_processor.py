import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, AsyncGenerator, Generator, Callable, Union
from log import log
from tts_module.sentences import sentences_generator
import asyncio


class SentenceProcessor:
    def __init__(self, sequence_manager, max_workers: int = 4):
        self.sequence_manager = sequence_manager
        self.max_workers = max_workers
        self.executor = None
        self.skip = False
        self._running = False

    def start(self):
        """初始化处理器"""
        if not self._running:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
            self._running = True
            log.info("句子处理器已启动")

    def stop(self):
        """停止处理器并清理资源"""
        if self._running and self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None
            self._running = False
            log.info("句子处理器已停止")

    async def _to_async_generator(self, gen: Generator[str, None, None]) -> AsyncGenerator[str, None]:
        """将同步生成器转换为异步生成器"""
        for item in gen:
            yield item

    async def process_sentences(self, text_generator: Union[Generator[str, None, None], AsyncGenerator[str, None]], callback: Callable[[str, int], None] = None) -> None:
        """处理文本生成器中的句子，生成序号并传递给回调"""
        if not self._running:
            raise RuntimeError("句子处理器尚未启动")

        start_time = time.time()
        if not hasattr(text_generator, '__aiter__'):
            text_generator = self._to_async_generator(text_generator)

        try:
            gen = sentences_generator(
                text_generator,
                min_chars=5,
                max_chars=100,
                quick_first=False
            )
            async for sentence in gen:
                sentence_time = time.time() - start_time
                sequence = self.sequence_manager.get_next()
                log.info(f"第 {sequence} 句「{sentence}」获取延迟: {sentence_time:.3f} 秒")
                if self.skip:
                    await gen.aclose()
                    log.info("processor跳过剩余句子")
                    self.skip = False

                if callback:
                    self.executor.submit(self._sync_callback, callback, sentence, sequence)

        except Exception as e:
            log.error(f"处理过程出错: {str(e)}")

    def _sync_callback(self, callback, sentence: str, sequence: int):
        """修改后的回调包装，传入序号"""
        try:
            callback(sentence, sequence)
        except Exception as e:
            log.error(f"回调执行错误: {str(e)}")
