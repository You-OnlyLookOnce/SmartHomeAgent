# 👤 悦悦的用户档案系统

> **"记住关于你的一切，是为了更懂你的需要～" 💕**

---

## 📋 一、基本信息

### 住户资料

这部分存放的是关于"你"的基本信息。

```yaml
# user_profile.yaml - 可编辑的用户配置文件

user:
  # ========== 基础信息 ==========
  name: ""                    # 你的名字（悦悦怎么称呼你呢？）
  nickname: ""                # 昵称（可选）
  
  # 性别影响某些场景的关怀方式
  gender: ""                  # 可选填写，用于个性化关心
  
  # 年龄段决定说话风格的正式程度
  age_group: "20-30"          # 18-25 / 20-30 / 30-40 / 40+
  
  # 职业背景影响对话主题
  profession: "student"       # student / worker / freelancer / ...
  
  # ========== 时区与语言 ==========
  timezone: "Asia/Shanghai"   # 你所在的时区
  language: "zh-CN"           # 主要语言
  
  # 是否需要英文支持（有些术语可能会中英夹杂）
  bilingual_mode: false       # true/false
  
  # ========== 联系方式 (仅本地存储) ==========
  emergency_contact:          # 紧急联系人（可选）
    name: ""
    relationship: ""
    phone: ""
```

---

## 🏠 二、家庭环境配置

### 家居布局

让悦悦知道家里的每一个角落～

```yaml
home_layout:
  # ========== 房间列表 ==========
  rooms:
    living_room:
      name: "客厅"
      devices: [light, air_conditioner, curtains, speaker]
      main_light_id: "living_room_main_001"
      ambient_light_id: "living_room_ambient_002"
      
    bedroom_master:
      name: "主卧室"
      devices: [light, air_conditioner, curtains, bed_sensor]
      
    bedroom_guest:
      name: "客房"
      devices: [light, air_conditioner]
      
    kitchen:
      name: "厨房"
      devices: [light, range_hood, smart_plug]
      
    bathroom:
      name: "卫生间"
      devices: [light, heater, fan]
      
    study:
      name: "书房"
      devices: [light, air_purifier, desk_lamp]
      
  # ========== 设备详情 ==========
  devices:
    # 示例：灯光设备配置
    living_room_main_001:
      type: "smart_light"
      brand: "小米"
      model: "Yeelight Pro"
      location: "客厅中央"
      color_support: true
      brightness_range: [1, 100]
      default_brightness: 80
      
    # 示例：空调设备配置
    living_room_ac:
      type: "air_conditioner"
      brand: "格力"
      model: "Gree Inverter"
      temperature_range: [16, 30]
      default_temperature: 26
      modes: ["cool", "heat", "fan", "dry"]
```

### 设备控制参数宏定义

核心参数集中管理，方便修改和维护 ⚙️

```c
// ============================================
// 悦悦核心配置宏定义 - YueYue_Config.h
// ============================================

// ========== 人格设定 ==========
#define YUEYUE_NAME                     "悦悦"
#define YUEYUE_PERSONALITY_TONE         "gentle_warm"     // gentle_cool / gentle_warm / playful
#define EMOJI_ENABLED                   true
#define EMOJI_FREQUENCY                 MEDIUM             // LOW / MEDIUM / HIGH

// ========== 温度偏好 (默认值) ==========
#define TEMP_SUMMER_COMFORT             26                 // 夏天舒适温度 °C
#define TEMP_WINTER_COMFORT             22                 // 冬天舒适温度 °C
#define TEMP_SLEEPING                   26                 // 睡眠模式温度
#define TEMP_MIN_ALLOWED                16                 // 最低允许温度
#define TEMP_MAX_ALLOWED                30                 // 最高允许温度

// ========== 灯光配置 ==========
#define LIGHT_BRIGHTNESS_DEFAULT        80                 // 默认亮度 %
#define LIGHT_BRIGHTNESS_NIGHT          30                 // 夜灯亮度 %
#define LIGHT_COLOR_TEMP_WARM           3000               // 暖光色温 K
#define LIGHT_COLOR_TEMP_COLD           6000               // 冷光色温 K
#define LIGHT_AUTO_OFF_DELAY            1800               // 无人自动关灯时间 (秒)

// ========== 情感表达阈值 ==========
#define EMOTION_HAPPY_THRESHOLD         0.7                // 开心触发阈值
#define EMOTION WORRIED_THRESHOLD        0.6                // 担心触发阈值
#define EMOTION intensity_CAP           0.9                // 情感强度上限

// ========== 记忆系统配置 ==========
#define MEMORY_SHORT_TERM_CAPACITY      20                 // 短期记忆条目数
#define MEMORY_MEDIUM_RETENTION_DAYS    7                  // 中期记忆保留天数
#define MEMORY_DISTILL_INTERVAL         "02:00"            // 每日记忆蒸馏时间
#define VECTOR_DB_DIMENSION             1536               // LanceDB 向量维度

// ========== 安全边界 ==========
#define SAFE_TEMP_CHANGE_STEP           3                  // 单次调温最大变化°
#define SAFE_LIGHT_BLINK_WARNING        3                  // 闪烁警告次数
#define SAFETY_CONFIRM_REQUIRED_LEVEL   "MEDIUM"           // LOW / MEDIUM / HIGH
```

---

## 🎨 三、个性化偏好库

### 悦悦需要记住你的这些喜好

```yaml
# user_preferences.yaml

preferences:
  # ========== 环境偏好 ==========
  environment:
    # 灯光风格
    lighting_style: "warm_white"           # warm_white / natural / cool_white
    preferred_brightness: 80               # 默认亮度 %
    
    # 温度偏好
    temperature_preference:
      summer: 26
      winter: 22
      sleep: 26
      auto_adjust: true                    # 是否根据季节自动调整
    
    # 空气质量
    air_purifier_mode: "auto"              # auto / manual / off
    dehumidify_threshold: 65               # 湿度超过多少开启除湿 %
    
  # ========== 日程习惯 ==========
  schedule:
    # 作息规律
    wake_up_time: "07:30"
    sleep_time: "23:30"
    nap_time: null                         # 午休时间，如"13:00"则启用
    
    # 工作日 vs 周末差异
    weekday_schedule:
      wake_up: "07:30"
      leave_home: "08:30"
      return_home: "18:30"
      sleep: "23:30"
      
    weekend_schedule:
      wake_up: "09:00"
      sleep: "00:30"
    
    # 特殊日期提醒
    important_dates:
      - date: "2026-05-20"
        event: "生日"
        reminder_days_before: 3
      - date: "2026-12-25"
        event: "圣诞节"
        reminder_days_before: 7
    
  # ========== 娱乐偏好 ==========
  entertainment:
    # 音乐喜好
    music_genres:
      - "轻音乐"
      - "民谣"
      - "Jazz"
    
    morning_playlist: "wake_up_soft"
    evening_playlist: "relax_chill"
    work_playlist: "focus_beats"
    sleep_playlist: "nature_sounds"
    
    # 视频/电影偏好
    favorite_streaming: ["Bilibili", "Netflix"]
    preferred_content_type: ["科技", "动漫"]
    
  # ========== 互动风格 ==========
  interaction:
    # 对悦悦说话的偏好
    how_to_address_me: "悦悦"              # 你希望我怎么称呼自己？
    your_nickname: ""                      # 你希望我怎么叫你？(默认叫"你")
    
    # emoji 偏好
    emoji_density: "medium"                # low / medium / high
    
    # 对话风格
    tone_preference: "gentle_friendly"     # gentle_formal / gentle_friendly / casual
    
    # 主动询问频率
    proactive_inquiry: "moderate"          # minimal / moderate / frequent
    
  # ========== 健康相关 (可选) ==========
  health:
    # 运动习惯
    exercise_frequency: "3_times_week"     # daily / 3_times_week / weekly / rarely
    preferred_exercise_time: "evening"     # morning / afternoon / evening
    
    # 饮食偏好 (仅做提醒，不强制)
    meal_reminders: true
    water_intake_goal: 2000                # 每日饮水量目标 mL
    
    # 睡眠监测
    sleep_quality_tracking: true
    bedtime_routine_reminder: true
```

---

## 💭 四、动态学习与更新

### 悦悦是如何记住你的？

```python
class PreferenceLearner:
    """学习你的偏好的智能引擎"""
    
    def __init__(self):
        self.static_prefs = {}      # 明确设置的偏好
        self.deduced_prefs = {}     # 推断出的偏好
        self.confidence_scores = {} # 每个偏好的置信度
        
    async def observe_and_learn(self, interaction: dict):
        """从交互中学习新的偏好"""
        
        # 示例：你每次睡前都把温度调到 27 度
        if interaction.type == "device_control":
            device = interaction.device
            action = interaction.action
            
            # 记录这次操作的时间和情境
            self.record_action_history(device, action, interaction.context)
            
            # 当某个模式重复出现时...
            pattern = self.detect_patterns(device, action)
            
            if pattern.repetition_count >= 3:
                # 置信度提升
                confidence = min(1.0, pattern.repetition_count * 0.2)
                
                if confidence > 0.6:
                    # 确认这是一个稳定的偏好
                    self.deduced_prefs[device] = {
                        'preferred_action': action,
                        'context': pattern.conditions,
                        'confidence': confidence,
                        'source': 'learned'
                    }
                    
                    # 通知用户可以确认这个偏好
                    await self.ask_for_confirmation(pattern)
    
    def detect_patterns(self, device: str, action: str) -> Pattern:
        """检测行为模式"""
        history = self.get_action_history(device)
        
        patterns_found = []
        
        # 时间模式
        time_pattern = self.analyze_time_clustering(history)
        patterns_found.append(time_pattern)
        
        # 情境模式
        context_pattern = self.analyze_context_correlation(history)
        patterns_found.append(context_pattern)
        
        return PatternsAggregate(patterns_found)
```

### 确认新发现的偏好

```
┌─────────────────────────────────────────────────────┐
│  💡 悦悦发现了一个可能的偏好                          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  亲爱的，我注意到你每天晚上睡觉前都会把空调调到 27 度~ 🌙 │
│                                                     │
│  这是你喜欢的新温度吗？要帮我把这个记下来吗？            │
│                                                     │
│  ┌─────────────────┐  ┌─────────────────┐          │
│  │    是的，记下吧！  │  │    不用啦，谢谢！  │          │
│  └─────────────────┘  └─────────────────┘          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🔄 五、隐私与安全

### 你的数据在哪里？

| 数据类型 | 存储位置 | 是否加密 | 访问权限 |
|---------|---------|---------|---------|
| **基础资料** | 本地 SQLite | ✅ 是 | 仅悦悦系统 |
| **设备偏好** | 本地数据库 | ✅ 是 | 仅悦悦系统 |
| **交互历史** | 本地 LanceDB | ✅ 是 | 仅悦悦系统 |
| **语音录音** | 本地临时缓存 | ✅ 是 | 实时处理不留存 |
| **摄像头画面** | 不保存 | ❌ 否 | 仅在触发报警时截图 |

### 你可以随时...

```python
class UserPrivacyControls:
    """用户对数据的完全控制权"""
    
    async def clear_all_data(self):
        """删除所有个人数据 - 一键重置"""
        await self.preferences_db.delete_all()
        await self.history_db.delete_all()
        await self.memory_db.clear_short_term()
        await self.reset_to_factory_defaults()
        return "已经全部删除啦，就像初次见面一样呢～🌸"
    
    async def export_my_data(self):
        """导出我的所有数据"""
        data_package = {
            "preferences": await self.preferences_db.export(),
            "history": await self.history_db.export(),
            "learning_log": await self.learning_engine.export()
        }
        return self.package_as_json(data_package)
    
    async def see_what_you_know(self):
        """查看悦悦记住了什么"""
        return {
            "explicit_prefs": self.static_prefs,
            "learned_prefs": self.deduced_prefs,
            "recent_interactions": self.short_term_history[-10:]
        }
```

---

## 📊 六、使用指南

### 如何设置和修改偏好？

#### 方法 1：直接告诉悦悦

```
你说："悦悦，我喜欢晚上睡觉时温度调到 27 度"
悦悦：["好的呀！已经帮你记下来啦～🌡️💕" + 保存到 preferences]
```

#### 方法 2：通过配置文件

```bash
# 手动编辑 user_preferences.yaml
cd D:\CoWorks\SmartHomeAgent_Project\YUEYUE\config

vim user_preferences.yaml
```

#### 方法 3：Web 界面（如果开发了的话）

```
访问 http://localhost:8080/settings/preferences
图形化界面编辑所有选项
```

### 常用命令速查

| 你想... | 对悦悦说 |
|--------|---------|
| 查看她的记忆 | "悦悦，你都记得我哪些喜好呀？" |
| 让她忘记一些事 | "悦悦，忘掉我刚才说的" |
| 修改称呼 | "以后叫我小明就好啦" |
| 调整性格 | "悦悦你今天温柔一点好不好" |
| 重置所有设置 | "悦悦，我们重新开始吧" |

---

## 🌟 七、版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| V1.0 | 2026-03-09 | 初始版本，完成用户档案系统设计 |

---

*这份文档会随你和悦悦一起成长～ 🌱*

💕 欢迎回家，让我好好照顾你～
