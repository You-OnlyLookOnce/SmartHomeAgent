// 前端应用逻辑

// DOM元素
const chatArea = document.getElementById('chat-area');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const taskInput = document.getElementById('task-input');
const createTaskBtn = document.getElementById('create-task-btn');
const taskList = document.getElementById('task-list');

// 初始化
function init() {
    // 绑定事件
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
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
    
    // 加载任务列表
    loadTasks();
    
    // 绑定侧边栏导航事件
    bindSidebarNavigation();
}

// 绑定侧边栏导航事件
function bindSidebarNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const contentSections = document.querySelectorAll('.content-section');
    const sectionTitle = document.getElementById('section-title');
    
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const section = item.getAttribute('data-section');
            
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
                    'task': '任务管理',
                    'memory': '记忆管理',
                    'scheduler': '定时任务',
                    'distillation': '记忆蒸馏',
                    'status': '系统状态'
                };
                sectionTitle.textContent = titles[section] || '聊天';
            }
            
            // 加载对应模块的内容
            if (section === 'memory') {
                loadMemoryFiles();
            } else if (section === 'scheduler') {
                loadScheduleList();
            }
        });
    });
}

// 发送消息
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    // 添加用户消息
    addMessage('sent', message);
    messageInput.value = '';
    
    // 调用后端API
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message, user_id: 'default_user' })
        });
        
        if (!response.ok) {
            throw new Error('API调用失败');
        }
        
        const data = await response.json();
        
        if (data.success) {
            let responseContent = '已收到你的消息';
            if (typeof data.response === 'object' && data.response !== null) {
                if (data.response.message) {
                    responseContent = data.response.message;
                } else if (data.response.result) {
                    responseContent = data.response.result;
                } else if (data.response.success === false) {
                    responseContent = '抱歉，无法理解你的请求，请换个方式表达。';
                }
            } else if (typeof data.response === 'string') {
                responseContent = data.response;
            }
            addMessage('received', responseContent);
        } else {
            addMessage('received', '抱歉，出了点问题，请再试试。');
        }
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
        // 调用后端API
        const response = await fetch('/api/device/control', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                device_id: deviceId,
                action: action,
                params: value ? { brightness: value } : {}
            })
        });
        
        if (!response.ok) {
            throw new Error('API调用失败');
        }
        
        const data = await response.json();
        
        if (data.success) {
            const message = data.message || `设备已${action === 'on' ? '打开' : action === 'off' ? '关闭' : '调整'}`;
            addMessage('received', message);
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
        const response = await fetch('/api/reminder/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title: taskContent })
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
        const response = await fetch('/api/reminder/list/default_user');
        
        if (!response.ok) {
            throw new Error('API调用失败');
        }
        
        const data = await response.json();
        
        if (data.success) {
            renderTasks(data.reminders);
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

// 加载记忆文件
async function loadMemoryFiles() {
    try {
        // 加载人格文件
        const soulResponse = await fetch('/api/memory/soul');
        if (soulResponse.ok) {
            const soulData = await soulResponse.json();
            if (soulData.success && soulData.data) {
                document.getElementById('soul-content').value = soulData.data;
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
    const content = document.getElementById('soul-content').value;
    try {
        const response = await fetch('/api/memory/soul', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content: content })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                alert('人格文件保存成功');
            } else {
                alert('保存失败: ' + (data.message || '未知错误'));
            }
        } else {
            alert('保存失败: API调用失败');
        }
    } catch (error) {
        console.error('保存人格文件失败:', error);
        alert('保存失败: ' + error.message);
    }
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
                renderScheduleList(data.schedules || []);
            }
        }
    } catch (error) {
        console.error('加载定时任务失败:', error);
    }
}

// 渲染定时任务列表
function renderScheduleList(schedules) {
    const scheduleList = document.getElementById('schedule-list');
    if (!scheduleList) return;
    
    scheduleList.innerHTML = '';
    
    if (schedules.length === 0) {
        const emptySchedule = document.createElement('div');
        emptySchedule.className = 'schedule-item';
        emptySchedule.innerHTML = '<div class="schedule-content">暂无定时任务</div>';
        scheduleList.appendChild(emptySchedule);
        return;
    }
    
    schedules.forEach(schedule => {
        const scheduleItem = document.createElement('div');
        scheduleItem.className = 'schedule-item';
        scheduleItem.innerHTML = `
            <div class="schedule-content">${schedule.title}</div>
            <div class="schedule-time">${schedule.time}</div>
            <div class="schedule-status ${schedule.status || 'pending'}">${schedule.status || '待执行'}</div>
        `;
        scheduleList.appendChild(scheduleItem);
    });
}

// 创建定时任务
async function createSchedule() {
    const taskInput = document.getElementById('schedule-task-input');
    const timeInput = document.getElementById('schedule-time-input');
    
    const task = taskInput.value.trim();
    const time = timeInput.value;
    
    if (!task || !time) {
        alert('请输入任务内容和时间');
        return;
    }
    
    try {
        const response = await fetch('/api/scheduler/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title: task, time: time })
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

// 记忆蒸馏相关函数

// 开始记忆蒸馏
async function startDistillation() {
    const statusDiv = document.getElementById('distillation-status');
    if (statusDiv) {
        statusDiv.innerHTML = '<p>正在进行记忆蒸馏...</p>';
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
    
    // 记忆蒸馏事件
    const startDistillationBtn = document.getElementById('start-distillation-btn');
    if (startDistillationBtn) {
        startDistillationBtn.addEventListener('click', startDistillation);
    }
    
    // 绑定记忆管理标签页事件
    bindMemoryTabs();
}

// 初始化应用
function init() {
    // 绑定事件
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
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
    
    // 加载任务列表
    loadTasks();
    
    // 绑定侧边栏导航事件
    bindSidebarNavigation();
    
    // 绑定新功能模块的事件
    bindNewModuleEvents();
}

// 初始化应用
init();
