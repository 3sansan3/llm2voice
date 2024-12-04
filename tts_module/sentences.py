async def sentences_generator(text_generator, min_chars=5, max_chars=10, quick_first=False):
    """优化的句子分割生成器"""
    punctuations = set(",.?，。？！!;；:：")  # 分句的标点符号
    hard_break = set(".。!！?？")  # 强制分句的标点符号
    buffer = []
    is_first = True

    async def yield_sentence(text):
        nonlocal is_first
        if not text:
            return None
        if is_first and quick_first:
            is_first = False
            return text
        return text if len(text) >= min_chars else None

    async for text_chunk in text_generator:
        for char in text_chunk:
            buffer.append(char)
            
            # 当遇到标点符号时尝试分句
            if char in punctuations:
                current_text = ''.join(buffer).strip()
                
                # 如果长度超过最大限制且不是硬分割标点，继续累积
                if len(current_text) > max_chars and char not in hard_break:
                    continue
                    
                # 遇到分句标点或达到长度限制，输出句子
                if current_text and (result := await yield_sentence(current_text)):
                    yield result
                buffer.clear()

    # 处理剩余文本
    final_text = ''.join(buffer).strip()
    if final_text and (result := await yield_sentence(final_text)):
        yield result

