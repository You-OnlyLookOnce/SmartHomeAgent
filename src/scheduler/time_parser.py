from datetime import datetime, timedelta
import re

class TimeParser:
    def __init__(self):
        self.weekdays = {
            '周一': 0, '周二': 1, '周三': 2, '周四': 3, '周五': 4, '周六': 5, '周日': 6,
            '星期一': 0, '星期二': 1, '星期三': 2, '星期四': 3, '星期五': 4, '星期六': 5, '星期日': 6
        }
        self.months = {
            '1月': 1, '2月': 2, '3月': 3, '4月': 4, '5月': 5, '6月': 6,
            '7月': 7, '8月': 8, '9月': 9, '10月': 10, '11月': 11, '12月': 12
        }
    
    def parse(self, text: str) -> (str, str):
        """解析时间表达式，返回(提醒时间, 重复类型)"""
        text = text.strip()
        
        # 检查重复类型
        repeat_type = "once"
        if '每天' in text or '天天' in text:
            repeat_type = "daily"
        elif '每周' in text:
            repeat_type = "weekly"
        elif '每月' in text:
            repeat_type = "monthly"
        
        # 解析具体时间
        now = datetime.now()
        target_date = now
        
        # 处理今天、明天、后天
        if '今天' in text:
            target_date = now
        elif '明天' in text:
            target_date = now + timedelta(days=1)
        elif '后天' in text:
            target_date = now + timedelta(days=2)
        
        # 处理本周几
        for weekday, day_num in self.weekdays.items():
            if weekday in text:
                days_ahead = (day_num - now.weekday()) % 7
                target_date = now + timedelta(days=days_ahead)
                break
        
        # 处理具体日期
        date_match = re.search(r'(\d+)月(\d+)日', text)
        if date_match:
            month = int(date_match.group(1))
            day = int(date_match.group(2))
            year = now.year
            if month < now.month:
                year += 1
            target_date = target_date.replace(year=year, month=month, day=day)
        
        # 处理时间
        time_match = re.search(r'(\d+):(\d+)', text)
        if not time_match:
            time_match = re.search(r'(\d+)点', text)
            if time_match:
                hour = int(time_match.group(1))
                minute = 0
            else:
                hour = 8
                minute = 0
        else:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
        
        # 处理上午、下午
        if '下午' in text and hour < 12:
            hour += 12
        elif '上午' in text and hour >= 12:
            hour -= 12
        
        target_datetime = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # 如果解析出的时间早于当前时间，且不是重复类型，则调整到下一天
        if target_datetime < now and repeat_type == "once":
            target_datetime += timedelta(days=1)
        
        return target_datetime.isoformat(), repeat_type
    
    def is_reminder_intent(self, text: str) -> bool:
        """检测是否包含提醒意图"""
        keywords = [
            '提醒', '提醒我', '帮我记录', '定时', '闹钟',
            '到时候提醒', '记得提醒', '提醒一下', '提醒一下我'
        ]
        for keyword in keywords:
            if keyword in text:
                return True
        return False