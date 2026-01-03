/**
 * 通用组件库
 * 维海科技信息化管理平台
 * 版本: 1.0
 */

// ==================== 通知组件 ====================
class NotificationManager {
    constructor() {
        this.container = null;
        this.init();
    }
    
    init() {
        this.container = document.createElement('div');
        this.container.id = 'notificationContainer';
        this.container.className = 'notification-container';
        document.body.appendChild(this.container);
    }
    
    show(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-icon">
                <i class="bi bi-${this.getIcon(type)}"></i>
            </div>
            <div class="notification-message">${message}</div>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="bi bi-x"></i>
            </button>
        `;
        
        this.container.appendChild(notification);
        
        setTimeout(() => notification.classList.add('show'), 10);
        
        if (duration > 0) {
            setTimeout(() => this.remove(notification), duration);
        }
        
        return notification;
    }
    
    remove(notification) {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }
    
    getIcon(type) {
        const icons = {
            success: 'check-circle-fill',
            error: 'x-circle-fill',
            warning: 'exclamation-triangle-fill',
            info: 'info-circle-fill'
        };
        return icons[type] || 'info-circle-fill';
    }
    
    success(message, duration) {
        return this.show(message, 'success', duration);
    }
    
    error(message, duration) {
        return this.show(message, 'error', duration);
    }
    
    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }
    
    info(message, duration) {
        return this.show(message, 'info', duration);
    }
}

// ==================== 加载组件 ====================
class LoadingManager {
    constructor() {
        this.overlay = null;
        this.init();
    }
    
    init() {
        this.overlay = document.createElement('div');
        this.overlay.id = 'globalLoadingOverlay';
        this.overlay.className = 'loading-overlay';
        document.body.appendChild(this.overlay);
    }
    
    show(message = '加载中...') {
        this.overlay.innerHTML = `
            <div class="loading-content">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <div class="loading-message">${message}</div>
            </div>
        `;
        this.overlay.style.display = 'flex';
    }
    
    hide() {
        this.overlay.style.display = 'none';
    }
}

// ==================== 确认对话框组件 ====================
class ConfirmDialog {
    static async show(message, title = '确认操作', options = {}) {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" id="confirmBtn">确定</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            
            document.getElementById('confirmBtn').addEventListener('click', () => {
                bsModal.hide();
                setTimeout(() => {
                    modal.remove();
                    resolve(true);
                }, 300);
            });
            
            modal.addEventListener('hidden.bs.modal', () => {
                resolve(false);
            }, { once: true });
        });
    }
}

// ==================== 文件上传组件 ====================
class FileUploader {
    constructor(options = {}) {
        this.options = {
            accept: options.accept || '*/*',
            multiple: options.multiple || false,
            maxSize: options.maxSize || 10 * 1024 * 1024, // 10MB
            onUpload: options.onUpload || null,
            onProgress: options.onProgress || null,
            onError: options.onError || null
        };
    }
    
    select() {
        return new Promise((resolve) => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = this.options.accept;
            input.multiple = this.options.multiple;
            
            input.addEventListener('change', (e) => {
                const files = Array.from(e.target.files);
                const validFiles = files.filter(file => {
                    if (file.size > this.options.maxSize) {
                        if (this.options.onError) {
                            this.options.onError(`文件 ${file.name} 超过大小限制`);
                        }
                        return false;
                    }
                    return true;
                });
                
                resolve(validFiles);
            });
            
            input.click();
        });
    }
    
    async upload(file, url) {
        return new Promise((resolve, reject) => {
            const formData = new FormData();
            formData.append('file', file);
            
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable && this.options.onProgress) {
                    const percent = (e.loaded / e.total) * 100;
                    this.options.onProgress(percent);
                }
            });
            
            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch (e) {
                        resolve(xhr.responseText);
                    }
                } else {
                    reject(new Error(`上传失败: ${xhr.status}`));
                }
            });
            
            xhr.addEventListener('error', () => {
                reject(new Error('上传失败'));
            });
            
            xhr.open('POST', url);
            xhr.send(formData);
        });
    }
}

// ==================== 日期选择器组件 ====================
class DateRangePicker {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' 
            ? document.querySelector(container) 
            : container;
        this.options = {
            format: options.format || 'YYYY-MM-DD',
            startDate: options.startDate || null,
            endDate: options.endDate || null,
            onChange: options.onChange || null
        };
        this.init();
    }
    
    init() {
        this.container.innerHTML = `
            <div class="date-range-picker">
                <input type="date" class="form-control form-control-sm" id="startDate">
                <span class="date-separator">至</span>
                <input type="date" class="form-control form-control-sm" id="endDate">
            </div>
        `;
        
        const startInput = this.container.querySelector('#startDate');
        const endInput = this.container.querySelector('#endDate');
        
        if (this.options.startDate) {
            startInput.value = this.formatDate(this.options.startDate);
        }
        if (this.options.endDate) {
            endInput.value = this.formatDate(this.options.endDate);
        }
        
        startInput.addEventListener('change', () => {
            if (this.options.onChange) {
                this.options.onChange({
                    start: startInput.value,
                    end: endInput.value
                });
            }
        });
        
        endInput.addEventListener('change', () => {
            if (this.options.onChange) {
                this.options.onChange({
                    start: startInput.value,
                    end: endInput.value
                });
            }
        });
    }
    
    formatDate(date) {
        const d = new Date(date);
        return d.toISOString().split('T')[0];
    }
    
    getValue() {
        return {
            start: this.container.querySelector('#startDate').value,
            end: this.container.querySelector('#endDate').value
        };
    }
}

// ==================== 数据表格组件 ====================
class DataTable {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' 
            ? document.querySelector(container) 
            : container;
        this.options = {
            columns: options.columns || [],
            data: options.data || [],
            pagination: options.pagination !== false,
            pageSize: options.pageSize || 10,
            searchable: options.searchable !== false,
            sortable: options.sortable !== false
        };
        this.currentPage = 1;
        this.sortColumn = null;
        this.sortOrder = 'asc';
        this.searchQuery = '';
        this.init();
    }
    
    init() {
        this.render();
    }
    
    render() {
        const filteredData = this.getFilteredData();
        const paginatedData = this.getPaginatedData(filteredData);
        
        this.container.innerHTML = `
            ${this.options.searchable ? this.renderSearch() : ''}
            <div class="table-responsive">
                <table class="table table-hover">
                    ${this.renderHeader()}
                    ${this.renderBody(paginatedData)}
                </table>
            </div>
            ${this.options.pagination ? this.renderPagination(filteredData.length) : ''}
        `;
        
        this.bindEvents();
    }
    
    renderSearch() {
        return `
            <div class="mb-3">
                <input type="text" class="form-control" id="tableSearch" 
                       placeholder="搜索..." value="${this.searchQuery}">
            </div>
        `;
    }
    
    renderHeader() {
        return `
            <thead>
                <tr>
                    ${this.options.columns.map(col => `
                        <th class="${col.sortable !== false ? 'sortable' : ''}" 
                            data-column="${col.key}">
                            ${col.label}
                            ${col.sortable !== false ? '<i class="bi bi-arrow-down-up"></i>' : ''}
                        </th>
                    `).join('')}
                </tr>
            </thead>
        `;
    }
    
    renderBody(data) {
        return `
            <tbody>
                ${data.map(row => `
                    <tr>
                        ${this.options.columns.map(col => `
                            <td>${this.formatCell(row[col.key], col)}</td>
                        `).join('')}
                    </tr>
                `).join('')}
            </tbody>
        `;
    }
    
    renderPagination(total) {
        const totalPages = Math.ceil(total / this.options.pageSize);
        return `
            <nav>
                <ul class="pagination">
                    <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                        <a class="page-link" href="#" data-page="${this.currentPage - 1}">上一页</a>
                    </li>
                    ${Array.from({ length: totalPages }, (_, i) => i + 1).map(page => `
                        <li class="page-item ${page === this.currentPage ? 'active' : ''}">
                            <a class="page-link" href="#" data-page="${page}">${page}</a>
                        </li>
                    `).join('')}
                    <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
                        <a class="page-link" href="#" data-page="${this.currentPage + 1}">下一页</a>
                    </li>
                </ul>
            </nav>
        `;
    }
    
    formatCell(value, column) {
        if (column.formatter && typeof column.formatter === 'function') {
            return column.formatter(value);
        }
        return value || '-';
    }
    
    getFilteredData() {
        let data = [...this.options.data];
        
        if (this.searchQuery) {
            data = data.filter(row => {
                return this.options.columns.some(col => {
                    const value = String(row[col.key] || '').toLowerCase();
                    return value.includes(this.searchQuery.toLowerCase());
                });
            });
        }
        
        if (this.sortColumn) {
            data.sort((a, b) => {
                const aVal = a[this.sortColumn];
                const bVal = b[this.sortColumn];
                if (aVal < bVal) return this.sortOrder === 'asc' ? -1 : 1;
                if (aVal > bVal) return this.sortOrder === 'asc' ? 1 : -1;
                return 0;
            });
        }
        
        return data;
    }
    
    getPaginatedData(data) {
        const start = (this.currentPage - 1) * this.options.pageSize;
        const end = start + this.options.pageSize;
        return data.slice(start, end);
    }
    
    bindEvents() {
        // 搜索
        const searchInput = this.container.querySelector('#tableSearch');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchQuery = e.target.value;
                this.currentPage = 1;
                this.render();
            });
        }
        
        // 排序
        this.container.querySelectorAll('th.sortable').forEach(th => {
            th.addEventListener('click', () => {
                const column = th.getAttribute('data-column');
                if (this.sortColumn === column) {
                    this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
                } else {
                    this.sortColumn = column;
                    this.sortOrder = 'asc';
                }
                this.render();
            });
        });
        
        // 分页
        this.container.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(link.getAttribute('data-page'));
                if (page && page !== this.currentPage) {
                    this.currentPage = page;
                    this.render();
                }
            });
        });
    }
    
    updateData(data) {
        this.options.data = data;
        this.render();
    }
}

// ==================== 标签输入组件 ====================
class TagInput {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' 
            ? document.querySelector(container) 
            : container;
        this.options = {
            placeholder: options.placeholder || '输入标签后按回车',
            allowDuplicates: options.allowDuplicates || false,
            maxTags: options.maxTags || null,
            onChange: options.onChange || null
        };
        this.tags = [];
        this.init();
    }
    
    init() {
        this.container.innerHTML = `
            <div class="tag-input-container">
                <div class="tag-list" id="tagList"></div>
                <input type="text" class="tag-input" id="tagInput" 
                       placeholder="${this.options.placeholder}">
            </div>
        `;
        
        const input = this.container.querySelector('#tagInput');
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.addTag(input.value.trim());
                input.value = '';
            } else if (e.key === 'Backspace' && input.value === '') {
                this.removeTag(this.tags.length - 1);
            }
        });
    }
    
    addTag(tag) {
        if (!tag) return;
        
        if (!this.options.allowDuplicates && this.tags.includes(tag)) {
            return;
        }
        
        if (this.options.maxTags && this.tags.length >= this.options.maxTags) {
            return;
        }
        
        this.tags.push(tag);
        this.render();
        
        if (this.options.onChange) {
            this.options.onChange(this.tags);
        }
    }
    
    removeTag(index) {
        this.tags.splice(index, 1);
        this.render();
        
        if (this.options.onChange) {
            this.options.onChange(this.tags);
        }
    }
    
    render() {
        const tagList = this.container.querySelector('#tagList');
        tagList.innerHTML = this.tags.map((tag, index) => `
            <span class="tag-item">
                ${tag}
                <button type="button" class="tag-remove" onclick="tagInputInstance.removeTag(${index})">
                    <i class="bi bi-x"></i>
                </button>
            </span>
        `).join('');
    }
    
    getTags() {
        return [...this.tags];
    }
    
    setTags(tags) {
        this.tags = [...tags];
        this.render();
    }
}

// ==================== 导出组件 ====================
if (typeof window !== 'undefined') {
    window.VHComponents = {
        Notification: new NotificationManager(),
        Loading: new LoadingManager(),
        Confirm: ConfirmDialog,
        FileUploader,
        DateRangePicker,
        DataTable,
        TagInput
    };
}

