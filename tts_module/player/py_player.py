import io
import queue
import threading
import sounddevice as sd
import soundfile as sf
from log import log
from typing import Iterator

class FFPlayer:
    def __init__(self, audio_device=None):
        self.chunk_queue = queue.Queue()
        self.is_active = False
        self.audio_device = audio_device
        self.play_thread = None
        self.first_chunk = True

    def start(self):
        if self.is_active:
            return

        # if self.audio_device:
        #     sd.default.device = self.audio_device['name']

        self.is_active = True
        self.play_thread = threading.Thread(target=self._process_chunks)
        self.play_thread.start()
        log.info("Python音频播放器已启动")

    def _process_chunks(self):
        try:
            while self.is_active or not self.chunk_queue.empty():
                chunks = []
                # 收集直到遇到None标记
                while True:
                    try:
                        chunk = self.chunk_queue.get(timeout=0.5)
                        if chunk is None:  # 收到结束标记
                            if chunks:  # 如果有收集到的数据就播放
                                audio_data = b"".join(chunks)
                                if self.first_chunk:
                                    log.info(f"播放首个音频chunk")
                                    self.first_chunk = False
                                try:
                                    data, samplerate = sf.read(io.BytesIO(audio_data))
                                    sd.play(data, samplerate)
                                    sd.wait()
                                except Exception as e:
                                    log.error(f"音频播放错误: {e}")
                            break  # 跳出内层循环，继续等待新的音频序列
                        chunks.append(chunk)
                    except queue.Empty:
                        continue
                    
        finally:
            sd.stop()  # 保持简单,只停止当前播放

    def add_chunk(self, chunk: bytes):
        if self.is_active:
            self.chunk_queue.put(chunk)

    def stop(self):
        if not self.is_active:
            return
        self.is_active = False
        self.chunk_queue.put(None)
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join()
        sd.stop()
        log.info("音频设备资源已清理")
        log.info("Python音频播放器已停止")
