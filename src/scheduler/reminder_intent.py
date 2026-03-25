from .time_parser import TimeParser

class ReminderIntent:
    def __init__(self):
        self.time_parser = TimeParser()
    
    def detect(self, text: str) -> dict:
        """检测提醒意图，返回解析结果"""
        if not self.time_parser.is_reminder_intent(text):
            return {
                "has_intent": False,
                "data": None
            }
        
        # 提取标题和内容
        title = "提醒"
        content = text
        
        # 解析时间
        reminder_time, repeat_type = self.time_parser.parse(text)
        
        return {
            "has_intent": True,
            "data": {
                "title": title,
                "content": content,
                "reminder_time": reminder_time,
                "repeat_type": repeat_type
            }
        }