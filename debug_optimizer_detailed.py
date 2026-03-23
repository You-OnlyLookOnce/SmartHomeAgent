from src.core.persona_expression_optimizer import persona_optimizer
from src.core.persona_validator import persona_validator

# 详细测试优化过程
def debug_optimize_detailed():
    input_content = "帮我计算123乘以456"
    content = "123乘以456等于56088"
    
    print(f"原始输入: {input_content}")
    print(f"原始内容: {content}")
    print()
    
    # 测试场景识别
    scene = persona_optimizer.identify_scene(input_content)
    print(f"识别场景: {scene}")
    print()
    
    # 测试优化表达
    optimized_content = persona_optimizer.optimize_expression(content, input_content)
    print(f"优化后内容: {optimized_content}")
    print()
    
    # 测试验证
    validation_result = persona_validator.validate(optimized_content)
    print(f"验证结果: {'通过' if validation_result['passed'] else '未通过'}")
    print(f"验证得分: {validation_result['score']}")
    if not validation_result['passed']:
        print(f"问题: {validation_result['issues']}")
    print()
    
    # 测试验证和修正
    correction_result = persona_validator.validate_and_correct(content)
    print(f"验证和修正结果:")
    print(f"原始内容: {correction_result['original_content']}")
    print(f"修正后内容: {correction_result['corrected_content']}")
    print()
    
    # 手动测试各个步骤
    print("=== 手动测试各个步骤 ===")
    
    # 步骤 1: 基础优化
    step1 = content
    print(f"步骤 1 (基础优化): {step1}")
    
    # 步骤 2: 语言风格优化
    step2 = step1
    # 模拟语言风格优化
    cold_replacements = {
        "我不知道": "悦悦不太清楚呢",
        "不行": "可能不太方便呢",
        "不可以": "可能不太合适呢",
        "没有": "暂时没有呢",
        "是的": "是的呢",
        "好的": "好的呢",
        "对的": "对的呢"
    }
    for cold, warm in cold_replacements.items():
        step2 = step2.replace(cold, warm)
    print(f"步骤 2 (语言风格优化): {step2}")
    
    # 步骤 3: Emoji 优化
    step3 = step2
    # 指令场景不需要 Emoji
    print(f"步骤 3 (Emoji 优化): {step3}")
    
    # 步骤 4: 情感表达优化
    step4 = step3
    # 指令场景不需要情感表达
    print(f"步骤 4 (情感表达优化): {step4}")
    
    # 步骤 5: 交互模式优化
    step5 = step4
    # 指令场景不需要自称
    print(f"步骤 5 (交互模式优化): {step5}")
    
    # 步骤 6: 场景特定优化
    step6 = step5
    # 移除情感表达
    emotional_phrases = ["你觉得呢？", "这样可以吗？", "你最近怎么样呀？", "有什么需要帮忙的吗？"]
    for phrase in emotional_phrases:
        if phrase in step6:
            step6 = step6.replace(phrase, "")
    # 移除 Emoji
    import re
    step6 = re.sub(r"[\u2600-\u27BF\u1F300-\u1F64F\u1F680-\u1F6FF]", "", step6)
    # 添加贴心的表达
    caring_phrases = ["希望这对你有帮助", "如果有其他需要告诉我哦", "有什么其他问题随时问我"]
    if not any(phrase in step6 for phrase in caring_phrases):
        step6 += " " + caring_phrases[0]
    # 添加温暖的表达
    warm_phrases = ["很高兴能帮到你", "随时为你服务", "有任何问题都可以问我"]
    if not any(phrase in step6 for phrase in warm_phrases):
        step6 += " " + warm_phrases[0]
    print(f"步骤 6 (场景特定优化): {step6}")
    
    # 步骤 7: 验证和修正
    step7 = step6
    validation_result = persona_validator.validate(step7)
    if not validation_result["passed"]:
        correction_result = persona_validator.validate_and_correct(step7)
        step7 = correction_result["corrected_content"]
    print(f"步骤 7 (验证和修正): {step7}")

if __name__ == "__main__":
    debug_optimize_detailed()