# llm2voice

Transforming Streaming LLM Output into Steaming Audio Playback

将流式的llm输出转变为流式的音频输出并播放

---

需要mpv作为播放器，核心为tts_module，其余都是测试用文件。

本仓库为快速开发的实验性tts播放deemo


**运行日志**

> 2024-12-04 21:53:45.487 [INFO] 第 1 句「很高兴见到你。」获取延迟: 0.816 秒
> 2024-12-04 21:53:45.784 [INFO] 当前序号: 2，下一个序号: 3，当前队列序号1
> 2024-12-04 21:53:45.784 [INFO] 第 2 句「有什么我可以帮忙的吗？」获取延迟: 1.113 秒
> 2024-12-04 21:53:46.624 [INFO] 接收首个音频chunk
> 2024-12-04 21:53:46.624 [INFO] 播放首个音频chunk

### 开始

llm.py中填入openai格式的api_key，base_url，model_name

运行test1.py

### **架构**

![1733321294461](https://file+.vscode-resource.vscode-cdn.net/d%3A/github/llm2voice/image/README/introduce.png)

### 特性

* 流式文本处理
* 多线程音频处理
* 流式音频播放
* 即时中断机制
