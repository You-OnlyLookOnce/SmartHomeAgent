# 简单测试优化器
def debug_simple():
    # 模拟优化过程
    content = "123乘以456等于56088"
    
    print(f"原始内容: {content}")
    print()
    
    # 测试 1: 基础替换
    test1 = content
    print(f"测试 1 (基础内容): {test1}")
    
    # 测试 2: 情感表达移除
    test2 = test1
    emotional_phrases = ["你觉得呢？", "这样可以吗？", "你最近怎么样呀？", "有什么需要帮忙的吗？"]
    for phrase in emotional_phrases:
        if phrase in test2:
            test2 = test2.replace(phrase, "")
    print(f"测试 2 (移除情感表达): {test2}")
    
    # 测试 3: Emoji 移除
    test3 = test2
    import re
    test3 = re.sub(r"[\u2600-\u27BF\u1F300-\u1F64F\u1F680-\u1F6FF]", "", test3)
    print(f"测试 3 (移除 Emoji): {test3}")
    
    # 测试 4: 添加贴心表达
    test4 = test3
    caring_phrases = ["希望这对你有帮助", "如果有其他需要告诉我哦", "有什么其他问题随时问我"]
    if not any(phrase in test4 for phrase in caring_phrases):
        test4 += " " + caring_phrases[0]
    print(f"测试 4 (添加贴心表达): {test4}")
    
    # 测试 5: 添加温暖表达
    test5 = test4
    warm_phrases = ["很高兴能帮到你", "随时为你服务", "有任何问题都可以问我"]
    if not any(phrase in test5 for phrase in warm_phrases):
        test5 += " " + warm_phrases[0]
    print(f"测试 5 (添加温暖表达): {test5}")
    
    # 测试 6: 空格处理
    test6 = test5
    test6 = " ".join(test6.split())
    print(f"测试 6 (空格处理): {test6}")

if __name__ == "__main__":
    debug_simple()