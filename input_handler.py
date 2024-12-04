import asyncio
from typing import Optional
from log import log

class UserInputHandler:
    def __init__(self):
        self.input_queue = asyncio.Queue()
        self._running = True

    async def get_user_input(self) -> bool:
        """异步获取用户输入"""
        try:
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, input, "请输入提示文本(输入q退出)："
            )
            if user_input.lower() == 'q':
                self._running = False
                return False
                
            await self.input_queue.put(user_input)
            return True
        except Exception as e:
            log.error("获取用户输入失败", exc_info=e)
            return False
    
    async def put_user_input(self, user_input: str):
        """将用户输入放入队列"""
        await self.input_queue.put(user_input)
        

    def is_running(self) -> bool:
        return self._running

    async def get_next_input(self) -> Optional[str]:
        """从队列获取下一个输入"""
        try:
            return await self.input_queue.get()
        except asyncio.CancelledError:
            return None
        finally:
            self.input_queue.task_done()

    def stop(self):
        """停止输入处理"""
        self._running = False
