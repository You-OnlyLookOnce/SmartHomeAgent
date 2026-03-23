import re

# 测试 Emoji 移除正则表达式
def test_emoji_regex():
    test_string = "123乘以456等于56088"
    print(f"原始字符串: {test_string}")
    
    # 测试不同的正则表达式
    print()
    print("=== 测试不同的正则表达式 ===")
    
    # 测试 1: 当前使用的正则表达式
    regex1 = r"[\u2600-\u27BF\u1F300-\u1F64F\u1F680-\u1F6FF]"
    result1 = re.sub(regex1, "", test_string)
    print(f"测试 1 (当前正则): {result1}")
    
    # 测试 2: 只测试 \u2600-\u27BF 范围
    regex2 = r"[\u2600-\u27BF]"
    result2 = re.sub(regex2, "", test_string)
    print(f"测试 2 (\u2600-\u27BF): {result2}")
    
    # 测试 3: 只测试 \u1F300-\u1F64F 范围
    regex3 = r"[\u1F300-\u1F64F]"
    result3 = re.sub(regex3, "", test_string)
    print(f"测试 3 (\u1F300-\u1F64F): {result3}")
    
    # 测试 4: 只测试 \u1F680-\u1F6FF 范围
    regex4 = r"[\u1F680-\u1F6FF]"
    result4 = re.sub(regex4, "", test_string)
    print(f"测试 4 (\u1F680-\u1F6FF): {result4}")
    
    # 测试 5: 使用更精确的 Emoji 正则表达式
    regex5 = r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]"
    result5 = re.sub(regex5, "", test_string)
    print(f"测试 5 (更精确的 Emoji 正则): {result5}")

if __name__ == "__main__":
    test_emoji_regex()