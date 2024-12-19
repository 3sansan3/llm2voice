import subprocess
import threading
import queue
from log import log

class MPVPlayer:
    def __init__(self, audio_device=None):
        self.mpv_process = None
        self.chunk_queue = queue.Queue()
        self.is_active = False
        self.audio_device = audio_device
        self.play_thread = None
        self.first_chunk = True

    def start(self):
        if self.is_active:
            return

        mpv_command = ["mpv", "--no-cache", "--no-terminal"]
        if self.audio_device:
            mpv_command.extend([
                "--ao=wasapi",
                f"--audio-device=wasapi/{self.audio_device['name']}"
            ])
        mpv_command.extend(["--", "fd://0"])

        self.mpv_process = subprocess.Popen(
            mpv_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.is_active = True
        self.play_thread = threading.Thread(target=self._process_chunks)
        self.play_thread.start()
        log.info("MPV播放器已启动")

    def _process_chunks(self):
        try:
            while self.is_active or not self.chunk_queue.empty():
                try:
                    chunk = self.chunk_queue.get(timeout=0.5)
                    if chunk is None:  # 收到结束标记
                        continue  # 改为continue,继续处理下一个音频序列
                    if self.mpv_process and self.mpv_process.stdin:
                        if self.first_chunk:
                            log.info(f"播放首个音频chunk")
                            self.first_chunk = False
                        self.mpv_process.stdin.write(chunk)
                        self.mpv_process.stdin.flush()
                except queue.Empty:
                    continue
        finally:
            if self.mpv_process and self.mpv_process.stdin:
                self.mpv_process.stdin.close()

    def add_chunk(self, chunk: bytes):
        if self.is_active:
            self.chunk_queue.put(chunk)

    def stop(self):
        if not self.is_active:
            return
        self.is_active = False
        self.chunk_queue.put(None)  # 发送结束信号
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join()
        if self.mpv_process:
            if self.mpv_process.stdin:
                self.mpv_process.stdin.close()
            self.mpv_process.terminate()
            self.mpv_process.wait()
            self.mpv_process = None
        self.first_chunk = True
        log.info("MPV播放器已停止")