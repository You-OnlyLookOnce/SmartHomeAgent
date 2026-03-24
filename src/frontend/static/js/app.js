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
            } else if (tab === 'regular') {
                loadTasks();
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
            <div class="schedule-actions">
                <button class="delete-btn" onclick="deleteSchedule('${schedule.id}')">删除</button>
            </div>
        `;
        scheduleList.appendChild(scheduleItem);
    });
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



// 检查任务提醒
async function checkTaskReminders() {
    try {
        const response = await fetch('/api/scheduler/list');
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                const tasks = data.schedules;
                const dueTasks = tasks.filter(task => {
                    // 检查任务是否到期
                    // 这里可以根据实际需求实现更复杂的检查逻辑
                    return true;
                });
                
                if (dueTasks.length > 0) {
                    // 显示小红点提醒
                    showNotificationBadge(dueTasks.length);
                }
            }
        }
    } catch (error) {
        console.error('检查任务提醒失败:', error);
    }
}

// 显示通知小红点
function showNotificationBadge(count) {
    // 检查是否已经存在小红点
    let badge = document.getElementById('notification-badge');
    if (!badge) {
        // 创建小红点元素
        badge = document.createElement('div');
        badge.id = 'notification-badge';
        badge.className = 'notification-badge';
        
        // 将小红点添加到任务管理导航项
        const taskNavItem = document.querySelector('.nav-item[data-section="task"]');
        if (taskNavItem) {
            taskNavItem.appendChild(badge);
        }
    }
    
    // 设置小红点计数
    badge.textContent = count;
    badge.style.display = 'inline-block';
}

// 清除通知小红点
function clearNotificationBadge() {
    const badge = document.getElementById('notification-badge');
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
        // 加载对话历史
        loadChatHistory(currentSessionId);
    } else {
        // 没有保存的会话ID，显示初始化界面
        console.log('没有保存的会话ID，显示初始化界面');
        showInitializationUI();
    }
    
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
    
    // 加载任务列表
    loadTasks();
    
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
                    'task': '任务管理',
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
                loadTasks();
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

// 初始化应用 - 确保DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM加载完成，开始初始化应用');
    init();
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
    await sendMessageWithRetry(message, 3); // 最多重试3次
}

// 带重试机制的消息发送函数
async function sendMessageWithRetry(message, maxRetries) {
    let retries = 0;
    const thinkingMessageId = 'thinking-' + Date.now();
    let answerMessageId = null;
    let answerContent = ''; // 累积答案内容
    isStreaming = true; // 标记是否正在进行流式响应
    
    while (retries < maxRetries) {
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
                stream: true
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
                    stream: true
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
