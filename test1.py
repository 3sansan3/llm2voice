import asyncio
from llm import OpenAILLM
from log import log
from input_handler import UserInputHandler
from tts_module.tts import TTS
import sounddevice as sd

def select_audio_device():
    """选择音频输出设备"""
    target_name = "Voicemeeter Input (VB-Audio Voicemeeter VAIO)"
    devices = sd.query_devices()
    
    for device in devices:
        if device['max_output_channels'] > 0 and device['name'] == target_name:
            log.info(f"使用音频设备: {device['name']}")
            return device
            
    log.error(f"未找到目标音频设备: {target_name}")
    return None

async def main():
    """简化后的主函数"""
    device = select_audio_device()
    if not device:
        return
        
    llm = OpenAILLM()
    input_handler = UserInputHandler()
    tts = TTS(audio_device=device)
    
    await tts.start()
    
    async def process_input_task():
        while input_handler.is_running():
            user_input = await input_handler.get_next_input()
            if user_input:
                dialogue = [{"role": "user", "content": user_input}]
                response_generator = llm.fake_response(dialogue)
                await tts.process_stream(response_generator)
            await asyncio.sleep(0.1)

    try:
        asyncio.create_task(process_input_task())
        
        log.info("中断测试")
        await input_handler.get_user_input()
        # await asyncio.sleep(3)
        # tts.skip_remaining()
        log.info("开始接收用户输入...")
        while input_handler.is_running():
            await input_handler.get_user_input()
        

    except KeyboardInterrupt:
        log.info("程序被用户中断")
    except Exception as e:
        log.error("程序执行错误", exc_info=e)
    finally:
        log.info("开始清理资源...")
        input_handler.stop()
        await tts.stop()
        log.info("资源清理完成")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("程序被强制终止")