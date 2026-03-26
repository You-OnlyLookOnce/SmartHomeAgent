// 前端应用逻辑

// DOM元素
const chatArea = document.getElementById('chat-area');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const taskInput = document.getElementById('task-input');
const createTaskBtn = document.getElementById('create-task-btn');
const taskList = document.getElementById('task-list');
const chatList = document.getElementById('chat-list');
const newChatBtn = document.getElementById('new-chat-btn');
const renameChatBtn = document.getElementById('rename-chat-btn');
const deleteChatBtn = document.getElementById('delete-chat-btn');
const sectionTitle = document.getElementById('section-title');

// 模态窗口元素
const nameModal = document.getElementById('name-modal');
const chatNameInput = document.getElementById('chat-name-input');
const closeModalBtn = document.getElementById('close-modal-btn');
const cancelCreateBtn = document.getElementById('cancel-create-btn');
const confirmCreateBtn = document.getElementById('confirm-create-btn');

// 当前会话ID
let currentSessionId = null;
// 窗口唯一标识符，用于在本地存储中区分不同窗口的会话状态
const windowId = 'window_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
// 是否正在进行流式响应
let isStreaming = false;
// 搜索相关变量
let searchTimeout = null;
let chatHistory = [];
// 请求去重相关变量
let processingMessages = new Set(); // 存储正在处理的消息ID
console.log('窗口唯一标识符:', windowId);

// 初始化函数将在后面定义



// 切换到聊天界面
function switchToChatSection() {
    const navItems = document.querySelectorAll('.nav-item');
    const contentSections = document.querySelectorAll('.content-section');
    const sectionTitle = document.getElementById('section-title');
    
    // 更新导航项状态
    navItems.forEach(nav => nav.classList.remove('active'));
    
    // 更新内容区域
    contentSections.forEach(sec => sec.classList.remove('active'));
    document.getElementById('chat-section').classList.add('active');
    
    // 更新标题
    if (sectionTitle) {
        sectionTitle.textContent = '聊天';
    }
    
    // 尝试从本地存储恢复会话ID
    const savedSessionId = localStorage.getItem(`currentSessionId_${windowId}`);
    if (savedSessionId) {
        currentSessionId = savedSessionId;
        console.log('从本地存储恢复会话ID:', currentSessionId);
    }
    
    // 显示初始化界面或对话历史
    if (currentSessionId) {
        // 不再自动重新加载对话历史，避免新消息被覆盖
        // 只有在切换到不同对话时才需要重新加载
        console.log('切换到聊天界面，保持当前对话内容');
        // 确保聊天区域可见
        if (chatArea) {
            chatArea.style.display = 'block';
        }
        hideInitializationUI();
    } else {
        // 没有会话时显示初始化界面
        showInitializationUI();
    }
}





// 设备状态缓存
let deviceStates = {};

/**
 * 加载设备列表并恢复状态
 * 执行流程：
 * 1. 从后端获取设备列表
 * 2. 恢复之前的设备配置
 * 3. 保持状态同步
 */
async function loadDevicesAndRestoreState() {
    console.log('[设备管理] 开始加载设备列表和状态...');

    try {
        // 从后端获取设备列表
        const response = await fetch('/api/devices');

        if (!response.ok) {
            throw new Error('获取设备列表失败');
        }

        const data = await response.json();

        if (data.success && data.devices) {
            console.log(`[设备管理] 加载了 ${data.devices.length} 个设备`);

            // 存储设备状态
            data.devices.forEach(device => {
                deviceStates[device.device_id] = device;
            });

            // 恢复设备UI状态
            restoreDeviceUIState(data.devices);

            // 启动定期状态同步
            startDeviceStateSync();
        } else {
            console.log('[设备管理] 没有设备或加载失败');
        }
    } catch (error) {
        console.error('[设备管理] 加载设备失败:', error);
    }
}

/**
 * 恢复设备UI状态
 * @param {Array} devices - 设备列表
 */
function restoreDeviceUIState(devices) {
    console.log('[设备管理] 恢复设备UI状态...');

    devices.forEach(device => {
        const deviceId = device.device_id;
        const deviceType = device.device_type;
        const state = device.current_state || {};

        // 根据设备类型恢复UI
        if (deviceType === 'lamp') {
            restoreLampUI(deviceId, state);
        } else if (deviceType === 'air_conditioner') {
            restoreACUI(deviceId, state);
        } else if (deviceType === 'curtain') {
            restoreCurtainUI(deviceId, state);
        }
    });
}

/**
 * 恢复台灯UI状态
 * @param {string} deviceId - 设备ID
 * @param {Object} state - 设备状态
 */
function restoreLampUI(deviceId, state) {
    const power = state.power === 'on';
    const brightness = state.brightness || 50;
    const colorTemp = state.color_temp || 'normal';

    // 查找对应的UI元素
    const powerBtn = document.querySelector(`[data-device="${deviceId}"][data-action="power_toggle"]`);
    const brightnessSlider = document.querySelector(`[data-device="${deviceId}"].brightness-slider`);
    const brightnessValue = document.querySelector(`[data-device="${deviceId}"].brightness-value`);

    if (powerBtn) {
        powerBtn.textContent = power ? '关闭' : '打开';
        powerBtn.classList.toggle('active', power);
    }

    if (brightnessSlider) {
        brightnessSlider.value = brightness;
    }

    if (brightnessValue) {
        brightnessValue.textContent = `${brightness}%`;
    }

    console.log(`[设备管理] 台灯 ${deviceId} 状态已恢复: power=${power}, brightness=${brightness}`);
}

/**
 * 恢复空调UI状态
 * @param {string} deviceId - 设备ID
 * @param {Object} state - 设备状态
 */
function restoreACUI(deviceId, state) {
    const power = state.power === 'on';
    const temperature = state.temperature || 26;
    const mode = state.mode || 'cool';
    const fanSpeed = state.fan_speed || 3;

    // 查找对应的UI元素
    const powerBtn = document.querySelector(`[data-device="${deviceId}"][data-action="power_toggle"]`);
    const tempDisplay = document.querySelector(`[data-device="${deviceId}"].temperature-display`);
    const modeBtn = document.querySelector(`[data-device="${deviceId}"][data-action="mode"]`);
    const fanSpeedSlider = document.querySelector(`[data-device="${deviceId}"].fan-speed-slider`);

    if (powerBtn) {
        powerBtn.textContent = power ? '关闭' : '打开';
        powerBtn.classList.toggle('active', power);
    }

    if (tempDisplay) {
        tempDisplay.textContent = `${temperature}°C`;
    }

    if (modeBtn) {
        const modeNames = { cool: '制冷', heat: '制热', dry: '除湿', fan: '送风', auto: '自动' };
        modeBtn.textContent = modeNames[mode] || mode;
    }

    if (fanSpeedSlider) {
        fanSpeedSlider.value = fanSpeed;
    }

    console.log(`[设备管理] 空调 ${deviceId} 状态已恢复: power=${power}, temp=${temperature}, mode=${mode}`);
}

/**
 * 恢复窗帘UI状态
 * @param {string} deviceId - 设备ID
 * @param {Object} state - 设备状态
 */
function restoreCurtainUI(deviceId, state) {
    const position = state.position || 0;
    const isOpen = position > 0;

    // 查找对应的UI元素
    const positionSlider = document.querySelector(`[data-device="${deviceId}"].position-slider`);
    const positionValue = document.querySelector(`[data-device="${deviceId}"].position-value`);
    const openBtn = document.querySelector(`[data-device="${deviceId}"][data-action="open"]`);
    const closeBtn = document.querySelector(`[data-device="${deviceId}"][data-action="close"]`);

    if (positionSlider) {
        positionSlider.value = position;
    }

    if (positionValue) {
        positionValue.textContent = `${position}%`;
    }

    if (openBtn) {
        openBtn.classList.toggle('active', isOpen);
    }

    if (closeBtn) {
        closeBtn.classList.toggle('active', !isOpen);
    }

    console.log(`[设备管理] 窗帘 ${deviceId} 状态已恢复: position=${position}`);
}

/**
 * 启动设备状态定期同步
 * 每30秒同步一次设备状态
 */
function startDeviceStateSync() {
    console.log('[设备管理] 启动定期状态同步...');

    // 立即同步一次
    syncDeviceStates();

    // 每30秒同步一次
    setInterval(syncDeviceStates, 30000);
}

/**
 * 同步设备状态
 * 从后端获取最新的设备状态并更新UI
 */
async function syncDeviceStates() {
    try {
        const deviceIds = Object.keys(deviceStates);

        for (const deviceId of deviceIds) {
            const response = await fetch(`/api/devices/${deviceId}/status`);

            if (response.ok) {
                const data = await response.json();

                if (data.success && data.status) {
                    // 更新本地状态
                    deviceStates[deviceId].current_state = data.status;

                    // 更新UI
                    const device = deviceStates[deviceId];
                    if (device.device_type === 'lamp') {
                        restoreLampUI(deviceId, data.status);
                    } else if (device.device_type === 'air_conditioner') {
                        restoreACUI(deviceId, data.status);
                    } else if (device.device_type === 'curtain') {
                        restoreCurtainUI(deviceId, data.status);
                    }
                }
            }
        }

        console.log('[设备管理] 状态同步完成');
    } catch (error) {
        console.error('[设备管理] 状态同步失败:', error);
    }
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
    console.log(`[设备控制] 发送命令: device=${deviceId}, action=${action}, value=${value}`);

    try {
        // 构建命令参数
        let command = action;
        let params = {};

        // 根据action类型构建命令
        if (action === 'on' || action === 'off') {
            command = action === 'on' ? 'power_on' : 'power_off';
        } else if (action === 'brightness') {
            command = 'set_brightness';
            params = { brightness: parseInt(value) };
        } else if (action === 'temperature') {
            command = 'set_temperature';
            params = { temperature: parseInt(value) };
        } else if (action === 'mode') {
            command = 'set_mode';
            params = { mode: value };
        } else if (action === 'fan_speed') {
            command = 'set_fan_speed';
            params = { fan_speed: parseInt(value) };
        } else if (action === 'position') {
            command = 'set_position';
            params = { position: parseInt(value) };
        } else if (action === 'open') {
            command = 'open';
        } else if (action === 'close') {
            command = 'close';
        } else if (action === 'stop') {
            command = 'stop';
        }

        // 调用后端API
        const response = await fetch(`/api/devices/${deviceId}/command`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                command: command,
                params: params
            })
        });

        if (!response.ok) {
            throw new Error('API调用失败');
        }

        const data = await response.json();

        if (data.success) {
            const message = data.message || `设备已${action === 'on' ? '打开' : action === 'off' ? '关闭' : '调整'}`;
            addMessage('received', message);

            // 更新本地状态缓存
            if (deviceStates[deviceId]) {
                if (action === 'on' || action === 'off') {
                    deviceStates[deviceId].current_state.power = action;
                } else if (action === 'brightness') {
                    deviceStates[deviceId].current_state.brightness = parseInt(value);
                } else if (action === 'temperature') {
                    deviceStates[deviceId].current_state.temperature = parseInt(value);
                } else if (action === 'mode') {
                    deviceStates[deviceId].current_state.mode = value;
                } else if (action === 'fan_speed') {
                    deviceStates[deviceId].current_state.fan_speed = parseInt(value);
                } else if (action === 'position') {
                    deviceStates[deviceId].current_state.position = parseInt(value);
                }
            }

            // 立即同步状态
            syncDeviceStates();
        } else {
            addMessage('received', data.message || '控制设备失败，请再试试。');
        }
    } catch (error) {
        addMessage('received', '控制设备失败，请再试试。');
        console.error('控制设备失败:', error);
    }
}



// 创建任务
async function createTask() {
    const taskContent = taskInput.value.trim();
    if (!taskContent) return;
    
    try {
        // 使用现有的 scheduler 端点
        const response = await fetch('/api/scheduler/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                title: taskContent, 
                content: taskContent, 
                reminder_time: new Date().toISOString(),
                repeat_type: 'once'
            })
        });
        
        if (!response.ok) {
            throw new Error('API调用失败');
        }
        
        const data = await response.json();
        
        if (data.success) {
            addMessage('received', `任务已创建: ${taskContent}`);
            taskInput.value = '';
            loadTasks();
        } else {
            addMessage('received', '创建任务失败，请再试试。');
        }
    } catch (error) {
        addMessage('received', '创建任务失败，请再试试。');
        console.error('创建任务失败:', error);
    }
}

// 加载任务列表
async function loadTasks() {
    if (!taskList) return;
    
    try {
        // 使用现有的 scheduler 端点
        const response = await fetch('/api/scheduler/list');
        
        if (!response.ok) {
            throw new Error('API调用失败');
        }
        
        const data = await response.json();
        
        if (data.success) {
            renderTasks(data.tasks || []);
        }
    } catch (error) {
        console.error('加载任务失败:', error);
    }
}

// 渲染任务列表
function renderTasks(tasks) {
    if (!taskList) return;
    
    taskList.innerHTML = '';
    
    if (tasks.length === 0) {
        const emptyTask = document.createElement('div');
        emptyTask.className = 'task-item';
        emptyTask.innerHTML = '<div class="task-content">暂无任务</div>';
        taskList.appendChild(emptyTask);
        return;
    }
    
    tasks.forEach(task => {
        const taskItem = document.createElement('div');
        taskItem.className = 'task-item';
        taskItem.innerHTML = `
            <div class="task-content">${task.title || task}</div>
            <div class="task-status ${task.status || 'pending'}">${task.status || '待处理'}</div>
        `;
        taskList.appendChild(taskItem);
    });
}

// 记忆管理相关函数

// 绑定记忆管理标签页事件
function bindMemoryTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.getAttribute('data-tab');
            
            // 更新标签按钮状态
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // 更新标签内容
            tabPanes.forEach(pane => pane.classList.remove('active'));
            document.getElementById(`${tab}-tab`).classList.add('active');
        });
    });
}

// 绑定任务管理标签页事件
function bindTaskTabs() {
    const taskTabBtns = document.querySelectorAll('.task-tabs .tab-btn');
    const taskTabPanes = document.querySelectorAll('.task-panel .tab-pane');
    
    taskTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.getAttribute('data-tab');
            
            // 更新标签按钮状态
            taskTabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // 更新标签内容
            taskTabPanes.forEach(pane => pane.classList.remove('active'));
            document.getElementById(`${tab}-tab`).classList.add('active');
            
            // 加载对应标签的内容
            if (tab === 'scheduled') {
                loadScheduleList();
            }
        });
    });
}

// 加载记忆文件
async function loadMemoryFiles() {
    try {
        // 加载人格文件
        const soulResponse = await fetch('/api/memory/soul');
        if (soulResponse.ok) {
            const soulData = await soulResponse.json();
            if (soulData.success && soulData.data) {
                const soulContent = document.getElementById('soul-content');
                soulContent.value = soulData.data;
                // 设置人格文件为只读
                soulContent.readOnly = true;
                soulContent.style.backgroundColor = '#f5f5f5';
                // 禁用保存按钮
                document.getElementById('save-soul-btn').disabled = true;
                document.getElementById('save-soul-btn').style.opacity = '0.5';
            }
        }
        
        // 加载记忆文件
        const memoryResponse = await fetch('/api/memory/long-term');
        if (memoryResponse.ok) {
            const memoryData = await memoryResponse.json();
            if (memoryData.success && memoryData.data) {
                document.getElementById('memory-content').value = memoryData.data;
            }
        }
    } catch (error) {
        console.error('加载记忆文件失败:', error);
    }
}

// 保存人格文件
async function saveSoulFile() {
    // 人格文件是只读的，不允许修改
    alert('人格文件不可修改');
    return;
}

// 保存记忆文件
async function saveMemoryFile() {
    const content = document.getElementById('memory-content').value;
    try {
        const response = await fetch('/api/memory/long-term', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content: content })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                alert('记忆文件保存成功');
            } else {
                alert('保存失败: ' + (data.message || '未知错误'));
            }
        } else {
            alert('保存失败: API调用失败');
        }
    } catch (error) {
        console.error('保存记忆文件失败:', error);
        alert('保存失败: ' + error.message);
    }
}

// 定时任务相关函数

// 加载定时任务列表
async function loadScheduleList() {
    const scheduleList = document.getElementById('schedule-list');
    if (!scheduleList) return;
    
    try {
        const response = await fetch('/api/scheduler/list');
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                renderScheduleList(data.tasks || []);
                // 更新小红点
                updateTaskBadge(data.pending_count || 0);
            }
        }
    } catch (error) {
        console.error('加载定时任务失败:', error);
    }
}

// 渲染定时任务列表
function renderScheduleList(tasks) {
    const scheduleList = document.getElementById('schedule-list');
    if (!scheduleList) return;
    
    scheduleList.innerHTML = '';
    
    if (tasks.length === 0) {
        const emptySchedule = document.createElement('div');
        emptySchedule.className = 'schedule-item';
        emptySchedule.innerHTML = '<div class="schedule-content">暂无定时任务</div>';
        scheduleList.appendChild(emptySchedule);
        return;
    }
    
    tasks.forEach(task => {
        const scheduleItem = document.createElement('div');
        // 根据任务状态设置不同的样式
        let itemClass = 'schedule-item';
        if (task.status === 'active') {
            itemClass += ' active';
        } else if (task.status === 'completed') {
            itemClass += ' completed';
        }
        scheduleItem.className = itemClass;
        
        // 格式化时间
        const reminderTime = new Date(task.reminder_time);
        const timeString = reminderTime.toLocaleString('zh-CN');
        
        // 状态文本
        let statusText = '未到点';
        if (task.status === 'active') {
            statusText = '正在看';
        } else if (task.status === 'completed') {
            statusText = '已知晓';
        }
        
        scheduleItem.innerHTML = `
            <div class="schedule-content">${task.title}</div>
            <div class="schedule-time">${timeString}</div>
            <div class="schedule-status ${task.status || 'pending'}">${statusText}</div>
            <div class="schedule-actions">
                ${task.status !== 'completed' ? `<button class="confirm-btn" onclick="confirmTask('${task.id}')">已经知晓</button>` : ''}
                <button class="delete-btn" onclick="deleteSchedule('${task.id}')">删除</button>
            </div>
        `;
        scheduleList.appendChild(scheduleItem);
    });
}

// 确认任务
async function confirmTask(taskId) {
    try {
        const response = await fetch(`/api/scheduler/${taskId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: 'completed' })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                alert('任务已确认');
                loadScheduleList();
            } else {
                alert('确认失败: ' + (data.message || '未知错误'));
            }
        } else {
            alert('确认失败: API调用失败');
        }
    } catch (error) {
        console.error('确认任务失败:', error);
        alert('确认失败: ' + error.message);
    }
}

// 删除定时任务
async function deleteSchedule(scheduleId) {
    if (confirm('确定要删除这个定时任务吗？')) {
        try {
            const response = await fetch(`/api/scheduler/${scheduleId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    alert('定时任务删除成功');
                    loadScheduleList();
                } else {
                    alert('删除失败: ' + (data.message || '未知错误'));
                }
            } else {
                alert('删除失败: API调用失败');
            }
        } catch (error) {
            console.error('删除定时任务失败:', error);
            alert('删除失败: ' + error.message);
        }
    }
}

// 创建定时任务
async function createSchedule() {
    const taskInput = document.getElementById('schedule-task-input');
    const timeInput = document.getElementById('schedule-time-input');
    
    const title = taskInput.value.trim();
    const reminder_time = timeInput.value;
    
    if (!title || !reminder_time) {
        alert('请输入任务内容和时间');
        return;
    }
    
    try {
        const response = await fetch('/api/scheduler/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                title: title, 
                content: title, 
                reminder_time: reminder_time,
                repeat_type: 'once'
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                alert('定时任务创建成功');
                taskInput.value = '';
                timeInput.value = '';
                loadScheduleList();
            } else {
                alert('创建失败: ' + (data.message || '未知错误'));
            }
        } else {
            alert('创建失败: API调用失败');
        }
    } catch (error) {
        console.error('创建定时任务失败:', error);
        alert('创建失败: ' + error.message);
    }
}



// 检查任务提醒
async function checkTaskReminders() {
    try {
        const response = await fetch('/api/scheduler/pending-count');
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                updateTaskBadge(data.count || 0);
            }
        }
    } catch (error) {
        console.error('检查任务提醒失败:', error);
    }
}

// 更新任务徽章
function updateTaskBadge(count) {
    // 检查是否已经存在小红点
    let badge = document.getElementById('task-badge');
    if (!badge) {
        // 创建小红点元素
        badge = document.createElement('span');
        badge.id = 'task-badge';
        badge.className = 'notification-badge';
        
        // 将小红点添加到任务管理导航项
        const taskNavItem = document.querySelector('.nav-item[data-section="task"]');
        if (taskNavItem) {
            taskNavItem.appendChild(badge);
        }
    }
    
    // 设置小红点计数
    badge.textContent = count;
    badge.style.display = count > 0 ? 'flex' : 'none';
}

// 清除通知小红点
function clearNotificationBadge() {
    const badge = document.getElementById('task-badge');
    if (badge) {
        badge.style.display = 'none';
    }
}

// 记忆蒸馏相关函数

// 绑定记忆蒸馏标签页事件
function bindDistillationTabs() {
    const distillationTabBtns = document.querySelectorAll('.distillation-tabs .tab-btn');
    const distillationTabPanes = document.querySelectorAll('.distillation-panel .tab-pane');
    
    distillationTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.getAttribute('data-tab');
            
            // 更新标签按钮状态
            distillationTabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // 更新标签内容
            distillationTabPanes.forEach(pane => pane.classList.remove('active'));
            document.getElementById(`${tab}-tab`).classList.add('active');
        });
    });
}

// 开始记忆蒸馏
async function startDistillation() {
    const statusDiv = document.getElementById('distillation-status');
    const resultDiv = document.getElementById('distillation-result');
    if (statusDiv) {
        statusDiv.innerHTML = '<p>正在进行记忆蒸馏...</p>';
    }
    if (resultDiv) {
        resultDiv.innerHTML = '';
    }
    
    try {
        const response = await fetch('/api/memory/distill', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                if (statusDiv) {
                    statusDiv.innerHTML = '<p class="success">记忆蒸馏完成！</p>';
                }
                if (resultDiv) {
                    resultDiv.innerHTML = `
                        <h4>蒸馏结果</h4>
                        <div class="result-item">
                            <h5>获得的新知识：</h5>
                            <p>系统已从最近的对话中提取重要信息，并更新到长期记忆中。</p>
                        </div>
                        <div class="result-item">
                            <h5>知识结构变化：</h5>
                            <p>记忆库已优化，去除冗余内容，保留核心信息。</p>
                        </div>
                        <div class="result-item">
                            <h5>建议：</h5>
                            <p>定期执行记忆蒸馏可以保持记忆库的整洁和有效性。</p>
                        </div>
                    `;
                }
            } else {
                if (statusDiv) {
                    statusDiv.innerHTML = '<p class="error">蒸馏失败: ' + (data.message || '未知错误') + '</p>';
                }
            }
        } else {
            if (statusDiv) {
                statusDiv.innerHTML = '<p class="error">蒸馏失败: API调用失败</p>';
            }
        }
    } catch (error) {
        console.error('记忆蒸馏失败:', error);
        if (statusDiv) {
            statusDiv.innerHTML = '<p class="error">蒸馏失败: ' + error.message + '</p>';
        }
    }
}

// 保存定时蒸馏设置
async function saveDistillSettings() {
    const frequency = document.getElementById('distill-frequency').value;
    const time = document.getElementById('distill-time').value;
    const days = document.getElementById('distill-days').value;
    
    try {
        // 这里应该调用后端API保存设置
        // 暂时使用模拟数据
        alert('定时蒸馏设置保存成功！');
    } catch (error) {
        console.error('保存定时蒸馏设置失败:', error);
        alert('保存失败: ' + error.message);
    }
}

// 绑定新功能模块的事件
function bindNewModuleEvents() {
    // 记忆管理事件
    const saveSoulBtn = document.getElementById('save-soul-btn');
    if (saveSoulBtn) {
        saveSoulBtn.addEventListener('click', saveSoulFile);
    }
    
    const saveMemoryBtn = document.getElementById('save-memory-btn');
    if (saveMemoryBtn) {
        saveMemoryBtn.addEventListener('click', saveMemoryFile);
    }
    
    // 定时任务事件
    const createScheduleBtn = document.getElementById('create-schedule-btn');
    if (createScheduleBtn) {
        createScheduleBtn.addEventListener('click', createSchedule);
    }
    

    
    // 定时任务标签页切换
    const schedulerTabBtns = document.querySelectorAll('.scheduler-tab-btn');
    schedulerTabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tab = this.getAttribute('data-scheduler-tab');
            
            // 更新标签按钮状态
            schedulerTabBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // 更新标签内容
            const tabPanes = document.querySelectorAll('.scheduler-tab-pane');
            tabPanes.forEach(pane => pane.classList.remove('active'));
            if (tab === 'regular') {
                document.getElementById('regular-scheduler-tab').classList.add('active');
            } else if (tab === 'batch_inference') {
                document.getElementById('batch-inference-scheduler-tab').classList.add('active');
            }
        });
    });
    
    // 记忆蒸馏事件
    const startDistillationBtn = document.getElementById('start-distillation-btn');
    if (startDistillationBtn) {
        startDistillationBtn.addEventListener('click', startDistillation);
    }
    
    const saveDistillSettingsBtn = document.getElementById('save-distill-settings-btn');
    if (saveDistillSettingsBtn) {
        saveDistillSettingsBtn.addEventListener('click', saveDistillSettings);
    }
    
    // 绑定记忆管理标签页事件
    bindMemoryTabs();
    
    // 绑定任务管理标签页事件
    bindTaskTabs();
    
    // 绑定记忆蒸馏标签页事件
    bindDistillationTabs();
}

// 初始化应用
function init() {
    // 从本地存储中加载之前保存的会话ID，使用窗口唯一标识符作为键
    const savedSessionId = localStorage.getItem(`currentSessionId_${windowId}`);
    if (savedSessionId) {
        currentSessionId = savedSessionId;
        console.log('从本地存储加载会话ID:', currentSessionId);
        // 不直接加载对话历史，由 loadChats 函数处理
    } else {
        // 没有保存的会话ID，显示初始化界面
        console.log('没有保存的会话ID，显示初始化界面');
        showInitializationUI();
    }

    // 加载设备列表和状态
    loadDevicesAndRestoreState();

    // 绑定事件
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
        console.log('发送按钮事件绑定成功');
    } else {
        console.error('发送按钮未找到');
    }
    if (messageInput) {
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        console.log('输入框回车键事件绑定成功');
    } else {
        console.error('输入框未找到');
    }
    
    // 对话管理事件
    console.log('newChatBtn:', newChatBtn);
    console.log('renameChatBtn:', renameChatBtn);
    console.log('deleteChatBtn:', deleteChatBtn);
    
    if (newChatBtn) {
        newChatBtn.addEventListener('click', createNewChat);
        console.log('新建对话按钮事件绑定成功');
    } else {
        console.error('新建对话按钮未找到');
    }
    if (renameChatBtn) {
        renameChatBtn.addEventListener('click', renameCurrentChat);
        console.log('重命名按钮事件绑定成功');
    } else {
        console.error('重命名按钮未找到');
    }
    if (deleteChatBtn) {
        deleteChatBtn.addEventListener('click', deleteCurrentChat);
        console.log('删除按钮事件绑定成功');
    } else {
        console.error('删除按钮未找到');
    }
    
    // 绑定对话管理标题点击事件
    const chatHeader = document.querySelector('.chat-header h3');
    if (chatHeader) {
        chatHeader.addEventListener('click', switchToChatSection);
        console.log('对话管理标题点击事件绑定成功');
    } else {
        console.error('对话管理标题未找到');
    }
    
    // 模态窗口事件
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeModal);
        console.log('关闭模态窗口按钮事件绑定成功');
    } else {
        console.error('关闭模态窗口按钮未找到');
    }
    if (cancelCreateBtn) {
        cancelCreateBtn.addEventListener('click', closeModal);
        console.log('取消创建按钮事件绑定成功');
    } else {
        console.error('取消创建按钮未找到');
    }
    if (confirmCreateBtn) {
        confirmCreateBtn.addEventListener('click', confirmCreateChat);
        console.log('确认创建按钮事件绑定成功');
    } else {
        console.error('确认创建按钮未找到');
    }
    // 为输入框添加回车键事件
    if (chatNameInput) {
        chatNameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                confirmCreateChat();
            }
        });
        console.log('输入框回车键事件绑定成功');
    } else {
        console.error('对话名称输入框未找到');
    }
    
    // 任务管理事件
    if (createTaskBtn) {
        createTaskBtn.addEventListener('click', createTask);
        taskInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                createTask();
            }
        });
    }
    
    // 设备控制事件
    bindDeviceControls();
    
    // 加载定时任务列表
    loadScheduleList();
    
    // 绑定侧边栏导航事件
    bindSidebarNavigation();
    
    // 绑定新功能模块的事件
    bindNewModuleEvents();
    
    // 绑定搜索事件
    bindSearchEvents();
    
    // 加载对话列表
    loadChats();
    
    // 检查任务提醒
    checkTaskReminders();
    
    // 每60秒检查一次任务提醒
    setInterval(checkTaskReminders, 60000);
    
    // 添加窗口焦点事件处理 - 移除自动重新加载对话历史，避免AI回复被覆盖
    window.addEventListener('focus', () => {
        console.log('窗口获得焦点');
        if (currentSessionId) {
            console.log('当前会话ID:', currentSessionId);
            // 不再自动重新加载对话历史，避免AI回复被覆盖
            // 只有在特定情况下（如手动刷新）才重新加载
        } else {
            console.log('当前没有活跃会话');
        }
    });
}

// 显示通知消息
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 显示动画
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // 3秒后自动消失
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// 备忘录相关函数

// 全局变量用于存储备忘录数据和当前筛选状态
let allMemos = [];
let currentFilter = { category: 'all', sortBy: 'updated_at', sortOrder: 'desc' };

// 加载备忘录列表
async function loadMemos() {
    try {
        const response = await fetch('/api/memos', {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        if (!response.ok) {
            throw new Error(`API调用失败: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        if (data.success) {
            allMemos = data.memos;
            applyFilters();
        } else {
            showNotification('加载备忘录失败: ' + (data.message || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('加载备忘录失败:', error);
        showNotification('加载备忘录失败，请检查网络连接后重试', 'error');
    }
}

// 应用筛选和排序
function applyFilters() {
    let filteredMemos = [...allMemos];
    
    // 按分类筛选
    if (currentFilter.category !== 'all') {
        filteredMemos = filteredMemos.filter(memo => memo.category === currentFilter.category);
    }
    
    // 排序
    filteredMemos.sort((a, b) => {
        if (currentFilter.sortBy === 'updated_at') {
            const dateA = new Date(a.updated_at);
            const dateB = new Date(b.updated_at);
            return currentFilter.sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
        } else if (currentFilter.sortBy === 'priority') {
            const priorityOrder = { high: 3, normal: 2, low: 1 };
            return currentFilter.sortOrder === 'desc' ? 
                priorityOrder[b.priority] - priorityOrder[a.priority] : 
                priorityOrder[a.priority] - priorityOrder[b.priority];
        }
        return 0;
    });
    
    renderMemos(filteredMemos);
}

// 绑定筛选和排序事件
function bindMemoFilters() {
    // 分类筛选
    const categoryFilter = document.getElementById('memo-category-filter');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', function() {
            currentFilter.category = this.value;
            applyFilters();
        });
    }
    
    // 排序选择
    const sortSelect = document.getElementById('memo-sort');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            const [sortBy, sortOrder] = this.value.split('-');
            currentFilter.sortBy = sortBy;
            currentFilter.sortOrder = sortOrder;
            applyFilters();
        });
    }
}

// 渲染备忘录列表
function renderMemos(memos) {
    const memoList = document.getElementById('memo-list');
    if (!memoList) return;
    
    memoList.innerHTML = '';
    
    if (memos.length === 0) {
        const emptyMemo = document.createElement('div');
        emptyMemo.className = 'memo-item';
        emptyMemo.innerHTML = '<div class="memo-item-content">暂无备忘录</div>';
        memoList.appendChild(emptyMemo);
        return;
    }
    
    memos.forEach(memo => {
        const memoItem = document.createElement('div');
        memoItem.className = 'memo-item';
        
        // 格式化日期
        const updatedAt = new Date(memo.updated_at);
        const dateString = updatedAt.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        // 处理标签
        const tagsHtml = memo.tags && memo.tags.length > 0 ? 
            memo.tags.map(tag => `<span class="memo-item-tag">${tag}</span>`).join('') : '';
        
        // 处理分类
        const categoryText = memo.category ? {
            'personal': '个人',
            'work': '工作',
            'study': '学习',
            'other': '其他'
        }[memo.category] || memo.category : '个人';
        
        memoItem.innerHTML = `
            <div class="memo-item-header">
                <div class="memo-item-title">${memo.title}</div>
                <div class="memo-item-meta">
                    <span class="memo-item-category">${categoryText}</span>
                    <span class="memo-item-priority ${memo.priority}">${memo.priority === 'high' ? '高' : memo.priority === 'normal' ? '中' : '低'}</span>
                    <span class="memo-item-date">${dateString}</span>
                </div>
            </div>
            <div class="memo-item-content">${memo.content}</div>
            ${tagsHtml ? `<div class="memo-item-tags">${tagsHtml}</div>` : ''}
            <div class="memo-item-actions">
                <button class="memo-item-action-btn" onclick="editMemo('${memo.id}')">编辑</button>
                <button class="memo-item-action-btn" onclick="deleteMemo('${memo.id}')">删除</button>
            </div>
        `;
        
        memoList.appendChild(memoItem);
    });
}

// 显示创建备忘录模态窗口
function showCreateMemoModal() {
    document.getElementById('memo-modal-title').textContent = '创建备忘录';
    document.getElementById('memo-id').value = '';
    document.getElementById('memo-title').value = '';
    document.getElementById('memo-content').value = '';
    document.getElementById('memo-tags').value = '';
    document.getElementById('memo-priority').value = 'normal';
    // 添加分类选择
    if (document.getElementById('memo-category')) {
        document.getElementById('memo-category').value = 'personal';
    }
    
    const modal = document.getElementById('memo-modal');
    modal.style.display = 'flex';
    modal.classList.add('modal-visible');
    
    // 初始化标签输入处理
    handleTagInput();
}

// 检查是否有未保存的更改
function hasUnsavedChanges() {
    const title = document.getElementById('memo-title').value.trim();
    const content = document.getElementById('memo-content').value.trim();
    const tags = document.getElementById('memo-tags').value.trim();
    return title || content || tags;
}

// 关闭备忘录模态窗口
function closeMemoModal() {
    // 检查是否有未保存的更改
    if (hasUnsavedChanges()) {
        if (!confirm('您有未保存的更改，确定要关闭吗？')) {
            return;
        }
    }
    
    const modal = document.getElementById('memo-modal');
    modal.classList.remove('modal-visible');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

// 处理标签输入
function handleTagInput() {
    const tagsInput = document.getElementById('memo-tags');
    if (tagsInput) {
        tagsInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' || e.key === ',') {
                e.preventDefault();
                const value = this.value.trim();
                if (value) {
                    // 确保标签不重复
                    const currentTags = this.value.split(',').map(tag => tag.trim()).filter(tag => tag);
                    if (!currentTags.includes(value)) {
                        this.value = currentTags.concat(value).join(', ') + ', ';
                    }
                }
            }
        });
    }
}

// 保存备忘录
async function saveMemo() {
    const memoId = document.getElementById('memo-id').value;
    const title = document.getElementById('memo-title').value.trim();
    const content = document.getElementById('memo-content').value.trim();
    const tagsInput = document.getElementById('memo-tags').value.trim();
    const priority = document.getElementById('memo-priority').value;
    // 添加分类信息
    const category = document.getElementById('memo-category') ? document.getElementById('memo-category').value : 'personal';
    
    if (!title) {
        showNotification('请输入备忘录标题', 'warning');
        return;
    }
    
    // 处理标签
    const tags = tagsInput ? tagsInput.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
    
    // 对于更新操作，添加确认机制
    if (memoId) {
        if (!confirm('确定要更新这个备忘录吗？')) {
            return;
        }
    }
    
    // 显示加载状态
    const saveBtn = document.querySelector('#memo-modal button[type="button"]');
    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.innerHTML = '保存中...';
    }
    
    try {
        let response;
        if (memoId) {
            // 更新备忘录
            response = await fetch(`/api/memos/${memoId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ title, content, tags, priority, category })
            });
        } else {
            // 创建新备忘录
            response = await fetch('/api/memos', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ title, content, tags, priority, category })
            });
        }
        
        if (!response.ok) {
            throw new Error(`API调用失败: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        if (data.success) {
            closeMemoModal();
            loadMemos();
            showNotification(memoId ? '备忘录更新成功' : '备忘录创建成功', 'success');
        } else {
            showNotification('保存失败: ' + (data.message || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('保存备忘录失败:', error);
        showNotification('保存失败，请检查网络连接后重试', 'error');
    } finally {
        // 恢复按钮状态
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '保存';
        }
    }
}

// 编辑备忘录
async function editMemo(memoId) {
    try {
        const response = await fetch(`/api/memos/${memoId}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        if (!response.ok) {
            throw new Error(`API调用失败: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        if (data.success) {
            const memo = data.memo;
            document.getElementById('memo-modal-title').textContent = '编辑备忘录';
            document.getElementById('memo-id').value = memo.id;
            document.getElementById('memo-title').value = memo.title;
            document.getElementById('memo-content').value = memo.content;
            document.getElementById('memo-tags').value = memo.tags.join(', ');
            document.getElementById('memo-priority').value = memo.priority;
            // 添加分类选择
            if (document.getElementById('memo-category')) {
                document.getElementById('memo-category').value = memo.category || 'personal';
            }
            document.getElementById('memo-modal').style.display = 'flex';
            
            // 初始化标签输入处理
            handleTagInput();
        } else {
            showNotification('获取备忘录失败: ' + (data.message || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('获取备忘录失败:', error);
        showNotification('获取备忘录失败，请检查网络连接后重试', 'error');
    }
}

// 删除备忘录
async function deleteMemo(memoId) {
    if (confirm('确定要删除这个备忘录吗？此操作无法撤销。')) {
        try {
            const response = await fetch(`/api/memos/${memoId}`, {
                method: 'DELETE',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`API调用失败: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            if (data.success) {
                loadMemos();
                showNotification('备忘录删除成功', 'success');
            } else {
                showNotification('删除失败: ' + (data.message || '未知错误'), 'error');
            }
        } catch (error) {
            console.error('删除备忘录失败:', error);
            showNotification('删除失败，请检查网络连接后重试', 'error');
        }
    }
}

// 搜索备忘录
async function searchMemos(query) {
    if (!query.trim()) {
        loadMemos();
        return;
    }
    
    try {
        const response = await fetch(`/api/memos/search?query=${encodeURIComponent(query)}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        if (!response.ok) {
            throw new Error('API调用失败');
        }
        
        const data = await response.json();
        if (data.success) {
            renderMemos(data.memos);
            if (data.memos.length === 0) {
                showNotification('未找到匹配的备忘录', 'info');
            }
        }
    } catch (error) {
        console.error('搜索备忘录失败:', error);
        showNotification('搜索失败，请重试', 'error');
    }
}

// 绑定侧边栏导航事件
function bindSidebarNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const contentSections = document.querySelectorAll('.content-section');
    const sectionTitle = document.getElementById('section-title');
    
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const section = item.getAttribute('data-section');
            
            // 保存当前会话ID到本地存储，无论切换到哪个视图
            if (currentSessionId) {
                localStorage.setItem(`currentSessionId_${windowId}`, currentSessionId);
                console.log('保存会话ID到本地存储:', currentSessionId);
            }
            
            // 更新导航项状态
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            // 更新内容区域
            contentSections.forEach(sec => sec.classList.remove('active'));
            document.getElementById(`${section}-section`).classList.add('active');
            
            // 更新标题
            if (sectionTitle) {
                const titles = {
                    'chat': '聊天',
                    'device': '设备控制',
                    'task': '定时任务',
                    'memory': '记忆管理',
                    'scheduler': '定时任务',
                    'distillation': '记忆蒸馏',
                    'memo': '备忘录',
                    'status': '系统状态'
                };
                sectionTitle.textContent = titles[section] || '聊天';
            }
            
            // 隐藏聊天初始化界面
            hideInitializationUI();
            
            // 加载对应模块的内容
            if (section === 'memory') {
                loadMemoryFiles();
            } else if (section === 'scheduler') {
                loadScheduleList();
            } else if (section === 'task') {
                loadScheduleList();
            } else if (section === 'chat') {
                // 尝试从本地存储恢复会话ID
                const savedSessionId = localStorage.getItem(`currentSessionId_${windowId}`);
                if (savedSessionId) {
                    currentSessionId = savedSessionId;
                    console.log('从本地存储恢复会话ID:', currentSessionId);
                }
                
                // 如果有当前会话，显示对应对话
                if (currentSessionId) {
                    // 不再自动重新加载对话历史，避免新消息被覆盖
                    // 只有在切换到不同对话时才需要重新加载
                    console.log('切换到聊天界面，保持当前对话内容');
                    // 确保聊天区域可见
                    if (chatArea) {
                        chatArea.style.display = 'block';
                    }
                    hideInitializationUI();
                } else {
                    // 没有会话时显示初始化界面
                    showInitializationUI();
                }
            } else if (section === 'memo') {
                loadMemos();
                // 绑定备忘录筛选和排序事件
                bindMemoFilters();
            }
        });
    });
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            func.apply(context, args);
        }, wait);
    };
}

// 搜索聊天历史
function searchChatHistory(query) {
    if (!query.trim()) {
        hideSearchResults();
        return;
    }
    
    const results = [];
    
    chatHistory.forEach((message, index) => {
        let content = '';
        let sender = '';
        
        if (message.user) {
            content = message.user;
            sender = '用户';
        } else if (message.assistant) {
            content = message.assistant;
            sender = '智能体';
        } else if (message.analysis) {
            content = message.analysis;
            sender = '分析';
        } else if (message.web_search) {
            content = message.web_search;
            sender = '搜索';
        } else if (message.mcp_tool) {
            content = message.mcp_tool;
            sender = '工具';
        }
        
        if (content.toLowerCase().includes(query.toLowerCase())) {
            results.push({
                index: index,
                content: content,
                sender: sender,
                message: message
            });
        }
    });
    
    displaySearchResults(results, query);
}

// 显示搜索结果
function displaySearchResults(results, query) {
    const searchResults = document.getElementById('search-results');
    if (!searchResults) return;
    
    searchResults.innerHTML = '';
    
    if (results.length === 0) {
        searchResults.innerHTML = '<div class="search-no-results">没有找到匹配的结果</div>';
        searchResults.classList.add('show');
        return;
    }
    
    results.forEach(result => {
        const resultItem = document.createElement('div');
        resultItem.className = 'search-result-item';
        resultItem.onclick = () => scrollToMessage(result.index);
        
        // 高亮显示关键字
        const highlightedContent = result.content.replace(new RegExp(`(${query})`, 'gi'), '<span class="search-result-highlight">$1</span>');
        
        resultItem.innerHTML = `
            <div class="search-result-header">
                <span class="search-result-sender">${result.sender}</span>
                <span class="search-result-time">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="search-result-content">${highlightedContent}</div>
        `;
        
        searchResults.appendChild(resultItem);
    });
    
    searchResults.classList.add('show');
}

// 隐藏搜索结果
function hideSearchResults() {
    const searchResults = document.getElementById('search-results');
    if (searchResults) {
        searchResults.classList.remove('show');
    }
}

// 滚动到指定消息
function scrollToMessage(index) {
    const messageElement = document.getElementById(`message-${index}`);
    if (messageElement) {
        // 移除之前的高亮
        document.querySelectorAll('.message.highlighted').forEach(msg => {
            msg.classList.remove('highlighted');
        });
        
        // 高亮当前消息
        messageElement.classList.add('highlighted');
        
        // 滚动到消息
        messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // 隐藏搜索结果
        hideSearchResults();
    }
}

// 绑定搜索事件
function bindSearchEvents() {
    const searchInput = document.getElementById('chat-search-input');
    const searchBtn = document.getElementById('chat-search-btn');
    
    if (searchInput) {
        // 实时搜索（带防抖）
        const debouncedSearch = debounce((e) => {
            searchChatHistory(e.target.value);
        }, 300);
        
        searchInput.addEventListener('input', debouncedSearch);
        
        // 点击搜索按钮
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                searchChatHistory(searchInput.value);
            });
        }
        
        // 点击其他地方隐藏搜索结果
        document.addEventListener('click', (e) => {
            const searchSection = document.querySelector('.search-section');
            if (searchSection && !searchSection.contains(e.target)) {
                hideSearchResults();
            }
        });
    }
}

// 显示记忆确认对话框
function showMemoryConfirmationDialog(info, confirmationId) {
    // 创建确认对话框
    const dialog = document.createElement('div');
    dialog.id = 'memory-confirm-dialog';
    dialog.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    `;
    
    const dialogContent = document.createElement('div');
    dialogContent.style.cssText = `
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        width: 400px;
        max-width: 90%;
    `;
    
    const dialogTitle = document.createElement('h3');
    dialogTitle.textContent = '记忆确认';
    dialogContent.appendChild(dialogTitle);
    
    const dialogMessage = document.createElement('p');
    dialogMessage.innerHTML = `系统识别到您提到了以下信息，是否需要保存到记忆中？<br><br><strong>${info.content}</strong>`;
    dialogContent.appendChild(dialogMessage);
    
    const dialogButtons = document.createElement('div');
    dialogButtons.style.cssText = `
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        margin-top: 20px;
    `;
    
    const confirmBtn = document.createElement('button');
    confirmBtn.textContent = '确认';
    confirmBtn.style.cssText = `
        padding: 8px 16px;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    `;
    confirmBtn.onclick = async function() {
        document.body.removeChild(dialog);
        // 确认保存
        await confirmMemoryInfo(confirmationId, 'confirmed');
    };
    
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = '取消';
    cancelBtn.style.cssText = `
        padding: 8px 16px;
        background-color: #f44336;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    `;
    cancelBtn.onclick = async function() {
        document.body.removeChild(dialog);
        // 拒绝保存
        await confirmMemoryInfo(confirmationId, 'rejected');
    };
    
    dialogButtons.appendChild(confirmBtn);
    dialogButtons.appendChild(cancelBtn);
    dialogContent.appendChild(dialogButtons);
    dialog.appendChild(dialogContent);
    document.body.appendChild(dialog);
}

// 确认记忆信息
async function confirmMemoryInfo(confirmationId, status) {
    try {
        const response = await fetch('/api/confirm-memory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                confirmation_id: confirmationId,
                status: status
            })
        });
        
        if (response.ok) {
            console.log('记忆确认成功');
        } else {
            console.error('记忆确认失败');
        }
    } catch (error) {
        console.error('记忆确认请求失败:', error);
    }
}

// 检查记忆确认
async function checkMemoryConfirmations() {
    try {
        const response = await fetch('/api/memory-confirmations', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.confirmations) {
                data.confirmations.forEach(confirmation => {
                    showMemoryConfirmationDialog(confirmation.info, confirmation.id);
                });
            }
        } else {
            console.error('获取记忆确认失败');
        }
    } catch (error) {
        console.error('获取记忆确认请求失败:', error);
    }
}

// 初始化应用 - 确保DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM加载完成，开始初始化应用');
    init();
    
    // 初始化设备管理
    initDeviceManagement();
    
    // 绑定侧边栏导航事件，在切换到设备页面时加载设备
    const deviceNavItem = document.querySelector('.nav-item[data-section="device"]');
    if (deviceNavItem) {
        deviceNavItem.addEventListener('click', () => {
            loadDevices();
        });
    }
    
    // 绑定滑块事件(防抖处理)
    const lampBrightnessSlider = document.getElementById('lamp-brightness-slider');
    if (lampBrightnessSlider) {
        let timeout;
        lampBrightnessSlider.addEventListener('change', () => {
            clearTimeout(timeout);
            timeout = setTimeout(setLampBrightness, 300);
        });
    }
    
    const acFanSlider = document.getElementById('ac-fan-slider');
    if (acFanSlider) {
        let timeout;
        acFanSlider.addEventListener('change', () => {
            clearTimeout(timeout);
            timeout = setTimeout(setACFanSpeed, 300);
        });
    }
    
    const curtainSlider = document.getElementById('curtain-position-slider');
    if (curtainSlider) {
        let timeout;
        curtainSlider.addEventListener('change', () => {
            clearTimeout(timeout);
            timeout = setTimeout(() => controlCurtain('set_position'), 300);
        });
    }
});

// 对话管理相关函数

// 加载对话列表
async function loadChats() {
    if (!chatList) return;
    
    try {
        const response = await fetch('/api/chats');
        if (!response.ok) {
            throw new Error('API调用失败');
        }
        
        const data = await response.json();
        if (data.success) {
            renderChatList(data.chats);
            
            // 如果没有对话，创建一个默认对话
            if (data.chats.length === 0) {
                createNewChat();
            } else if (!currentSessionId) {
                // 只有在当前没有会话时才切换到第一个对话
                switchChat(data.chats[0].session_id, data.chats[0].name);
            } else {
                // 如果有已保存的会话ID，检查该会话是否存在
                const savedChat = data.chats.find(chat => chat.session_id === currentSessionId);
                if (savedChat) {
                    // 如果已保存的会话存在，切换到该会话
                    switchChat(savedChat.session_id, savedChat.name);
                } else {
                    // 如果已保存的会话不存在，切换到第一个对话
                    switchChat(data.chats[0].session_id, data.chats[0].name);
                }
            }
        }
    } catch (error) {
        console.error('加载对话列表失败:', error);
    }
}

// 渲染对话列表
function renderChatList(chats) {
    if (!chatList) return;
    
    chatList.innerHTML = '';
    
    // 按创建时间降序排序，确保新对话显示在顶部
    chats.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    
    chats.forEach(chat => {
        const chatItem = document.createElement('div');
        chatItem.className = `chat-item ${currentSessionId === chat.session_id ? 'active' : ''}`;
        chatItem.dataset.sessionId = chat.session_id;
        
        // 格式化时间
        const timestamp = new Date(chat.updated_at);
        const timeString = timestamp.toLocaleTimeString('zh-CN', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        chatItem.innerHTML = `
            <div class="chat-item-content">
                <div class="chat-item-name">${chat.name}</div>
                <div class="chat-item-time">${timeString}</div>
            </div>
            <div class="chat-item-actions">
                <button class="chat-item-action-btn" onclick="renameChat('${chat.session_id}', '${chat.name}')">重命名</button>
                <button class="chat-item-action-btn" onclick="deleteChat('${chat.session_id}')">删除</button>
            </div>
        `;
        
        // 点击对话项切换对话
        chatItem.addEventListener('click', (e) => {
            // 避免点击按钮时触发切换
            if (!e.target.closest('.chat-item-action-btn')) {
                switchChat(chat.session_id, chat.name);
            }
        });
        
        chatList.appendChild(chatItem);
    });
}

// 创建新对话
function createNewChat() {
    console.log('createNewChat() 被调用');
    // 显示命名模态窗口
    if (nameModal) {
        nameModal.style.display = 'flex';
        // 聚焦到输入框
        if (chatNameInput) {
            chatNameInput.focus();
        }
    } else {
        console.error('nameModal 未找到');
    }
}

// 确认创建对话
async function confirmCreateChat() {
    const chatName = chatNameInput.value.trim() || '新对话';
    console.log('确认创建对话，名称:', chatName);
    
    try {
        console.log('开始创建新对话');
        const response = await fetch('/api/chats', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: chatName })
        });
        
        console.log('创建新对话响应:', response);
        if (!response.ok) {
            throw new Error('API调用失败');
        }
        
        const data = await response.json();
        console.log('创建新对话响应数据:', data);
        if (data.success) {
            // 获取新创建的对话信息
            const newChat = data.chat;
            console.log('新创建的对话:', newChat);
            
            // 重新加载对话列表
            console.log('创建新对话成功，开始加载对话列表');
            await loadChats();
            
            // 切换到新创建的对话
            if (newChat && newChat.session_id) {
                console.log('切换到新创建的对话，session_id:', newChat.session_id);
                await switchChat(newChat.session_id, newChat.name);
            }
        }
    } catch (error) {
        console.error('创建新对话失败:', error);
    } finally {
        // 关闭模态窗口
        closeModal();
    }
}

// 关闭模态窗口
function closeModal() {
    nameModal.style.display = 'none';
    // 清空输入框
    chatNameInput.value = '';
}

// 切换对话
async function switchChat(sessionId, chatName) {
    console.log('切换对话，sessionId:', sessionId, 'chatName:', chatName);
    // 确保sessionId有效
    if (!sessionId) {
        console.error('switchChat: sessionId无效');
        return;
    }
    
    // 如果点击的是当前活跃的对话，直接返回，避免重复加载
    if (currentSessionId === sessionId) {
        console.log('点击的是当前活跃的对话，无需重新加载');
        return;
    }
    
    // 设置currentSessionId
    currentSessionId = sessionId;
    console.log('currentSessionId已更新为:', currentSessionId);
    
    // 更新标题
    if (sectionTitle) {
        sectionTitle.textContent = chatName;
    }
    
    // 切换到聊天内容区域
    const contentSections = document.querySelectorAll('.content-section');
    contentSections.forEach(sec => sec.classList.remove('active'));
    document.getElementById('chat-section').classList.add('active');
    
    // 显示加载状态
    if (chatArea) {
        chatArea.innerHTML = '<div class="loading-message">加载对话中...</div>';
        chatArea.style.display = 'block';
        // 隐藏初始化界面
        hideInitializationUI();
    }
    
    // 加载对话历史
    try {
        await loadChatHistory(sessionId);
    } catch (error) {
        console.error('加载对话历史失败:', error);
        if (chatArea) {
            chatArea.innerHTML = '<div class="error-message">加载对话失败，请刷新页面重试</div>';
        }
    }
    
    // 直接更新对话列表的活跃状态，不重新加载整个对话列表
    if (chatList) {
        // 移除所有活跃状态
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
        });
        // 添加当前对话的活跃状态
        const activeItem = document.querySelector(`.chat-item[data-session-id="${sessionId}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        } else {
            console.warn('未找到对应sessionId的聊天项:', sessionId);
            // 如果未找到，重新加载对话列表
            loadChats();
        }
    }
    
    // 保存当前会话ID到本地存储，使用窗口唯一标识符作为键，确保页面刷新后仍能恢复
    localStorage.setItem(`currentSessionId_${windowId}`, sessionId);
}

// 加载对话历史
async function loadChatHistory(sessionId) {
    // 如果正在进行流式响应，不重新加载对话历史
    if (isStreaming) {
        console.log('正在进行流式响应，跳过对话历史加载');
        return;
    }
    
    console.log('loadChatHistory() 被调用，sessionId:', sessionId);
    if (!chatArea) {
        console.error('chatArea 未找到');
        return;
    }
    
    try {
        console.log('开始加载对话历史');
        
        const response = await fetch(`/api/chats/${sessionId}/history`);
        console.log('加载对话历史响应:', response);
        
        if (!response.ok) {
            throw new Error(`API调用失败: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('加载对话历史响应数据:', data);
        
        if (data.success) {
            console.log('对话历史长度:', data.history.length);
            
            // 清空聊天区域
            chatArea.innerHTML = '';
            
            // 检查对话历史是否为空
            if (data.history.length === 0) {
                console.log('对话历史为空');
                // 即使对话历史为空，也要保持当前会话ID
                localStorage.setItem(`currentSessionId_${windowId}`, sessionId);
                showInitializationUI();
                // 隐藏聊天区域
                if (chatArea) {
                    chatArea.style.display = 'none';
                }
                return;
            }
            
            // 显示聊天区域
            if (chatArea) {
                chatArea.style.display = 'block';
            }
            
            // 存储对话历史到全局变量
            chatHistory = data.history;
            
            // 显示对话历史
            data.history.forEach((message, index) => {
                if (message.user) {
                    addMessage('sent', message.user, `message-${index}`);
                } else if (message.assistant) {
                    addMessage('received', message.assistant, `message-${index}`);
                } else if (message.analysis) {
                    addMessage('analysis', message.analysis, `message-${index}`);
                } else if (message.web_search) {
                    addMessage('web_search', message.web_search, `message-${index}`);
                } else if (message.mcp_tool) {
                    addMessage('mcp_tool', message.mcp_tool, `message-${index}`);
                }
            });
            
            // 隐藏初始化界面
            hideInitializationUI();
            // 保存会话ID到本地存储
            localStorage.setItem(`currentSessionId_${windowId}`, sessionId);
        } else {
            console.error('加载对话历史失败:', data.message || '未知错误');
            chatArea.innerHTML = '<div class="error-message">' + (data.message || '加载对话历史失败') + '</div>';
        }
    } catch (error) {
        console.error('加载对话历史失败:', error);
        chatArea.innerHTML = '<div class="error-message">加载对话历史失败，请检查网络连接后重试</div>';
    }
}

// 重命名对话
function renameChat(sessionId, currentName) {
    const newName = prompt('请输入新的对话名称:', currentName);
    if (newName && newName.trim() !== currentName) {
        updateChatName(sessionId, newName.trim());
    }
}

// 重命名当前对话
function renameCurrentChat() {
    if (currentSessionId) {
        const currentName = sectionTitle.textContent;
        renameChat(currentSessionId, currentName);
    }
}

// 更新对话名称
async function updateChatName(sessionId, newName) {
    console.log('updateChatName() 被调用，sessionId:', sessionId, 'newName:', newName);
    try {
        console.log('开始更新对话名称');
        const response = await fetch(`/api/chats/${sessionId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: newName })
        });
        
        console.log('更新对话名称响应:', response);
        if (!response.ok) {
            throw new Error('API调用失败');
        }
        
        const data = await response.json();
        console.log('更新对话名称响应数据:', data);
        if (data.success) {
            // 重新加载对话列表
            console.log('更新对话名称成功，开始加载对话列表');
            loadChats();
            
            // 如果是当前对话，更新标题
            if (sessionId === currentSessionId && sectionTitle) {
                console.log('更新当前对话标题:', newName);
                sectionTitle.textContent = newName;
            }
        }
    } catch (error) {
        console.error('更新对话名称失败:', error);
    }
}

// 删除对话
function deleteChat(sessionId) {
    if (confirm('确定要删除这个对话吗？')) {
        deleteChatById(sessionId);
    }
}

// 删除当前对话
function deleteCurrentChat() {
    if (currentSessionId) {
        deleteChat(currentSessionId);
    }
}

// 根据ID删除对话
async function deleteChatById(sessionId) {
    try {
        const response = await fetch(`/api/chats/${sessionId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('API调用失败');
        }
        
        const data = await response.json();
        if (data.success) {
            // 重新加载对话列表
            loadChats();
        }
    } catch (error) {
        console.error('删除对话失败:', error);
    }
}



// 发送问题
function sendQuestion(question) {
    messageInput.value = question;
    sendMessage();
    // 隐藏初始化界面
    hideInitializationUI();
}

// 显示初始化界面
function showInitializationUI() {
    const initializationUI = document.getElementById('chat-initialization');
    if (initializationUI) {
        initializationUI.style.display = 'flex';
    }
    // 隐藏聊天区域
    if (chatArea) {
        chatArea.style.display = 'none';
    }
}

// 隐藏初始化界面
function hideInitializationUI() {
    const initializationUI = document.getElementById('chat-initialization');
    if (initializationUI) {
        initializationUI.style.display = 'none';
    }
    // 显示聊天区域
    if (chatArea) {
        chatArea.style.display = 'block';
    }
}

// 检查是否是备忘录触发指令
function isMemoTriggerCommand(message) {
    const triggerPhrases = [
        '帮我记录',
        '我要记录',
        '记录一下',
        '写个备忘录',
        '创建备忘录',
        '添加备忘录',
        '记下来',
        '备忘录',
        '查看备忘录',
        '列出备忘录',
        '搜索备忘录',
        '删除备忘录',
        '修改备忘录',
        '更新备忘录'
    ];
    
    return triggerPhrases.some(phrase => message.includes(phrase));
}

// 处理备忘录触发
async function handleMemoTrigger(message) {
    // 检查是否是查看备忘录指令
    if (message.includes('查看备忘录') || message.includes('列出备忘录')) {
        // 切换到备忘录页面
        const memoNavItem = document.querySelector('.nav-item[data-section="memo"]');
        if (memoNavItem) {
            memoNavItem.click();
        }
        return;
    }
    
    // 检查是否是搜索备忘录指令
    if (message.includes('搜索备忘录')) {
        // 提取搜索关键词
        const searchQuery = message.replace('搜索备忘录', '').trim();
        if (searchQuery) {
            // 切换到备忘录页面并执行搜索
            const memoNavItem = document.querySelector('.nav-item[data-section="memo"]');
            if (memoNavItem) {
                memoNavItem.click();
                // 等待页面加载后执行搜索
                setTimeout(() => {
                    const searchInput = document.getElementById('memo-search-input');
                    if (searchInput) {
                        searchInput.value = searchQuery;
                        searchMemos(searchQuery);
                    }
                }, 500);
            }
        }
        return;
    }
    
    // 提取可能的备忘录内容（去掉触发词）
    let content = message;
    const triggerPhrases = [
        '帮我记录',
        '我要记录',
        '记录一下',
        '写个备忘录',
        '创建备忘录',
        '添加备忘录',
        '记下来',
        '备忘录'
    ];
    
    triggerPhrases.forEach(phrase => {
        content = content.replace(phrase, '').trim();
    });
    
    // 显示创建备忘录模态窗口
    showCreateMemoModal();
    
    // 如果有内容，自动填充
    if (content) {
        // 尝试提取标题和内容
        const parts = content.split('，');
        if (parts.length >= 2) {
            document.getElementById('memo-title').value = parts[0];
            document.getElementById('memo-content').value = parts.slice(1).join('，');
        } else {
            document.getElementById('memo-title').value = content;
        }
    }
    
    // 聚焦到标题输入框
    document.getElementById('memo-title').focus();
}

// 处理备忘录相关话题的识别和响应
function handleMemoRelatedTopic(message) {
    const memoRelatedPhrases = [
        '忘记',
        '记得',
        '提醒',
        '事项',
        '计划',
        '安排',
        '任务',
        '备忘'
    ];
    
    return memoRelatedPhrases.some(phrase => message.includes(phrase));
}

// 生成备忘录相关的响应
function generateMemoResponse(message) {
    if (message.includes('忘记')) {
        return '我可以帮你创建备忘录来记住重要的事情。你想记录什么内容？';
    } else if (message.includes('记得')) {
        return '好的，我会帮你记住这件事。你想创建一个备忘录吗？';
    } else if (message.includes('提醒')) {
        return '我可以帮你创建备忘录来提醒你。你想提醒什么事情？';
    } else if (message.includes('事项') || message.includes('计划') || message.includes('安排')) {
        return '你可以创建备忘录来记录你的计划和安排。需要我帮你创建一个吗？';
    } else if (message.includes('任务')) {
        return '你可以使用备忘录来管理你的任务。需要我帮你创建一个任务备忘录吗？';
    } else if (message.includes('备忘')) {
        return '是的，我可以帮你创建和管理备忘录。你想记录什么内容？';
    }
    return null;
}

// 更新发送消息函数
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    // 生成消息唯一标识符（基于消息内容和时间戳）
    const messageId = message + '_' + Date.now();
    
    // 检查消息是否正在处理中
    if (processingMessages.has(messageId)) {
        console.log('消息正在处理中，避免重复发送:', message);
        return;
    }
    
    // 添加到处理集合中
    processingMessages.add(messageId);
    
    try {
        // 隐藏初始化界面
        hideInitializationUI();
        
        // 检查是否是备忘录触发指令
        if (isMemoTriggerCommand(message)) {
            // 处理备忘录触发
            handleMemoTrigger(message);
            // 清空输入框
            messageInput.value = '';
            return;
        }
        
        // 检查是否是备忘录相关话题
        if (handleMemoRelatedTopic(message)) {
            // 生成备忘录相关的响应
            const response = generateMemoResponse(message);
            if (response) {
                // 添加用户消息
                addMessage('sent', message);
                messageInput.value = '';
                
                // 添加系统响应
                addMessage('received', response);
                return;
            }
        }
        
        // 添加用户消息
        addMessage('sent', message);
        messageInput.value = '';
        
        // 调用后端API
        await sendMessageWithRetry(message, 3, messageId); // 最多重试3次
        
        // 检查是否有需要确认的记忆信息
        checkMemoryConfirmations();
    } finally {
        // 处理完成后从集合中移除
        processingMessages.delete(messageId);
    }
}

// 带重试机制的消息发送函数
async function sendMessageWithRetry(message, maxRetries, messageId) {
    let retries = 0;
    const thinkingMessageId = 'thinking-' + Date.now();
    let answerMessageId = null;
    let answerContent = ''; // 累积答案内容
    
    while (retries < maxRetries) {
        // 重置流式响应状态
        isStreaming = true;
        
        try {
            // 第一次尝试时添加思考过程消息
            if (retries === 0) {
                addMessage('thinking', '正在思考...', thinkingMessageId);
            } else {
                // 重试时更新思考过程消息
                updateThinkingMessage(thinkingMessageId, `网络连接不稳定，正在重试... ${retries+1}/${maxRetries}`);
            }
            
            // 使用fetch API发送请求
            console.log('发送API请求:', {
                message: message,
                user_id: 'default_user',
                session_id: currentSessionId,
                stream: true,
                message_id: messageId
            });
            
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    message: message, 
                    user_id: 'default_user',
                    session_id: currentSessionId,
                    stream: true,
                    message_id: messageId // 添加消息唯一标识符
                })
            });
            
            console.log('API响应状态:', response.status);
            
            if (!response.ok) {
                // 处理HTTP错误
                const errorMessage = `服务器错误: ${response.status} ${response.statusText}`;
                throw new Error(errorMessage);
            }
            
            // 处理流式响应
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let receivedData = false;
            let hasError = false;
            
            console.log('开始处理流式响应');
            
            while (true) {
                try {
                    const { done, value } = await reader.read();
                    if (done) {
                        isStreaming = false; // 流式响应结束
                        break;
                    }
                    
                    receivedData = true;
                    buffer += decoder.decode(value, { stream: true });
                    console.log('收到数据:', buffer.length, '字节');
                    
                    // 处理SSE格式的数据
                    const lines = buffer.split('\n');
                    buffer = lines.pop(); // 保留不完整的最后一行
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                                const dataStr = line.substring(6);
                                if (dataStr) {
                                    try {
                                        console.log('解析数据:', dataStr);
                                        // 尝试解析JSON数据
                                        let data;
                                        try {
                                            data = JSON.parse(dataStr);
                                        } catch (parseError) {
                                            console.warn('JSON解析失败，尝试处理非JSON数据:', parseError);
                                            // 跳过非JSON数据，继续处理下一行
                                            continue;
                                        }
                                        
                                        // 检查是否是错误响应格式
                                        if (data.success === false && data.error) {
                                            // 移除思考过程消息
                                            removeThinkingMessage(thinkingMessageId);
                                            // 添加错误消息
                                            addMessage('received', data.error);
                                            // 标记为已收到数据
                                            receivedData = true;
                                            hasError = true;
                                            isStreaming = false; // 流式响应结束
                                            console.log('收到错误消息:', data.error);
                                        } 
                                        // 更新思考过程或累积答案内容
                                        else if (data.type === 'session_id') {
                                            // 保存会话ID
                                            currentSessionId = data.content;
                                            console.log('获取到新的会话ID:', currentSessionId);
                                            // 保存到本地存储
                                            localStorage.setItem(`currentSessionId_${windowId}`, currentSessionId);
                                        } else if (data.type === 'thinking') {
                                            updateThinkingMessage(thinkingMessageId, data.content);
                                        } else if (data.type === 'analysis') {
                                            // 显示思考分析过程
                                            removeThinkingMessage(thinkingMessageId);
                                            addMessage('analysis', data.content);
                                            // 重新创建思考过程消息，以便后续使用
                                            thinkingMessageId = 'thinking-' + Date.now();
                                            addMessage('thinking', '正在继续处理...', thinkingMessageId);
                                        } else if (data.type === 'web_search') {
                                            // 显示联网搜索过程
                                            removeThinkingMessage(thinkingMessageId);
                                            addMessage('web_search', data.content);
                                            // 重新创建思考过程消息，以便后续使用
                                            thinkingMessageId = 'thinking-' + Date.now();
                                            addMessage('thinking', '正在继续处理...', thinkingMessageId);
                                        } else if (data.type === 'mcp_tool') {
                                            // 显示MCP工具调用过程
                                            removeThinkingMessage(thinkingMessageId);
                                            addMessage('mcp_tool', data.content);
                                            // 重新创建思考过程消息，以便后续使用
                                            thinkingMessageId = 'thinking-' + Date.now();
                                            addMessage('thinking', '正在继续处理...', thinkingMessageId);
                                        } else if (data.type === 'searching') {
                                            // 移除思考过程消息并显示搜索状态提示
                                            removeThinkingMessage(thinkingMessageId);
                                            thinkingMessageId = 'searching-' + Date.now();
                                            const searchMessage = addMessage('searching', data.content, thinkingMessageId);
                                            // 添加搜索进度指示
                                            let dots = 0;
                                            const progressInterval = setInterval(() => {
                                                dots = (dots + 1) % 4;
                                                const newContent = data.content.replace(/\.{3}$/, '') + '.'.repeat(dots);
                                                const bubble = searchMessage.querySelector('.bubble');
                                                if (bubble) {
                                                    bubble.textContent = newContent;
                                                }
                                            }, 500);
                                            // 保存进度指示的定时器ID，以便在搜索完成后清除
                                            window.searchProgressInterval = progressInterval;
                                        } else if (data.type === 'answer') {
                                            // 清除搜索进度指示的定时器
                                            if (window.searchProgressInterval) {
                                                clearInterval(window.searchProgressInterval);
                                                window.searchProgressInterval = null;
                                            }
                                            // 累积答案内容
                                            answerContent += data.content;
                                            console.log('收到答案内容:', answerContent);
                                            
                                            // 实时更新UI
                                            if (!answerMessageId) {
                                                // 第一次收到答案内容，移除搜索状态提示并创建答案消息
                                                removeThinkingMessage(thinkingMessageId);
                                                answerMessageId = 'answer-' + Date.now();
                                                addMessage('received', answerContent, answerMessageId);
                                            } else {
                                                // 更新现有答案消息
                                                updateAnswerMessage(answerMessageId, answerContent);
                                            }
                                        } else if (data.type === 'error') {
                                            // 清除搜索进度指示的定时器
                                            if (window.searchProgressInterval) {
                                                clearInterval(window.searchProgressInterval);
                                                window.searchProgressInterval = null;
                                            }
                                            // 移除搜索状态提示
                                            removeThinkingMessage(thinkingMessageId);
                                            // 添加错误消息
                                            addMessage('received', data.content);
                                            // 标记为已收到数据
                                            receivedData = true;
                                            hasError = true;
                                            isStreaming = false; // 流式响应结束
                                            console.log('收到错误消息:', data.content);
                                        } else if (data.type === 'stream_end') {
                                            // 清除搜索进度指示的定时器
                                            if (window.searchProgressInterval) {
                                                clearInterval(window.searchProgressInterval);
                                                window.searchProgressInterval = null;
                                            }
                                            // 流式响应结束，不做特殊处理
                                            isStreaming = false; // 流式响应结束
                                            console.log('流式响应结束');
                                        } else {
                                            // 处理其他类型的数据
                                            console.log('收到其他类型的数据:', data);
                                        }
                                    } catch (e) {
                                        console.error('处理SSE数据时发生错误:', e);
                                        // 只记录错误，不显示错误消息
                                        // 继续处理下一行数据
                                        continue;
                                    }
                                }
                            }
                    }
                } catch (e) {
                    console.error('处理流式数据失败:', e);
                    // 只记录错误，不显示错误消息
                    // 继续处理，允许其他数据正常接收
                    isStreaming = false; // 流式响应结束
                }
            }
            
            // 流式响应结束后，确保答案已显示
            if (answerContent && !hasError && answerMessageId) {
                // 答案已经通过实时更新显示，这里不需要再做什么
                console.log('流式响应处理完成，答案已实时显示');
            } else if (!answerContent && !hasError) {
                // 如果没有收到答案内容且没有错误，显示默认回答
                removeThinkingMessage(thinkingMessageId);
                addMessage('received', '你好！我是悦悦，有什么可以帮到你的吗？');
                console.log('没有收到答案内容，显示默认回答');
            } else if (hasError) {
                // 如果有错误，显示错误消息
                console.log('流式响应处理完成，有错误');
            }
            
            // 如果没有收到任何数据，视为失败
            if (!receivedData) {
                removeThinkingMessage(thinkingMessageId);
                addMessage('received', '抱歉，服务器无响应，请稍后重试');
                console.log('没有收到任何数据');
                return;
            }
            
            console.log('流式响应处理完成');
            console.log('Answer content:', answerContent);
            console.log('Has error:', hasError);
            console.log('Received data:', receivedData);
            console.log('Is streaming:', isStreaming);
            
            // 更新当前会话ID（如果是新创建的对话）
            // 注意：由于使用了流式响应，会话ID需要从流式数据中获取
            // 这里我们假设后端在流式响应中返回了会话ID
            // 如果currentSessionId为空，说明是新创建的对话，需要重新加载对话列表
            if (!currentSessionId) {
                console.log('新创建的对话，重新加载对话列表');
                await loadChats();
            }
            
            // 不再自动重新加载对话历史，避免对话消失
            // 对话历史已经通过实时更新显示，不需要重新加载
            console.log('对话处理完成，答案已实时显示');
            // 只有在用户手动刷新或切换对话时才重新加载对话历史
            
            return;
        } catch (error) {
            console.error('发送消息失败:', error);
            
            // 只有网络错误才进行重试
            const isNetworkError = error.message.includes('网络') || error.message.includes('Network') || error.message.includes('fetch');
            if (!isNetworkError) {
                // 非网络错误，直接显示错误消息，不重试
                removeThinkingMessage(thinkingMessageId);
                addMessage('received', `抱歉，${error.message}，请稍后重试。`);
                isStreaming = false; // 流式响应结束
                return;
            }
            
            retries++;
            isStreaming = false; // 流式响应结束
            
            // 如果达到最大重试次数，显示错误消息
            if (retries >= maxRetries) {
                removeThinkingMessage(thinkingMessageId);
                addMessage('received', `抱歉，${error.message}，请检查网络后再试试。`);
                return;
            }
            
            // 等待一段时间后重试
            await new Promise(resolve => setTimeout(resolve, 1000 * retries));
        }
    }
}

// 检查是否正在进行流式响应
function isStreamingResponse() {
    return isStreaming;
}

// 更新答案消息
function updateAnswerMessage(id, content) {
    const messageDiv = document.getElementById(id);
    if (messageDiv) {
        const bubble = messageDiv.querySelector('.bubble');
        if (bubble) {
            // 处理特殊格式，确保格式的完整性
            const formattedContent = formatContent(content);
            bubble.innerHTML = formattedContent;
            chatArea.scrollTop = chatArea.scrollHeight;
        }
    }
}

// 格式化内容，确保特殊格式正确显示
function formatContent(content) {
    if (!content) return '';
    
    // 处理换行符，确保它们在HTML中正确显示
    let formatted = content.replace(/\n/g, '<br>');
    
    // 处理代码块
    formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    
    // 处理粗体
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // 处理斜体
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // 处理列表
    formatted = formatted.replace(/^\s*\-\s(.*?)$/gm, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*?<\/li>)/s, '<ul>$1</ul>');
    
    return formatted;
}

// 添加消息到聊天区域
function addMessage(type, content, id = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    if (id) {
        messageDiv.id = id;
    }
    
    if (type === 'received') {
        messageDiv.innerHTML = `
            <div class="avatar">🌟</div>
            <div class="bubble">${content}</div>
        `;
    } else if (type === 'thinking') {
        messageDiv.innerHTML = `
            <div class="avatar">🤔</div>
            <div class="bubble thinking">${content}</div>
        `;
    } else if (type === 'searching') {
        messageDiv.innerHTML = `
            <div class="avatar">🔍</div>
            <div class="bubble searching">${content}</div>
        `;
    } else if (type === 'analysis') {
        messageDiv.innerHTML = `
            <div class="avatar">🧠</div>
            <div class="bubble analysis">
                <div class="process-header">思考分析过程</div>
                <div class="process-content">${content}</div>
            </div>
        `;
    } else if (type === 'web_search') {
        messageDiv.innerHTML = `
            <div class="avatar">🌐</div>
            <div class="bubble web-search">
                <div class="process-header">联网搜索过程</div>
                <div class="process-content">${content}</div>
            </div>
        `;
    } else if (type === 'mcp_tool') {
        messageDiv.innerHTML = `
            <div class="avatar">🛠️</div>
            <div class="bubble mcp-tool">
                <div class="process-header">MCP工具调用过程</div>
                <div class="process-content">${content}</div>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="bubble">${content}</div>
        `;
    }
    
    chatArea.appendChild(messageDiv);
    chatArea.scrollTop = chatArea.scrollHeight;
    return messageDiv;
}

// 更新思考过程消息
function updateThinkingMessage(id, content) {
    const messageDiv = document.getElementById(id);
    if (messageDiv) {
        const bubble = messageDiv.querySelector('.bubble');
        if (bubble) {
            bubble.textContent = content;
            chatArea.scrollTop = chatArea.scrollHeight;
        }
    }
}

// 移除思考过程消息
function removeThinkingMessage(id) {
    const messageDiv = document.getElementById(id);
    if (messageDiv) {
        messageDiv.remove();
    }
}

// ==================== 设备管理功能 ====================

/**
 * 设备管理模块
 * 
 * 执行流程:
 * 1. 页面加载 -> 初始化设备管理 -> 加载设备列表
 * 2. 设备操作 -> 调用API -> 更新UI -> 显示反馈
 * 3. 状态轮询 -> 每5秒获取状态 -> 更新设备状态显示
 */

// 设备管理全局变量
let devicesData = [];           // 设备数据缓存
let currentDeviceId = null;     // 当前操作的设备ID
let deviceStatusInterval = null; // 状态轮询定时器
let deviceStatusWebSocket = null; // WebSocket连接
let isWebSocketConnected = false; // WebSocket连接状态

// 设备类型配置
const DEVICE_TYPES = {
    lamp: { label: '台灯', icon: '💡', color: '#FFB347' },
    air_conditioner: { label: '空调', icon: '❄️', color: '#64B5F6' },
    curtain: { label: '窗帘', icon: '🪟', color: '#81C784' }
};

// 设备类型描述
const DEVICE_TYPE_DESCRIPTIONS = {
    lamp: '智能台灯，支持亮度调节(0-100%)、色温切换(正常/护眼)、定时关机',
    air_conditioner: '智能空调，支持温度调节(16-30°C)、模式切换(制冷/制热)、风速调节(1-5档)',
    curtain: '智能窗帘，支持位置调节(0-100%)、全开/全关/停止控制'
};

/**
 * 初始化设备管理
 * 在页面加载时调用
 */
function initDeviceManagement() {
    // 加载设备列表
    loadDevices();
    
    // 尝试连接WebSocket，失败则使用轮询
    connectDeviceStatusWebSocket();
}

/**
 * 连接设备状态WebSocket
 * 如果WebSocket连接失败，自动回退到轮询
 */
function connectDeviceStatusWebSocket() {
    try {
        // 检查浏览器是否支持WebSocket
        if (!window.WebSocket) {
            console.log('浏览器不支持WebSocket，使用轮询');
            startDeviceStatusPolling();
            return;
        }
        
        // 创建WebSocket连接
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/api/devices/status/stream`;
        
        deviceStatusWebSocket = new WebSocket(wsUrl);
        
        deviceStatusWebSocket.onopen = function() {
            console.log('设备状态WebSocket已连接');
            isWebSocketConnected = true;
            
            // 停止轮询，使用WebSocket
            if (deviceStatusInterval) {
                clearInterval(deviceStatusInterval);
                deviceStatusInterval = null;
            }
            
            // 发送认证消息（如果需要）
            // deviceStatusWebSocket.send(JSON.stringify({ type: 'auth', token: getAuthToken() }));
        };
        
        deviceStatusWebSocket.onmessage = function(event) {
            try {
                const message = JSON.parse(event.data);
                handleWebSocketMessage(message);
            } catch (error) {
                console.error('解析WebSocket消息失败:', error);
            }
        };
        
        deviceStatusWebSocket.onerror = function(error) {
            console.error('WebSocket错误:', error);
            isWebSocketConnected = false;
        };
        
        deviceStatusWebSocket.onclose = function() {
            console.log('设备状态WebSocket已断开');
            isWebSocketConnected = false;
            
            // 如果WebSocket断开，启动轮询作为后备
            if (!deviceStatusInterval) {
                startDeviceStatusPolling();
            }
            
            // 尝试重新连接（指数退避）
            setTimeout(() => {
                if (!isWebSocketConnected) {
                    connectDeviceStatusWebSocket();
                }
            }, 5000);
        };
        
    } catch (error) {
        console.error('连接WebSocket失败:', error);
        startDeviceStatusPolling();
    }
}

/**
 * 处理WebSocket消息
 * @param {Object} message - WebSocket消息
 */
function handleWebSocketMessage(message) {
    switch (message.type) {
        case 'status_update':
            // 更新单个设备状态
            updateDeviceStatus(message.device_id, message.status);
            break;
        case 'status_batch':
            // 批量更新设备状态
            updateDeviceStatuses(message.devices);
            break;
        case 'device_online':
            // 设备上线
            showToast(`设备 ${message.device_name} 已上线`, 'success');
            refreshDeviceStatus();
            break;
        case 'device_offline':
            // 设备离线
            showToast(`设备 ${message.device_name} 已离线`, 'warning');
            refreshDeviceStatus();
            break;
        case 'error':
            console.error('WebSocket错误消息:', message.error);
            break;
        default:
            console.log('未知WebSocket消息类型:', message.type);
    }
}

/**
 * 更新单个设备状态（不重新渲染整个列表）
 * @param {string} deviceId - 设备ID
 * @param {Object} status - 设备状态
 */
function updateDeviceStatus(deviceId, status) {
    // 更新数据
    const deviceIndex = devicesData.findIndex(d => d.device_id === deviceId);
    if (deviceIndex !== -1) {
        devicesData[deviceIndex] = { ...devicesData[deviceIndex], ...status };
        
        // 更新UI
        const deviceCard = document.querySelector(`.device-card[data-device-id="${deviceId}"]`);
        if (deviceCard) {
            // 更新状态徽章
            const newStatus = getDeviceStatus(devicesData[deviceIndex]);
            const statusConfig = getStatusConfig(newStatus);
            
            const statusBadge = deviceCard.querySelector('.device-status-badge');
            if (statusBadge) {
                statusBadge.className = `device-status-badge ${newStatus}`;
                statusBadge.innerHTML = `
                    <span class="status-indicator" style="background-color: ${statusConfig.color}"></span>
                    ${statusConfig.label}
                `;
            }
            
            // 更新卡片样式
            deviceCard.className = `device-card status-${newStatus}`;
            
            // 更新状态详情
            const statusDetails = deviceCard.querySelector('.device-status-details');
            if (statusDetails) {
                const details = getDeviceStatusDetails(devicesData[deviceIndex]);
                statusDetails.innerHTML = details.map(detail => `
                    <div class="status-detail-item">
                        <span class="detail-label">${detail.label}:</span>
                        <span class="detail-value">${detail.value}</span>
                    </div>
                `).join('');
            }
            
            // 更新最后 seen 时间
            const lastSeen = deviceCard.querySelector('.last-seen');
            if (lastSeen && status.last_updated) {
                lastSeen.textContent = formatLastSeen(status.last_updated);
            }
        }
    }
}

/**
 * 批量更新设备状态
 * @param {Array} devices - 设备列表
 */
function updateDeviceStatuses(devices) {
    devices.forEach(device => {
        updateDeviceStatus(device.device_id, device);
    });
}

/**
 * 加载设备列表
 * 
 * 执行流程:
 * 1. 调用API获取设备列表
 * 2. 更新设备数据缓存
 * 3. 渲染设备列表
 * 4. 处理错误情况
 */
async function loadDevices() {
    try {
        const response = await fetch('/api/devices');
        const data = await response.json();
        
        if (data.success) {
            devicesData = data.devices || [];
            renderDeviceList();
        } else {
            showToast(data.message || '加载设备列表失败', 'error');
        }
    } catch (error) {
        console.error('加载设备列表失败:', error);
        showToast('加载设备列表失败，请检查网络连接', 'error');
    }
}

/**
 * 渲染设备列表
 * 
 * 执行流程:
 * 1. 清空现有列表
 * 2. 检查是否有设备
 * 3. 遍历设备数据创建卡片
 * 4. 绑定事件处理
 */
function renderDeviceList() {
    const deviceList = document.getElementById('device-list');
    const emptyState = document.getElementById('device-empty-state');
    
    if (!deviceList) return;
    
    // 更新仪表板统计
    updateDeviceDashboard();
    
    // 获取过滤和排序后的设备列表
    const filteredDevices = getFilteredAndSortedDevices();
    
    // 清空列表
    deviceList.innerHTML = '';
    
    // 检查是否有设备
    if (filteredDevices.length === 0) {
        deviceList.style.display = 'none';
        if (emptyState) {
            emptyState.style.display = 'flex';
            const emptyText = emptyState.querySelector('.empty-text');
            if (emptyText) {
                emptyText.textContent = devicesData.length === 0 ? '暂无设备' : '没有符合条件的设备';
            }
        }
        return;
    }
    
    deviceList.style.display = 'grid';
    if (emptyState) emptyState.style.display = 'none';
    
    // 渲染每个设备
    filteredDevices.forEach(device => {
        const deviceCard = createDeviceCard(device);
        deviceList.appendChild(deviceCard);
    });
}

/**
 * 更新设备状态仪表板
 */
function updateDeviceDashboard() {
    const totalEl = document.getElementById('stat-total');
    const onlineEl = document.getElementById('stat-online');
    const idleEl = document.getElementById('stat-idle');
    const offlineEl = document.getElementById('stat-offline');
    const connectionStatus = document.getElementById('connection-status');
    
    if (!totalEl) return;
    
    // 计算统计数据
    const total = devicesData.length;
    const online = devicesData.filter(d => getDeviceStatus(d) === 'online').length;
    const idle = devicesData.filter(d => getDeviceStatus(d) === 'idle').length;
    const offline = devicesData.filter(d => getDeviceStatus(d) === 'offline').length;
    
    // 更新显示
    totalEl.textContent = total;
    onlineEl.textContent = online;
    idleEl.textContent = idle;
    offlineEl.textContent = offline;
    
    // 更新连接状态
    if (connectionStatus) {
        if (isWebSocketConnected) {
            connectionStatus.className = 'connection-status connected';
            connectionStatus.querySelector('.status-text').textContent = '实时连接';
        } else if (deviceStatusInterval) {
            connectionStatus.className = 'connection-status';
            connectionStatus.querySelector('.status-text').textContent = '轮询模式';
        } else {
            connectionStatus.className = 'connection-status disconnected';
            connectionStatus.querySelector('.status-text').textContent = '已断开';
        }
    }
}

/**
 * 获取过滤和排序后的设备列表
 * @returns {Array} 过滤和排序后的设备列表
 */
function getFilteredAndSortedDevices() {
    let result = [...devicesData];
    
    // 应用状态过滤
    const statusFilter = document.getElementById('filter-status');
    if (statusFilter && statusFilter.value !== 'all') {
        result = result.filter(device => getDeviceStatus(device) === statusFilter.value);
    }
    
    // 应用类型过滤
    const typeFilter = document.getElementById('filter-type');
    if (typeFilter && typeFilter.value !== 'all') {
        result = result.filter(device => device.device_type === typeFilter.value);
    }
    
    // 应用排序
    const sortBy = document.getElementById('sort-by');
    if (sortBy) {
        switch (sortBy.value) {
            case 'name-asc':
                result.sort((a, b) => a.device_name.localeCompare(b.device_name, 'zh-CN'));
                break;
            case 'name-desc':
                result.sort((a, b) => b.device_name.localeCompare(a.device_name, 'zh-CN'));
                break;
            case 'status':
                const statusOrder = { online: 0, idle: 1, offline: 2, error: 3 };
                result.sort((a, b) => statusOrder[getDeviceStatus(a)] - statusOrder[getDeviceStatus(b)]);
                break;
            case 'type':
                result.sort((a, b) => a.device_type.localeCompare(b.device_type));
                break;
            case 'last-updated':
                result.sort((a, b) => new Date(b.last_updated || 0) - new Date(a.last_updated || 0));
                break;
        }
    }
    
    return result;
}

/**
 * 应用设备过滤和排序
 */
function applyDeviceFilters() {
    renderDeviceList();
}

/**
 * 创建设备卡片
 * 
 * @param {Object} device - 设备数据
 * @returns {HTMLElement} 设备卡片元素
 */
function createDeviceCard(device) {
    const typeConfig = DEVICE_TYPES[device.device_type] || { label: '未知', icon: '❓', color: '#999' };
    const state = device.current_state || {};
    
    // Determine device status with more granularity
    const status = getDeviceStatus(device);
    const statusConfig = getStatusConfig(status);
    
    const card = document.createElement('div');
    card.className = `device-card status-${status}`;
    card.dataset.deviceId = device.device_id;
    card.dataset.deviceType = device.device_type;
    card.dataset.deviceStatus = status;
    
    // Get detailed status information based on device type
    const statusDetails = getDeviceStatusDetails(device);
    
    // Format last seen time
    const lastSeen = device.last_updated ? formatLastSeen(device.last_updated) : '未知';
    
    card.innerHTML = `
        <div class="device-card-header">
            <div class="device-icon" style="background-color: ${typeConfig.color}20; color: ${typeConfig.color}">
                ${typeConfig.icon}
            </div>
            <div class="device-info">
                <div class="device-name">${escapeHtml(device.device_name)}</div>
                <div class="device-type">${typeConfig.label}</div>
            </div>
            <div class="device-status-container">
                <div class="device-status-badge ${status}" title="${statusConfig.description}">
                    <span class="status-indicator" style="background-color: ${statusConfig.color}"></span>
                    ${statusConfig.label}
                </div>
                <div class="last-seen">${lastSeen}</div>
            </div>
        </div>
        <div class="device-card-body">
            <div class="device-status-details">
                ${statusDetails.map(detail => `
                    <div class="status-detail-item">
                        <span class="detail-label">${detail.label}:</span>
                        <span class="detail-value">${detail.value}</span>
                    </div>
                `).join('')}
            </div>
        </div>
        <div class="device-card-footer">
            <button class="device-action-btn control-btn" onclick="openDeviceControlModal('${device.device_id}')">
                <span>⚙️</span> 控制
            </button>
            <button class="device-action-btn edit-btn" onclick="showEditDeviceModal('${device.device_id}')">
                <span>✏️</span> 编辑
            </button>
            <button class="device-action-btn delete-btn" onclick="confirmDeleteDevice('${device.device_id}')">
                <span>🗑️</span> 删除
            </button>
        </div>
    `
    
    return card;
}

/**
 * Get device status with enhanced granularity
 * @param {Object} device - Device data
 * @returns {string} Status: 'online', 'idle', 'offline', 'error'
 */
function getDeviceStatus(device) {
    const baseStatus = device.status || 'offline';
    const lastUpdated = device.last_updated ? new Date(device.last_updated) : null;
    const state = device.current_state || {};
    
    if (baseStatus === 'offline') {
        return 'offline';
    }
    
    if (baseStatus === 'error') {
        return 'error';
    }
    
    // Check if device is idle (online but inactive for >5 minutes)
    if (lastUpdated) {
        const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
        if (lastUpdated < fiveMinutesAgo) {
            return 'idle';
        }
    }
    
    return 'online';
}

/**
 * Get status configuration (label, color, description)
 * @param {string} status - Device status
 * @returns {Object} Status configuration
 */
function getStatusConfig(status) {
    const configs = {
        online: { label: '在线', color: '#4CAF50', description: '设备正常运行' },
        idle: { label: '空闲', color: '#FFC107', description: '设备在线但无活动' },
        offline: { label: '离线', color: '#F44336', description: '设备已离线' },
        error: { label: '错误', color: '#9C27B0', description: '设备发生错误' }
    };
    return configs[status] || configs.offline;
}

/**
 * Get detailed status information based on device type
 * @param {Object} device - Device data
 * @returns {Array} Array of status detail objects
 */
function getDeviceStatusDetails(device) {
    const state = device.current_state || {};
    const details = [];
    
    switch (device.device_type) {
        case 'lamp':
            details.push(
                { label: '电源', value: state.power ? '开启' : '关闭' },
                { label: '亮度', value: state.power ? `${state.brightness || 0}%` : '-' },
                { label: '色温', value: state.color_temperature === 'warm' ? '暖光' : 
                                      state.color_temperature === 'cool' ? '冷光' : '正常' }
            );
            break;
        case 'air_conditioner':
            details.push(
                { label: '电源', value: state.power ? '开启' : '关闭' },
                { label: '温度', value: state.power ? `${state.temperature || 24}°C` : '-' },
                { label: '模式', value: state.mode === 'cool' ? '制冷' : 
                                      state.mode === 'heat' ? '制热' : 
                                      state.mode === 'dry' ? '除湿' : '送风' },
                { label: '风速', value: state.fan_speed ? `${state.fan_speed}档` : '自动' }
            );
            break;
        case 'curtain':
            details.push(
                { label: '位置', value: `${state.position || 0}%` },
                { label: '状态', value: state.position === 0 ? '已关闭' : 
                                      state.position === 100 ? '已打开' : '部分打开' }
            );
            break;
        default:
            details.push({ label: '状态', value: '未知设备类型' });
    }
    
    return details;
}

/**
 * Format last seen time in human-readable format
 * @param {string} timestamp - ISO timestamp
 * @returns {string} Formatted time string
 */
function formatLastSeen(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) {
        return '刚刚';
    } else if (diffMins < 60) {
        return `${diffMins}分钟前`;
    } else if (diffHours < 24) {
        return `${diffHours}小时前`;
    } else if (diffDays < 7) {
        return `${diffDays}天前`;
    } else {
        return date.toLocaleDateString('zh-CN');
    }
}

/**
 * 显示添加设备模态窗口
 */
function showAddDeviceModal() {
    // 重置表单
    document.getElementById('device-id').value = '';
    document.getElementById('device-name').value = '';
    document.getElementById('device-type').value = '';
    document.getElementById('device-modal-title').textContent = '添加设备';
    
    // 隐藏错误信息
    document.getElementById('device-name-error').textContent = '';
    document.getElementById('device-type-error').textContent = '';
    document.getElementById('device-type-info').style.display = 'none';
    
    // 显示模态窗口
    const modal = document.getElementById('device-modal');
    modal.style.display = 'flex';
    modal.classList.add('modal-visible');
}

/**
 * 显示编辑设备模态窗口
 * 
 * @param {string} deviceId - 设备ID
 */
function showEditDeviceModal(deviceId) {
    const device = devicesData.find(d => d.device_id === deviceId);
    if (!device) {
        showToast('设备不存在', 'error');
        return;
    }
    
    // 填充表单
    document.getElementById('device-id').value = device.device_id;
    document.getElementById('device-name').value = device.device_name;
    document.getElementById('device-type').value = device.device_type;
    document.getElementById('device-modal-title').textContent = '编辑设备';
    
    // 隐藏错误信息
    document.getElementById('device-name-error').textContent = '';
    document.getElementById('device-type-error').textContent = '';
    
    // 显示类型描述
    onDeviceTypeChange();
    
    // 禁用类型选择(编辑时不允许修改类型)
    document.getElementById('device-type').disabled = true;
    
    // 显示模态窗口
    const modal = document.getElementById('device-modal');
    modal.style.display = 'flex';
    modal.classList.add('modal-visible');
}

/**
 * 关闭设备模态窗口
 */
function closeDeviceModal() {
    const modal = document.getElementById('device-modal');
    modal.classList.remove('modal-visible');
    setTimeout(() => {
        modal.style.display = 'none';
        // 重新启用类型选择
        document.getElementById('device-type').disabled = false;
    }, 300);
}

/**
 * 设备类型改变时的处理
 */
function onDeviceTypeChange() {
    const type = document.getElementById('device-type').value;
    const typeInfo = document.getElementById('device-type-info');
    const typeDescription = document.getElementById('type-description');
    
    if (type && DEVICE_TYPE_DESCRIPTIONS[type]) {
        typeDescription.textContent = DEVICE_TYPE_DESCRIPTIONS[type];
        typeInfo.style.display = 'block';
    } else {
        typeInfo.style.display = 'none';
    }
}

/**
 * 保存设备(创建或更新)
 */
async function saveDevice() {
    const deviceId = document.getElementById('device-id').value;
    const name = document.getElementById('device-name').value.trim();
    const type = document.getElementById('device-type').value;
    
    // 验证表单
    let hasError = false;
    
    if (!name) {
        document.getElementById('device-name-error').textContent = '请输入设备名称';
        hasError = true;
    } else {
        document.getElementById('device-name-error').textContent = '';
    }
    
    if (!type) {
        document.getElementById('device-type-error').textContent = '请选择设备类型';
        hasError = true;
    } else {
        document.getElementById('device-type-error').textContent = '';
    }
    
    if (hasError) return;
    
    // 显示加载状态
    const saveBtn = document.getElementById('save-device-btn');
    const originalText = saveBtn.textContent;
    saveBtn.textContent = '保存中...';
    saveBtn.disabled = true;
    
    try {
        let response;
        
        if (deviceId) {
            // 更新设备
            response = await fetch(`/api/devices/${deviceId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
        } else {
            // 创建设备
            response = await fetch('/api/devices', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, type })
            });
        }
        
        const data = await response.json();
        
        if (data.success) {
            showToast(deviceId ? '设备更新成功' : '设备创建成功', 'success');
            closeDeviceModal();
            loadDevices(); // 重新加载设备列表
        } else {
            showToast(data.message || '操作失败', 'error');
        }
    } catch (error) {
        console.error('保存设备失败:', error);
        showToast('保存失败，请检查网络连接', 'error');
    } finally {
        saveBtn.textContent = originalText;
        saveBtn.disabled = false;
    }
}

/**
 * 确认删除设备
 * 
 * @param {string} deviceId - 设备ID
 */
function confirmDeleteDevice(deviceId) {
    const device = devicesData.find(d => d.device_id === deviceId);
    if (!device) return;
    
    showConfirmModal(
        '删除设备',
        `确定要删除设备 "${device.device_name}" 吗？此操作无法撤销。`,
        () => deleteDevice(deviceId)
    );
}

/**
 * 删除设备
 * 
 * @param {string} deviceId - 设备ID
 */
async function deleteDevice(deviceId) {
    try {
        const response = await fetch(`/api/devices/${deviceId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('设备删除成功', 'success');
            loadDevices(); // 重新加载设备列表
        } else {
            showToast(data.message || '删除失败', 'error');
        }
    } catch (error) {
        console.error('删除设备失败:', error);
        showToast('删除失败，请检查网络连接', 'error');
    }
}

// ==================== 设备控制功能 ====================

/**
 * 打开设备控制面板模态窗口
 * 
 * @param {string} deviceId - 设备ID
 */
function openDeviceControlModal(deviceId) {
    const device = devicesData.find(d => d.device_id === deviceId);
    if (!device) {
        showToast('设备不存在', 'error');
        return;
    }
    
    currentDeviceId = deviceId;
    
    // 设置模态窗口标题
    document.getElementById('control-modal-title').textContent = device.device_name;
    document.getElementById('control-device-id').value = deviceId;
    
    // 更新状态显示
    updateDeviceStatusBar(device);
    
    // 根据设备类型显示对应的控制面板
    document.getElementById('lamp-control-panel').style.display = 'none';
    document.getElementById('ac-control-panel').style.display = 'none';
    document.getElementById('curtain-control-panel').style.display = 'none';
    
    if (device.device_type === 'lamp') {
        document.getElementById('lamp-control-panel').style.display = 'block';
        initLampControls(device);
    } else if (device.device_type === 'air_conditioner') {
        document.getElementById('ac-control-panel').style.display = 'block';
        initACControls(device);
    } else if (device.device_type === 'curtain') {
        document.getElementById('curtain-control-panel').style.display = 'block';
        initCurtainControls(device);
    }
    
    // 显示模态窗口
    const modal = document.getElementById('device-control-modal');
    modal.style.display = 'flex';
    modal.classList.add('modal-visible');
}

/**
 * 关闭设备控制面板模态窗口
 */
function closeDeviceControlModal() {
    const modal = document.getElementById('device-control-modal');
    modal.classList.remove('modal-visible');
    setTimeout(() => {
        modal.style.display = 'none';
        currentDeviceId = null;
    }, 300);
}

/**
 * 更新设备状态栏显示
 * 
 * @param {Object} device - 设备数据
 */
function updateDeviceStatusBar(device) {
    const indicator = document.getElementById('device-status-indicator');
    const statusText = document.getElementById('device-status-text');
    
    if (device.status === 'online') {
        indicator.className = 'status-indicator online';
        statusText.textContent = '设备在线';
    } else {
        indicator.className = 'status-indicator offline';
        statusText.textContent = '设备离线';
    }
}

// ==================== 台灯控制 ====================

/**
 * 初始化台灯控制面板
 * 
 * @param {Object} device - 设备数据
 */
function initLampControls(device) {
    const state = device.current_state || {};
    
    // 设置电源按钮状态
    updateLampPowerButton(state.power);
    
    // 设置亮度滑块
    document.getElementById('lamp-brightness-slider').value = state.brightness || 50;
    document.getElementById('lamp-brightness-value').textContent = state.brightness || 50;
    
    // 设置色温按钮
    updateLampColorTempButtons(state.color_temp || 'normal');
    
    // 设置定时器
    document.getElementById('lamp-timer-select').value = state.timer_off || '';
}

/**
 * 更新台灯电源按钮显示
 * 
 * @param {boolean} power - 电源状态
 */
function updateLampPowerButton(power) {
    const btn = document.getElementById('lamp-power-btn');
    const text = btn.querySelector('.power-text');
    
    if (power) {
        btn.classList.add('on');
        text.textContent = '开启';
    } else {
        btn.classList.remove('on');
        text.textContent = '关闭';
    }
}

/**
 * 切换台灯电源
 */
async function toggleLampPower() {
    if (!currentDeviceId) return;
    
    const device = devicesData.find(d => d.device_id === currentDeviceId);
    if (!device) return;
    
    const command = device.current_state.power ? 'power_off' : 'power_on';
    
    const result = await sendDeviceCommand(currentDeviceId, command);
    if (result.success) {
        device.current_state.power = !device.current_state.power;
        updateLampPowerButton(device.state.power);
        renderDeviceList(); // 更新列表显示
    }
}

/**
 * 台灯亮度改变
 * 
 * @param {number} value - 亮度值
 */
function onLampBrightnessChange(value) {
    document.getElementById('lamp-brightness-value').textContent = value;
}

/**
 * 设置台灯亮度
 */
async function setLampBrightness() {
    if (!currentDeviceId) return;
    
    const value = parseInt(document.getElementById('lamp-brightness-slider').value);
    
    const result = await sendDeviceCommand(currentDeviceId, 'set_brightness', { brightness: value });
    if (result.success) {
        const device = devicesData.find(d => d.device_id === currentDeviceId);
        if (device) {
            device.current_state.brightness = value;
            renderDeviceList();
        }
    }
}

/**
 * 更新台灯色温按钮状态
 * 
 * @param {string} temp - 色温类型
 */
function updateLampColorTempButtons(temp) {
    const normalBtn = document.getElementById('lamp-temp-normal');
    const eyeCareBtn = document.getElementById('lamp-temp-eye-care');
    
    normalBtn.classList.toggle('active', temp === 'normal');
    eyeCareBtn.classList.toggle('active', temp === 'eye_care');
}

/**
 * 设置台灯色温
 * 
 * @param {string} temp - 色温类型
 */
async function setLampColorTemp(temp) {
    if (!currentDeviceId) return;
    
    const result = await sendDeviceCommand(currentDeviceId, 'set_color_temp', { color_temp: temp });
    if (result.success) {
        updateLampColorTempButtons(temp);
        const device = devicesData.find(d => d.device_id === currentDeviceId);
        if (device) {
            device.current_state.color_temp = temp;
        }
    }
}

/**
 * 设置台灯定时
 * 
 * @param {string} minutes - 分钟数
 */
async function setLampTimer(minutes) {
    if (!currentDeviceId) return;
    
    const value = minutes ? parseInt(minutes) : null;
    
    const result = await sendDeviceCommand(currentDeviceId, 'set_timer', { minutes: value });
    if (result.success) {
        const device = devicesData.find(d => d.device_id === currentDeviceId);
        if (device) {
            device.current_state.timer_off = value;
        }
        showToast(minutes ? `已设置${minutes}分钟后自动关闭` : '已取消定时关闭', 'success');
    }
}

// ==================== 空调控制 ====================

/**
 * 初始化空调控制面板
 * 
 * @param {Object} device - 设备数据
 */
function initACControls(device) {
    const state = device.current_state || {};
    
    // 设置电源按钮
    updateACPowerButton(state.power);
    
    // 设置温度显示
    document.getElementById('ac-temp-display').textContent = `${state.temperature || 26}°C`;
    
    // 设置模式按钮
    updateACModeButtons(state.mode || 'cool');
    
    // 设置风速滑块
    document.getElementById('ac-fan-slider').value = state.fan_speed || 3;
    document.getElementById('ac-fan-value').textContent = state.fan_speed || 3;
}

/**
 * 更新空调电源按钮显示
 * 
 * @param {boolean} power - 电源状态
 */
function updateACPowerButton(power) {
    const btn = document.getElementById('ac-power-btn');
    const text = btn.querySelector('.power-text');
    
    if (power) {
        btn.classList.add('on');
        text.textContent = '开启';
    } else {
        btn.classList.remove('on');
        text.textContent = '关闭';
    }
}

/**
 * 切换空调电源
 */
async function toggleACPower() {
    if (!currentDeviceId) return;
    
    const device = devicesData.find(d => d.device_id === currentDeviceId);
    if (!device) return;
    
    const command = device.current_state.power ? 'power_off' : 'power_on';
    
    const result = await sendDeviceCommand(currentDeviceId, command);
    if (result.success) {
        device.current_state.power = !device.current_state.power;
        updateACPowerButton(device.state.power);
        renderDeviceList();
    }
}

/**
 * 调节空调温度
 * 
 * @param {number} delta - 温度变化量
 */
async function adjustACTemp(delta) {
    if (!currentDeviceId) return;
    
    const device = devicesData.find(d => d.device_id === currentDeviceId);
    if (!device) return;
    
    const newTemp = (device.current_state.temperature || 26) + delta;
    
    if (newTemp < 16 || newTemp > 30) return;
    
    const result = await sendDeviceCommand(currentDeviceId, 'set_temperature', { temperature: newTemp });
    if (result.success) {
        device.current_state.temperature = newTemp;
        document.getElementById('ac-temp-display').textContent = `${newTemp}°C`;
        renderDeviceList();
    }
}

/**
 * 更新空调模式按钮状态
 * 
 * @param {string} mode - 模式
 */
function updateACModeButtons(mode) {
    const coolBtn = document.getElementById('ac-mode-cool');
    const heatBtn = document.getElementById('ac-mode-heat');
    
    coolBtn.classList.toggle('active', mode === 'cool');
    heatBtn.classList.toggle('active', mode === 'heat');
}

/**
 * 设置空调模式
 * 
 * @param {string} mode - 模式
 */
async function setACMode(mode) {
    if (!currentDeviceId) return;
    
    const result = await sendDeviceCommand(currentDeviceId, 'set_mode', { mode });
    if (result.success) {
        updateACModeButtons(mode);
        const device = devicesData.find(d => d.device_id === currentDeviceId);
        if (device) {
            device.current_state.mode = mode;
            renderDeviceList();
        }
    }
}

/**
 * 空调风速改变
 * 
 * @param {number} value - 风速值
 */
function onACFanChange(value) {
    document.getElementById('ac-fan-value').textContent = value;
}

/**
 * 设置空调风速
 */
async function setACFanSpeed() {
    if (!currentDeviceId) return;
    
    const value = parseInt(document.getElementById('ac-fan-slider').value);
    
    const result = await sendDeviceCommand(currentDeviceId, 'set_fan_speed', { fan_speed: value });
    if (result.success) {
        const device = devicesData.find(d => d.device_id === currentDeviceId);
        if (device) {
            device.current_state.fan_speed = value;
            renderDeviceList();
        }
    }
}

// ==================== 窗帘控制 ====================

/**
 * 初始化窗帘控制面板
 * 
 * @param {Object} device - 设备数据
 */
function initCurtainControls(device) {
    const state = device.current_state || {};
    
    // 设置位置显示
    const position = state.position || 0;
    document.getElementById('curtain-position-value').textContent = `${position}%`;
    document.getElementById('curtain-position-slider').value = position;
}

/**
 * 窗帘位置改变
 * 
 * @param {number} value - 位置值
 */
function onCurtainPositionChange(value) {
    document.getElementById('curtain-position-value').textContent = `${value}%`;
}

/**
 * 控制窗帘
 * 
 * @param {string} command - 命令(open/close/stop)
 */
async function controlCurtain(command) {
    if (!currentDeviceId) return;
    
    let params = {};
    
    if (command === 'set_position') {
        params.position = parseInt(document.getElementById('curtain-position-slider').value);
    }
    
    const result = await sendDeviceCommand(currentDeviceId, command, params);
    if (result.success) {
        const device = devicesData.find(d => d.device_id === currentDeviceId);
        if (device) {
            if (command === 'open') {
                device.current_state.position = 100;
            } else if (command === 'close') {
                device.current_state.position = 0;
            } else if (command === 'set_position') {
                device.current_state.position = params.position;
            }
            
            // 更新显示
            if (command !== 'stop') {
                document.getElementById('curtain-position-value').textContent = `${device.current_state.position}%`;
                document.getElementById('curtain-position-slider').value = device.current_state.position;
                renderDeviceList();
            }
        }
    }
}

// ==================== 通用控制功能 ====================

/**
 * 发送设备控制命令
 * 
 * @param {string} deviceId - 设备ID
 * @param {string} command - 命令
 * @param {Object} params - 参数
 * @returns {Object} 执行结果
 */
async function sendDeviceCommand(deviceId, command, params = {}) {
    try {
        const response = await fetch(`/api/devices/${deviceId}/command`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command, params })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
        } else {
            showToast(data.message || '操作失败', 'error');
        }
        
        return data;
    } catch (error) {
        console.error('发送设备命令失败:', error);
        showToast('操作失败，请检查网络连接', 'error');
        return { success: false, message: '网络错误' };
    }
}

/**
 * 启动设备状态轮询
 */
function startDeviceStatusPolling() {
    // 清除现有轮询
    if (deviceStatusInterval) {
        clearInterval(deviceStatusInterval);
    }
    
    // 每5秒轮询一次
    deviceStatusInterval = setInterval(async () => {
        // 只有在设备页面且控制面板未打开时才更新列表
        const deviceSection = document.getElementById('device-section');
        const controlModal = document.getElementById('device-control-modal');
        
        if (deviceSection && deviceSection.classList.contains('active')) {
            if (!controlModal || controlModal.style.display === 'none') {
                await refreshDeviceStatus();
            }
        }
    }, 5000);
}

/**
 * 刷新设备状态
 */
async function refreshDeviceStatus() {
    try {
        const response = await fetch('/api/devices');
        const data = await response.json();
        
        if (data.success) {
            const newDevices = data.devices || [];
            
            // 检查是否有变化
            if (JSON.stringify(newDevices) !== JSON.stringify(devicesData)) {
                devicesData = newDevices;
                renderDeviceList();
            }
        }
    } catch (error) {
        console.error('刷新设备状态失败:', error);
    }
}

// ==================== 通用工具函数 ====================

/**
 * 显示确认模态窗口
 * 
 * @param {string} title - 标题
 * @param {string} message - 消息
 * @param {Function} onConfirm - 确认回调
 */
function showConfirmModal(title, message, onConfirm) {
    document.getElementById('confirm-modal-title').textContent = title;
    document.getElementById('confirm-modal-message').textContent = message;
    
    const confirmBtn = document.getElementById('confirm-modal-btn');
    confirmBtn.onclick = () => {
        closeConfirmModal();
        onConfirm();
    };
    
    const modal = document.getElementById('confirm-modal');
    modal.style.display = 'flex';
    modal.classList.add('modal-visible');
}

/**
 * 关闭确认模态窗口
 */
function closeConfirmModal() {
    const modal = document.getElementById('confirm-modal');
    modal.classList.remove('modal-visible');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

/**
 * 显示Toast提示
 * 
 * @param {string} message - 消息
 * @param {string} type - 类型(success/error/warning/info)
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // 显示动画
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });
    
    // 3秒后自动移除
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

/**
 * HTML转义，防止XSS攻击
 * 
 * @param {string} text - 原始文本
 * @returns {string} 转义后的文本
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== 事件绑定 ====================



// 页面卸载时清理定时器
window.addEventListener('beforeunload', () => {
    if (deviceStatusInterval) {
        clearInterval(deviceStatusInterval);
    }
});
