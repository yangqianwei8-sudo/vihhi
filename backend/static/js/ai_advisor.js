// AI设计优化顾问系统 - JavaScript
(function() {
    'use strict';
    
    // 获取配置
    const config = window.AI_ADVISOR_CONFIG || {};
    
    // 存储当前分析结果和上下文
    let currentAnalysisContext = {
        problem: '',
        constraints: '',
        serviceTypeId: null,
        professionCode: '',
        budgetImpact: '',
        solutions: []
    };
    
    // 获取CSRF token
    function getCSRFToken() {
        return config.csrfToken || document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
    
    // API调用函数
    async function apiCall(url, method = 'GET', data = null) {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API调用失败:', error);
            throw error;
        }
    }
    
    // 初始化函数
    function initAIAdvisor() {
        const sendMessageBtn = document.getElementById('sendMessageBtn');
        const quickAnalysisBtn = document.getElementById('quickAnalysisBtn');
        const clearChatBtn = document.getElementById('clearChatBtn');
        
        if (sendMessageBtn) {
            sendMessageBtn.addEventListener('click', sendMessage);
        }
        if (quickAnalysisBtn) {
            quickAnalysisBtn.addEventListener('click', quickAnalysis);
        }
        if (clearChatBtn) {
            clearChatBtn.addEventListener('click', clearChat);
        }
        
        // 文件上传处理
        setupFileUpload();
        
        // 初始化聊天
        addWelcomeMessage();
        
        // 加载已保存的方案列表
        loadSavedSolutions();
    }
    
    // 发送消息
    async function sendMessage() {
        const problemInput = document.getElementById('problemInput');
        const constraintsInput = document.getElementById('constraintsInput');
        const constraints = constraintsInput?.value.trim() || '';
        const serviceTypeId = document.getElementById('serviceTypeId')?.value;
        const professionCode = document.getElementById('professionCode')?.value;
        const budgetImpact = document.getElementById('budgetImpact')?.value;
        
        // 保存当前分析上下文
        currentAnalysisContext = {
            problem: problem,
            constraints: constraints,
            serviceTypeId: serviceTypeId || null,
            professionCode: professionCode || '',
            budgetImpact: budgetImpact || '',
            solutions: []
        };
        
        const problem = problemInput?.value.trim();
        const constraints = constraintsInput?.value.trim() || '';
        
        if (!problem) {
            showToast('请输入优化前做法', '请详细描述优化前的做法', 'warning');
            return;
        }
        
        // 保存当前分析上下文
        currentAnalysisContext = {
            problem: problem,
            constraints: constraints,
            serviceTypeId: serviceTypeId || null,
            professionCode: professionCode || '',
            budgetImpact: budgetImpact || '',
            solutions: []
        };
        
        // 添加到聊天
        addChatMessage('user', problem);
        if (constraints) {
            addChatMessage('user', `约束条件: ${constraints}`);
        }
        
        // 显示加载
        showLoading(true);
        
        // 显示处理状态
        if (uploadedCADFiles && uploadedCADFiles.length > 0) {
            addChatMessage('ai', `正在解析CAD文件: ${uploadedCADFiles[0].name}，提取设计参数...`);
        }
        
        try {
            // 构建FormData（支持文件上传）
            const formData = new FormData();
            formData.append('problem', problem);
            formData.append('constraints', constraints || '');
            if (serviceTypeId) formData.append('service_type_id', serviceTypeId);
            if (professionCode) formData.append('profession_code', professionCode);
            if (budgetImpact) formData.append('budget_impact', budgetImpact);
            
            // 如果有上传的图片，添加到请求中
            if (uploadedImages && uploadedImages.length > 0) {
                formData.append('images', JSON.stringify(uploadedImages));
                addChatMessage('user', `已上传 ${uploadedImages.length} 张图纸，正在识别...`);
            }
            
            // 如果有上传的CAD文件，添加到请求中
            if (uploadedCADFiles && uploadedCADFiles.length > 0) {
                formData.append('cad_file', uploadedCADFiles[0]);
                addChatMessage('user', `已上传CAD文件: ${uploadedCADFiles[0].name}，正在解析...`);
            }
            
            // 调用API（使用FormData）
            // 显示上传进度（如果有）
            const response = await fetch(
                config.analyzeUrl || '/production/api/ai-advisor/analyze/',
                {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: formData
                }
            );
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const errorMsg = errorData.error || errorData.message || `HTTP错误: ${response.status}`;
                throw new Error(errorMsg);
            }
            const result = await response.json();
            
            // 检查是否有错误
            if (result.error) {
                throw new Error(result.error);
            }
            
            // 显示结果
            displayResults(result);
            
            // 显示AI回复
            let ai_message = result.summary || '分析完成，请查看下方优化方案。';
            if (result.solutions && result.solutions.length > 0) {
                ai_message += `\n\n已生成 ${result.solutions.length} 个优化方案，预计总节省金额约 ${result.solutions.reduce((sum, s) => sum + (s.savings || 0), 0).toFixed(1)} 万元。`;
            }
            addChatMessage('ai', ai_message);
            
        } catch (error) {
            console.error('分析错误:', error);
            showToast('分析失败', error.message || '请稍后重试', 'danger');
            addChatMessage('ai', `抱歉，分析过程中出现错误: ${error.message || '未知错误'}。请检查文件格式或稍后重试。`);
        } finally {
            showLoading(false);
        }
    }
    
    // 快速分析
    async function quickAnalysis() {
        const problemInput = document.getElementById('problemInput');
        const problem = problemInput?.value.trim();
        
        if (!problem) {
            showToast('请输入优化前做法', '请至少简要描述优化前的做法', 'warning');
            return;
        }
        
        addChatMessage('user', `[快速分析] ${problem.substring(0, 100)}...`);
        addChatMessage('ai', '正在快速分析您的问题...');
        
        try {
            const result = await apiCall(
                config.casesSearchUrl || '/production/api/ai-advisor/cases/search/?q=' + encodeURIComponent(problem),
                'GET'
            );
            
            let response = `找到 ${result.cases?.length || 0} 个相似案例：\n\n`;
            if (result.cases && result.cases.length > 0) {
                result.cases.forEach((caseItem, index) => {
                    response += `${index + 1}. ${caseItem.name} - ${caseItem.description}\n`;
                    response += `   节省金额: ¥ ${caseItem.savings} 万元\n\n`;
                });
            }
            response += "如需详细优化建议，请使用完整分析功能。";
            
            addChatMessage('ai', response);
            showToast('快速分析完成', `找到${result.cases?.length || 0}个相似案例`, 'success');
        } catch (error) {
            addChatMessage('ai', '快速分析失败，请稍后重试。');
        }
    }
    
    // 清空聊天
    function clearChat() {
        const chatContainer = document.getElementById('chatContainer');
        if (chatContainer) {
            chatContainer.innerHTML = '';
            addWelcomeMessage();
            showToast('已清空', '聊天记录已清空', 'info');
        }
    }
    
    // 添加聊天消息
    function addChatMessage(sender, message) {
        const chatContainer = document.getElementById('chatContainer');
        if (!chatContainer) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${sender}`;
        
        const icon = sender === 'user' ? 'fa-user' : 'fa-robot';
        const bgClass = sender === 'user' ? 'bg-success' : 'bg-primary';
        const label = sender === 'user' ? '工程师' : '设计优化AI顾问';
        
        messageElement.innerHTML = `
            <div class="d-flex align-items-center mb-2">
                <div class="${bgClass} rounded-circle d-flex align-items-center justify-content-center" style="width: 32px; height: 32px; margin-right: 10px;">
                    <i class="fas ${icon} text-white"></i>
                </div>
                <strong>${label}</strong>
            </div>
            <p>${escapeHtml(message)}</p>
        `;
        
        chatContainer.appendChild(messageElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // 添加欢迎消息
    function addWelcomeMessage() {
        addChatMessage('ai', '欢迎使用维海科技设计咨询AI顾问系统！我可以帮助您解决各种设计优化问题。请描述您的问题，我将基于内部案例库和专家知识为您提供优化建议。');
    }
    
    // 显示加载状态
    function showLoading(show) {
        const loading = document.getElementById('aiLoading');
        const results = document.getElementById('aiResults');
        
        if (loading) loading.style.display = show ? 'block' : 'none';
        if (results) results.style.display = show ? 'none' : 'block';
    }
    
    // 显示结果
    function displayResults(result) {
        if (result.solutions) {
            displaySolutions(result.solutions);
        }
        if (result.similar_cases) {
            displaySimilarCases(result.similar_cases);
        }
        if (result.analysis_report) {
            displayAnalysisReport(result.analysis_report);
        }
        if (result.risk_assessment) {
            displayRiskAssessment(result.risk_assessment);
        }
    }
    
    // 显示优化方案
    function displaySolutions(solutions) {
        const solutionsList = document.getElementById('solutionsList');
        if (!solutionsList) return;
        
        // 保存方案数据到上下文
        currentAnalysisContext.solutions = solutions;
        
        let html = '';
        solutions.forEach((solution, index) => {
            const riskClass = `risk-${solution.risk || 'low'}`;
            const riskText = solution.risk === 'low' ? '低风险' : solution.risk === 'medium' ? '中风险' : '高风险';
            
            html += `
                <div class="solution-item">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <h5>方案 ${index + 1}: ${solution.title}</h5>
                        <div class="text-end">
                            <span class="savings-badge">¥ ${solution.savings || 0} 万元</span>
                            <div class="mt-1">
                                <span class="risk-level ${riskClass}"></span>
                                <span class="small">${riskText}</span>
                            </div>
                        </div>
                    </div>
                    <p class="mb-3">${solution.description || ''}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <button class="btn btn-sm btn-outline-primary" onclick="selectSolution(${index})">
                            <i class="fas fa-check me-1"></i> 选择此方案
                        </button>
                    </div>
                </div>
            `;
        });
        
        solutionsList.innerHTML = html;
    }
    
    // 显示相似案例
    function displaySimilarCases(cases) {
        const similarCases = document.getElementById('similarCases');
        if (!similarCases) return;
        
        let html = '';
        if (cases.length === 0) {
            html = '<div class="text-center py-5"><p class="text-muted">未找到相似案例</p></div>';
        } else {
            cases.forEach((caseItem) => {
                html += `
                    <div class="case-item" onclick="loadCaseDetails('${caseItem.id}')">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="mb-0">${caseItem.name}</h6>
                            <span class="cost-savings">¥ ${caseItem.savings}万</span>
                        </div>
                        <p class="small text-muted mb-2">${caseItem.description}</p>
                    </div>
                `;
            });
        }
        
        similarCases.innerHTML = html;
    }
    
    // 显示分析报告
    function displayAnalysisReport(report) {
        const analysisReport = document.getElementById('analysisReport');
        if (!analysisReport) return;
        
        analysisReport.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">优化分析报告</h5>
                    <div class="mt-3">${report.content || ''}</div>
                </div>
            </div>
        `;
    }
    
    // 显示风险评估
    function displayRiskAssessment(risks) {
        const riskAssessment = document.getElementById('riskAssessment');
        if (!riskAssessment) return;
        
        let html = '';
        risks.forEach((risk) => {
            const riskClass = `risk-${risk.level || 'low'}`;
            const riskText = risk.level === 'low' ? '低风险' : risk.level === 'medium' ? '中风险' : '高风险';
            
            html += `
                <div class="solution-item">
                    <div class="d-flex align-items-center mb-2">
                        <span class="risk-level ${riskClass}"></span>
                        <h6 class="mb-0 ms-2">${risk.title}</h6>
                        <span class="ms-auto badge bg-${risk.level === 'low' ? 'success' : risk.level === 'medium' ? 'warning' : 'danger'}">${riskText}</span>
                    </div>
                    <p class="small mb-2">${risk.description}</p>
                </div>
            `;
        });
        
        riskAssessment.innerHTML = html;
    }
    
    // 存储上传的图片（base64格式）
    let uploadedImages = [];
    // 存储上传的CAD文件
    let uploadedCADFiles = [];
    
    // 设置文件上传
    function setupFileUpload() {
        const fileUploadArea = document.getElementById('fileUploadArea');
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.multiple = true;
        fileInput.accept = 'image/*,.pdf,.dwg,.dxf'; // 支持图片、PDF、DWG、DXF文件
        fileInput.style.display = 'none';
        
        if (fileUploadArea) {
            fileUploadArea.addEventListener('click', () => fileInput.click());
            fileInput.addEventListener('change', handleFileUpload);
            document.body.appendChild(fileInput);
        }
    }
    
    // 将文件转换为base64
    function fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                // 移除data:image/jpeg;base64,前缀，只保留base64数据
                const base64 = reader.result.split(',')[1];
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }
    
    // 处理文件上传
    async function handleFileUpload(e) {
        const files = e.target.files;
        const fileList = document.getElementById('fileList');
        if (!fileList || files.length === 0) return;
        
        fileList.innerHTML = '';
        uploadedImages = []; // 清空之前的图片
        uploadedCADFiles = []; // 清空之前的CAD文件
        
        // 分离图片文件和CAD文件
        const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
        const cadFiles = Array.from(files).filter(file => {
            const ext = file.name.toLowerCase().split('.').pop();
            return ['dwg', 'dxf', 'pdf'].includes(ext);
        });
        
        if (imageFiles.length === 0 && cadFiles.length === 0) {
            showToast('文件类型不支持', '请上传图片文件（JPG、PNG等）或CAD文件（DWG、DXF、PDF）', 'warning');
            return;
        }
        
        // 限制最多上传3张图片
        if (imageFiles.length > 3) {
            showToast('图片数量过多', '最多只能上传3张图片', 'warning');
            imageFiles.splice(3);
        }
        
        // 限制最多上传1个CAD文件（避免处理时间过长）
        if (cadFiles.length > 1) {
            showToast('CAD文件数量过多', '最多只能上传1个CAD文件', 'warning');
            cadFiles.splice(1);
        }
        
        // 显示加载提示
        const loadingItem = document.createElement('div');
        loadingItem.className = 'text-center p-3';
        loadingItem.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>正在处理文件...';
        fileList.appendChild(loadingItem);
        
        try {
            // 处理图片文件
            for (let i = 0; i < imageFiles.length; i++) {
                const file = imageFiles[i];
                const base64 = await fileToBase64(file);
                uploadedImages.push(base64);
                
                // 显示文件项
                const fileItem = document.createElement('div');
                fileItem.className = 'd-flex justify-content-between align-items-center border rounded p-2 mb-2';
                fileItem.innerHTML = `
                    <div>
                        <i class="fas fa-image text-primary me-2"></i>
                        <span>${file.name}</span>
                        <small class="text-muted ms-2">(${(file.size / 1024).toFixed(1)} KB)</small>
                        <span class="badge bg-success ms-2">图片已就绪</span>
                    </div>
                    <button class="btn btn-sm btn-outline-danger" onclick="removeImage(${i})">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                fileList.appendChild(fileItem);
            }
            
            // 处理CAD文件
            for (let i = 0; i < cadFiles.length; i++) {
                const file = cadFiles[i];
                
                // 检查文件大小（50MB限制）
                const maxSize = 50 * 1024 * 1024; // 50MB
                if (file.size > maxSize) {
                    showToast('文件过大', `${file.name} 超过50MB限制，已跳过`, 'warning');
                    continue;
                }
                
                uploadedCADFiles.push(file);
                
                // 显示文件项
                const fileItem = document.createElement('div');
                fileItem.className = 'd-flex justify-content-between align-items-center border rounded p-2 mb-2';
                const fileIcon = file.name.toLowerCase().endsWith('.dwg') ? 'fa-drafting-compass' : 
                                file.name.toLowerCase().endsWith('.dxf') ? 'fa-file-code' : 'fa-file-pdf';
                const fileSizeMB = (file.size / 1024 / 1024).toFixed(2);
                fileItem.innerHTML = `
                    <div>
                        <i class="fas ${fileIcon} text-warning me-2"></i>
                        <span>${file.name}</span>
                        <small class="text-muted ms-2">(${fileSizeMB} MB)</small>
                        <span class="badge bg-info ms-2">CAD文件已就绪</span>
                    </div>
                    <button class="btn btn-sm btn-outline-danger" onclick="removeCADFile(${i})">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                fileList.appendChild(fileItem);
            }
            
            // 显示文件大小警告（如果有大文件）
            const fileSizeWarning = document.getElementById('fileSizeWarning');
            if (fileSizeWarning) {
                const allFiles = [...uploadedImages.map(() => ({size: 0})), ...uploadedCADFiles];
                const hasLargeFile = allFiles.some(f => f.size > 10 * 1024 * 1024); // 10MB
                fileSizeWarning.style.display = hasLargeFile ? 'block' : 'none';
            }
            
            // 移除加载提示
            loadingItem.remove();
            
            let message = '';
            if (uploadedImages.length > 0) {
                message += `已上传 ${uploadedImages.length} 张图片`;
            }
            if (uploadedCADFiles.length > 0) {
                if (message) message += '，';
                message += `已上传 ${uploadedCADFiles.length} 个CAD文件`;
            }
            message += '，将在分析时使用';
            showToast('文件上传成功', message, 'success');
        } catch (error) {
            loadingItem.remove();
            showToast('文件处理失败', '请检查文件格式后重试', 'danger');
            console.error('文件处理错误:', error);
        }
    }
    
    // 移除图片
    function removeImage(index) {
        if (index >= 0 && index < uploadedImages.length) {
            uploadedImages.splice(index, 1);
            // 重新渲染文件列表
            const fileList = document.getElementById('fileList');
            if (fileList) {
                // 找到对应的图片文件项并移除
                const fileItems = fileList.querySelectorAll('div.d-flex');
                let imageIndex = 0;
                for (let i = 0; i < fileItems.length; i++) {
                    const item = fileItems[i];
                    if (item.innerHTML.includes('图片已就绪')) {
                        if (imageIndex === index) {
                            item.remove();
                            break;
                        }
                        imageIndex++;
                    }
                }
            }
            showToast('图片已移除', uploadedImages.length > 0 ? `还有 ${uploadedImages.length} 张图片` : '所有图片已移除', 'info');
        }
    }
    
    // 移除CAD文件
    function removeCADFile(index) {
        if (index >= 0 && index < uploadedCADFiles.length) {
            uploadedCADFiles.splice(index, 1);
            // 重新渲染文件列表
            const fileList = document.getElementById('fileList');
            if (fileList) {
                // 找到对应的CAD文件项并移除
                const fileItems = fileList.querySelectorAll('div.d-flex');
                let cadIndex = 0;
                for (let i = 0; i < fileItems.length; i++) {
                    const item = fileItems[i];
                    if (item.innerHTML.includes('CAD文件已就绪')) {
                        if (cadIndex === index) {
                            item.remove();
                            break;
                        }
                        cadIndex++;
                    }
                }
            }
            showToast('CAD文件已移除', uploadedCADFiles.length > 0 ? `还有 ${uploadedCADFiles.length} 个CAD文件` : '所有CAD文件已移除', 'info');
        }
    }
    
    // 全局函数，供HTML调用
    window.removeImage = removeImage;
    window.removeCADFile = removeCADFile;
    
    // 工具函数
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function showToast(title, message, type) {
        // 简单的toast实现
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
        toast.style.zIndex = '9999';
        toast.innerHTML = `
            <strong>${title}</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
    
    // 全局函数：选择方案并保存
    window.selectSolution = async function(index) {
        if (!currentAnalysisContext.solutions || index < 0 || index >= currentAnalysisContext.solutions.length) {
            showToast('错误', '方案数据不存在', 'danger');
            return;
        }
        
        const solution = currentAnalysisContext.solutions[index];
        
        try {
            // 调用API保存方案
            const response = await apiCall(
                config.saveSolutionUrl || '/production/api/ai-advisor/solutions/save/',
                'POST',
                {
                    solution_index: index,
                    problem_description: currentAnalysisContext.problem,
                    constraints: currentAnalysisContext.constraints,
                    service_type_id: currentAnalysisContext.serviceTypeId,
                    profession_code: currentAnalysisContext.professionCode,
                    budget_impact: currentAnalysisContext.budgetImpact,
                    solution: solution,
                    analysis_context: currentAnalysisContext
                }
            );
            
            if (response.success) {
                showToast('保存成功', `方案"${solution.title}"已保存到我的方案库`, 'success');
                // 刷新已保存的方案列表
                loadSavedSolutions();
            } else {
                showToast('保存失败', response.error || '未知错误', 'danger');
            }
        } catch (error) {
            console.error('保存方案失败:', error);
            showToast('保存失败', error.message || '请稍后重试', 'danger');
        }
    };
    
    // 加载已保存的方案列表
    async function loadSavedSolutions() {
        const savedSolutionsList = document.getElementById('savedSolutionsList');
        if (!savedSolutionsList) {
            console.warn('未找到savedSolutionsList元素，我的方案库可能未正确加载');
            return;
        }
        
        try {
            const listUrl = config.listSolutionsUrl || '/production/api/ai-advisor/solutions/list/';
            console.log('正在加载已保存的方案列表，URL:', listUrl);
            
            const response = await apiCall(listUrl, 'GET');
            console.log('方案列表API响应:', response);
            
            if (response.success && response.solutions) {
                let html = '';
                if (response.solutions.length === 0) {
                    html = '<div class="text-center py-3"><p class="text-muted small">暂无已保存的方案</p><p class="text-muted small mt-2">选择优化方案后，方案将自动保存到这里</p></div>';
                } else {
                    response.solutions.forEach((sol) => {
                        const riskText = sol.risk_level === 'low' ? '低风险' : sol.risk_level === 'medium' ? '中风险' : '高风险';
                        html += `
                            <div class="saved-solution-item border-bottom pb-2 mb-2">
                                <div class="d-flex justify-content-between align-items-start mb-1">
                                    <h6 class="mb-0 small">${escapeHtml(sol.solution_title)}</h6>
                                    ${sol.savings ? `<span class="badge bg-success">¥${sol.savings}万</span>` : ''}
                                </div>
                                <p class="small text-muted mb-1">${escapeHtml(sol.problem_description)}</p>
                                <div class="d-flex justify-content-between align-items-center">
                                    <span class="badge bg-secondary">${riskText}</span>
                                    <small class="text-muted">${sol.created_time}</small>
                                </div>
                            </div>
                        `;
                    });
                }
                savedSolutionsList.innerHTML = html;
                
                // 更新方案数量徽章
                const solutionCount = document.getElementById('solutionCount');
                if (solutionCount) {
                    if (response.solutions.length > 0) {
                        solutionCount.textContent = response.solutions.length;
                        solutionCount.style.display = 'inline-block';
                    } else {
                        solutionCount.style.display = 'none';
                    }
                }
            } else {
                console.warn('方案列表API返回异常:', response);
                savedSolutionsList.innerHTML = '<div class="text-center py-3"><p class="text-muted small">加载失败，请刷新页面重试</p></div>';
            }
        } catch (error) {
            console.error('加载已保存方案失败:', error);
            if (savedSolutionsList) {
                savedSolutionsList.innerHTML = '<div class="text-center py-3"><p class="text-danger small">加载失败: ' + escapeHtml(error.message) + '</p></div>';
            }
        }
    }
    
    window.loadCaseDetails = function(caseId) {
        showToast('加载案例', '正在加载案例详情...', 'info');
    };
    
    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAIAdvisor);
    } else {
        initAIAdvisor();
    }
    
})();

