import subprocess
import threading
import queue
import shutil
import time
from log import log

class MPVPlayer:
    """使用MPV播放音频流的播放器类"""

    def __init__(self, audio_device=None):
        self.mpv_process = None
        self.chunk_queue = queue.Queue()
        self.is_playing = False
        self.is_processing = False  # 标记是否正在处理音频
        self.play_thread = None
        self._lock = threading.Lock()
        self.first_chunk = True
        self.audio_device = audio_device

    def start(self):
        """启动MPV播放器进程"""
        if self.is_playing:
            return
        try:
            mpv_command = ["mpv", "--no-cache", "--no-terminal"]
            
            # 添加音频输出配置
            if self.audio_device:
                # Windows平台使用wasapi作为音频输出
                mpv_command.extend(["--ao=wasapi"])
                # 将设备名称作为设备ID
                device_id = self.audio_device['name']
                mpv_command.extend([f"--audio-device=wasapi/{device_id}"])
                log.info(f"使用音频设备: {device_id}")
                    
            mpv_command.extend(["--", "fd://0"])
            
            self.mpv_process = subprocess.Popen(
                mpv_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.is_playing = True
            self.play_thread = threading.Thread(target=self._process_chunks)
            self.play_thread.start()
            log.info("MPV播放器已启动")
        except Exception as e:
            log.error(f"启动MPV播放器失败: {e}")
            self.stop()
            raise

    def _process_chunks(self):
        """处理并播放音频数据块"""
        self.is_processing = True
        try:
            while self.is_playing or not self.chunk_queue.empty():
                try:
                    # 使用超时等待，避免卡死
                    chunk = self.chunk_queue.get(timeout=0.5)
                    if chunk is None:  # 结束信号
                        if self.chunk_queue.empty():  # 确保队列清空
                            break
                        continue
                    if self.mpv_process and self.mpv_process.stdin:
                        if self.first_chunk:
                            log.info(f"播放首个音频chunk")
                            self.first_chunk = False
                        self.mpv_process.stdin.write(chunk)
                        self.mpv_process.stdin.flush()
                except queue.Empty:
                    continue
                except Exception as e:
                    log.error(f"处理音频数据时出错: {e}")
                    break
        finally:
            self.is_processing = False
            # 清理MPV进程
            if self.mpv_process:
                if self.mpv_process.stdin:
                    self.mpv_process.stdin.close()
                self.mpv_process.terminate()
                self.mpv_process.wait()
                self.mpv_process = None

    def add_chunk(self, chunk: bytes):
        """添加音频数据块到队列"""
        if self.is_playing:
            self.chunk_queue.put(chunk)

    def stop(self):
        """停止播放"""
        with self._lock:
            if not self.is_playing and not self.is_processing:
                return
            self.is_playing = False
            self.chunk_queue.put(None)  # 发送结束信号
            # 等待所有数据处理完成
            while self.is_processing and not self.chunk_queue.empty():
                time.sleep(0.1)
            # 只有在不是当前线程时才join
            if (self.play_thread and 
                self.play_thread.is_alive() and 
                self.play_thread != threading.current_thread()):
                self.play_thread.join()
            self._cleanup_queue()
            self.play_thread = None
            log.info("MPV播放器已停止")

    def _cleanup_queue(self):
        """只清理队列"""
        while not self.chunk_queue.empty():
            try:
                self.chunk_queue.get_nowait()
            except queue.Empty:
                break

    def is_queue_empty(self) -> bool:
        """检查音频队列是否为空"""
        return self.chunk_queue.empty()

    def __del__(self):
        self.stop()
