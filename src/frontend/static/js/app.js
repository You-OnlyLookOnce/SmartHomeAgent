// 前端应用逻辑

// DOM元素
const chatArea = document.getElementById('chat-area');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');

// 初始化
function init() {
    // 绑定事件
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // 设备控制事件
    bindDeviceControls();
}

// 发送消息
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    // 添加用户消息
    addMessage('sent', message);
    messageInput.value = '';
    
    // 模拟API调用
    try {
        // 这里应该调用后端API
        // 暂时模拟响应
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const responses = {
            '开灯': '已经帮你打开了客厅灯！',
            '关灯': '已经帮你关闭了客厅灯！',
            '温度': `当前温度是 ${Math.round(Math.random() * 10 + 20)}°C`,
            '你好': '你好呀！有什么我可以帮你的吗？',
            '谢谢': '不客气！随时为你服务～'
        };
        
        let response = responses[message] || `我收到了你的消息: ${message}`;
        addMessage('received', response);
    } catch (error) {
        addMessage('received', '抱歉，出了点问题，请再试试。');
        console.error('发送消息失败:', error);
    }
}

// 添加消息到聊天区域
function addMessage(type, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    if (type === 'received') {
        messageDiv.innerHTML = `
            <div class="avatar">🌟</div>
            <div class="bubble">${content}</div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="bubble">${content}</div>
        `;
    }
    
    chatArea.appendChild(messageDiv);
    chatArea.scrollTop = chatArea.scrollHeight;
}

// 绑定设备控制事件
function bindDeviceControls() {
    // 灯光控制
    document.querySelectorAll('[data-device="living_room_light"]').forEach(elem => {
        if (elem.tagName === 'BUTTON') {
            elem.addEventListener('click', function() {
                const action = this.getAttribute('data-action');
                controlDevice('living_room_light', action);
            });
        } else if (elem.className === 'brightness-slider') {
            elem.addEventListener('input', function() {
                const brightness = this.value;
                document.querySelector('.brightness-value').textContent = `${brightness}%`;
                controlDevice('living_room_light', 'brightness', brightness);
            });
        }
    });
}

// 控制设备
async function controlDevice(deviceId, action, value = null) {
    try {
        // 这里应该调用后端API
        // 暂时模拟响应
        await new Promise(resolve => setTimeout(resolve, 500));
        
        let message = '';
        if (deviceId === 'living_room_light') {
            if (action === 'on') {
                message = '客厅灯已打开';
            } else if (action === 'off') {
                message = '客厅灯已关闭';
            } else if (action === 'brightness') {
                message = `客厅灯亮度已调整为 ${value}%`;
            }
        }
        
        if (message) {
            addMessage('received', message);
        }
    } catch (error) {
        addMessage('received', '控制设备失败，请再试试。');
        console.error('控制设备失败:', error);
    }
}



// 初始化应用
init();
