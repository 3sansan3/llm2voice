import asyncio
import threading
from typing import AsyncGenerator, Optional, Dict
from tts_module.engine import EdgeEngine
from tts_module.mpv_player import MPVPlayer
from tts_module.sentence_processor import SentenceProcessor
from log import log
import queue

class TTS:
    def __init__(self, max_workers: int = 5, audio_device = None):
        self.sequence_manager = SequenceManager()
        self.engine = EdgeEngine()
        self.mpv_player = MPVPlayer(audio_device=audio_device)
        self.max_workers = max_workers
        self.sentence_processor = SentenceProcessor(self.sequence_manager, self.max_workers)
        self._tasks: Dict[int, asyncio.Task] = {}
        self._loops: Dict[int, asyncio.AbstractEventLoop] = {}
        self._tasks_lock = threading.Lock()

    async def start(self):
        """启动TTS服务"""
        self.mpv_player.start()
        self.sentence_processor.start()  # 移除await

    async def stop(self):
        """停止TTS服务"""
        self.sentence_processor.stop()
        self.mpv_player.stop()

    def skip_remaining(self):
        """跳过剩余句子"""
        self.sentence_processor.skip = True
        self.sequence_manager.skip()
        
        # 取消所有正在进行的任务
        with self._tasks_lock:
            for sequence, loop in self._loops.items():
                if sequence in self._tasks and not self._tasks[sequence].done():
                    loop.call_soon_threadsafe(self._tasks[sequence].cancel)

    async def process_stream(self, text_generator: AsyncGenerator[str, None]):
        """处理文本流"""
        await self.sentence_processor.process_sentences(text_generator, self._process_sentence)

    def _process_sentence(self, sentence: str, sequence: int):
        """处理单个句子的音频生成和播放"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                with self._tasks_lock:
                    self._loops[sequence] = loop
                
                coro = self._process_audio2(sentence, sequence)
                task = loop.create_task(coro)
                
                with self._tasks_lock:
                    self._tasks[sequence] = task
                
                loop.run_until_complete(task)
            except asyncio.CancelledError:
                log.info(f"句子处理被取消 - 序号{sequence}")
            finally:
                with self._tasks_lock:
                    self._tasks.pop(sequence, None)
                    self._loops.pop(sequence, None)
                loop.close()
        except Exception as e:
            log.error(f"处理失败: {str(e)}")

    async def _process_audio2(self, sentence: str, sequence: int):
        """异步音频处理函数 - 确保按序播放"""
        try:
            # 使用异步队列作为缓冲区
            chunk_queue = asyncio.Queue()
            
            async def producer():
                """异步生成音频数据"""
                try:
                    async for chunk in self.engine.synthesize(sentence):
                        if chunk:
                            await chunk_queue.put(chunk)
                    # 放入结束标记
                    await chunk_queue.put(None)
                except asyncio.CancelledError:
                    log.info(f"音频生成被取消 - 序号{sequence}")
                    raise

            async def consumer():
                """异步消费音频数据"""
                try:
                    while True:
                        chunk = await chunk_queue.get()
                        if chunk is None:  # 结束标记
                            break
                        if self.sequence_manager.quene.empty():
                            log.info(f"当前正在播放的序号{sequence}，被终止！！！！！当前队列无序号")
                            return
                        if self.sequence_manager.quene.queue[0] == sequence:
                            self.mpv_player.add_chunk(chunk)
                except asyncio.CancelledError:
                    log.info(f"音频播放被取消 - 序号{sequence}")
                    raise

            while not self.sequence_manager.quene.empty():
                current_seq = self.sequence_manager.quene.queue[0]
                if current_seq > sequence:
                    log.info(f"音频序号{sequence}已过期,当前队列序号{current_seq}")

                    return
                if current_seq == sequence:
                    # 创建生产者和消费者任务
                    producer_task = asyncio.create_task(producer())
                    consumer_task = asyncio.create_task(consumer())
                    # 等待任务完成
                    await asyncio.gather(producer_task, consumer_task)
                    if self.sequence_manager.quene.empty():
                        return
                    self.sequence_manager.quene.get()
                    if not self.sequence_manager.quene.empty():
                        log.info(f"句子「{sentence}」(序号{sequence})播放完成，当前队列序号{self.sequence_manager.quene.queue[0]}")
                    else:
                        log.info(f"句子「{sentence}」(序号{sequence})播放完成，当前队列无序号")
                    return
                await asyncio.sleep(0.1)
            log.info(f"音频序号{sequence}已过期,当前队列无序号")

        except asyncio.CancelledError:
            log.info(f"音频处理被取消 - 序号{sequence}")
            raise
        except Exception as e:
            log.error(f"音频处理失败 - 序号{sequence}: {str(e)}")
            raise

class SequenceManager:
    def __init__(self):
        self._sequence = 1
        self.quene = queue.Queue()
        self._lock = threading.Lock()
    
    def get_next(self):
        with self._lock:
            seq = self._sequence
            self.quene.put(seq)
            self._sequence += 1
            log.info(f"当前序号: {seq}，下一个序号: {self._sequence}，当前队列序号{self.quene.queue[0]}")
            return seq
          
    def skip(self):
        with self._lock:
            self.quene.queue.clear()
            log.info("队列清空")