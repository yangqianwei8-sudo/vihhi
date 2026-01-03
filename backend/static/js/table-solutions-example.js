/**
 * 前端表格解决方案示例
 * 根据项目需求选择合适的表格库
 */

// ==================== 方案 1: AG Grid (推荐 - 企业级) ====================
/**
 * AG Grid - 最强大的企业级表格解决方案
 * 
 * 优势：
 * - 支持虚拟滚动，可处理百万级数据
 * - 丰富的功能：分组、聚合、透视表、Excel导出
 * - 性能优异，适合复杂业务场景
 * - 支持树形数据、主从表等复杂结构
 * 
 * 集成方式：
 * 1. 在模板中引入：
 *    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-community@31.0.0/styles/ag-grid.css">
 *    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-community@31.0.0/styles/ag-theme-alpine.css">
 *    <script src="https://cdn.jsdelivr.net/npm/ag-grid-community@31.0.0/dist/ag-grid-community.min.js"></script>
 * 
 * 2. 初始化表格：
 */
function initAGGrid(containerId, data, columns) {
    const gridOptions = {
        columnDefs: columns,
        rowData: data,
        defaultColDef: {
            sortable: true,
            filter: true,
            resizable: true,
        },
        pagination: true,
        paginationPageSize: 20,
        enableRangeSelection: true,
        rowSelection: 'multiple',
        suppressRowClickSelection: true,
        // 虚拟滚动（大数据量时）
        rowBuffer: 10,
        // Excel导出
        enableExcelExport: true,
        // 列分组
        enableRangeHandle: true,
        // 响应式布局
        domLayout: 'autoHeight',
    };
    
    const gridDiv = document.querySelector('#' + containerId);
    new agGrid.Grid(gridDiv, gridOptions);
    
    return gridOptions.api;
}

// ==================== 方案 2: Tabulator (推荐 - 轻量级) ====================
/**
 * Tabulator - 功能强大且轻量级的表格库
 * 
 * 优势：
 * - 轻量级，易于集成
 * - 功能丰富：虚拟DOM、分组、聚合、导出
 * - 完全免费开源
 * - 与Bootstrap兼容性好
 * 
 * 集成方式：
 * 1. 在模板中引入：
 *    <link href="https://unpkg.com/tabulator-tables@5.5.2/dist/css/tabulator_bootstrap5.min.css" rel="stylesheet">
 *    <script type="text/javascript" src="https://unpkg.com/tabulator-tables@5.5.2/dist/js/tabulator.min.js"></script>
 * 
 * 2. 初始化表格：
 */
function initTabulator(containerId, data, columns) {
    const table = new Tabulator('#' + containerId, {
        data: data,
        columns: columns,
        layout: "fitColumns",
        pagination: true,
        paginationSize: 20,
        paginationSizeSelector: [10, 20, 50, 100],
        movableColumns: true,
        resizableColumns: true,
        tooltips: true,
        // 虚拟DOM（大数据量时）
        virtualDom: true,
        virtualDomBuffer: 300,
        // 导出功能
        downloadConfig: {
            columnHeaders: true,
            columnGroups: true,
            rowGroups: true,
            columnCalcs: true,
            dataTree: true,
        },
        // 响应式布局
        responsiveLayout: "hide",
        // 列分组
        groupBy: function(data) {
            // 示例：按状态分组
            return data.status;
        },
        // 聚合函数
        groupHeader: function(value, count, data, group) {
            return value + " <span style='color:#d00; margin-left:10px;'>(" + count + " 项)</span>";
        },
    });
    
    return table;
}

// ==================== 方案 3: DataTables (传统方案) ====================
/**
 * DataTables - 经典的表格增强库
 * 
 * 优势：
 * - 成熟稳定，文档完善
 * - 与jQuery集成良好
 * - 插件生态丰富
 * 
 * 集成方式：
 * 1. 在模板中引入：
 *    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/dataTables.bootstrap5.min.css">
 *    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
 *    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
 *    <script src="https://cdn.datatables.net/1.13.7/js/dataTables.bootstrap5.min.js"></script>
 * 
 * 2. 初始化表格：
 */
function initDataTables(containerId, options) {
    const defaultOptions = {
        language: {
            url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/zh-CN.json'
        },
        pageLength: 20,
        lengthMenu: [[10, 20, 50, 100, -1], [10, 20, 50, 100, "全部"]],
        order: [[0, 'desc']],
        responsive: true,
        dom: '<"row"<"col-sm-6"l><"col-sm-6"f>>rt<"row"<"col-sm-6"i><"col-sm-6"p>>',
        ...options
    };
    
    return $('#' + containerId).DataTable(defaultOptions);
}

// ==================== 方案 4: Handsontable (Excel风格) ====================
/**
 * Handsontable - Excel风格的表格编辑器
 * 
 * 优势：
 * - Excel式编辑体验
 * - 支持公式计算
 * - 适合数据录入场景
 * 
 * 集成方式：
 * 1. 在模板中引入：
 *    <script src="https://cdn.jsdelivr.net/npm/handsontable@latest/dist/handsontable.full.min.js"></script>
 *    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/handsontable@latest/dist/handsontable.full.min.css">
 * 
 * 2. 初始化表格：
 */
function initHandsontable(containerId, data, columns) {
    const container = document.getElementById(containerId);
    const hot = new Handsontable(container, {
        data: data,
        columns: columns,
        colHeaders: true,
        rowHeaders: true,
        width: '100%',
        height: 'auto',
        licenseKey: 'non-commercial-and-evaluation', // 非商业用途
        // 公式支持
        formulas: true,
        // 数据验证
        validator: function(value, callback) {
            // 自定义验证逻辑
            callback(true);
        },
        // 复制粘贴
        copyPaste: true,
        // 列宽调整
        manualColumnResize: true,
        // 行高调整
        manualRowResize: true,
    });
    
    return hot;
}

// ==================== 实际使用示例 ====================

/**
 * 示例：在Django模板中使用AG Grid
 */
function exampleAGGridWithDjango() {
    // 从Django后端获取数据
    fetch('/api/customers/')
        .then(response => response.json())
        .then(data => {
            const columnDefs = [
                { field: 'id', headerName: 'ID', width: 80 },
                { field: 'name', headerName: '客户名称', width: 200, filter: 'agTextColumnFilter' },
                { field: 'phone', headerName: '联系电话', width: 150 },
                { field: 'email', headerName: '邮箱', width: 200 },
                { field: 'status', headerName: '状态', width: 120, 
                  cellRenderer: function(params) {
                      const statusMap = {
                          'active': '<span class="badge bg-success">活跃</span>',
                          'inactive': '<span class="badge bg-secondary">非活跃</span>'
                      };
                      return statusMap[params.value] || params.value;
                  }
                },
                { field: 'created_at', headerName: '创建时间', width: 180,
                  valueFormatter: function(params) {
                      return new Date(params.value).toLocaleString('zh-CN');
                  }
                },
                {
                    headerName: '操作',
                    width: 150,
                    cellRenderer: function(params) {
                        return `
                            <button class="btn btn-sm btn-primary" onclick="editCustomer(${params.data.id})">编辑</button>
                            <button class="btn btn-sm btn-danger" onclick="deleteCustomer(${params.data.id})">删除</button>
                        `;
                    }
                }
            ];
            
            initAGGrid('customerGrid', data, columnDefs);
        });
}

/**
 * 示例：在Django模板中使用Tabulator
 */
function exampleTabulatorWithDjango() {
    // 从Django后端获取数据
    fetch('/api/customers/')
        .then(response => response.json())
        .then(data => {
            const columns = [
                {title: "ID", field: "id", width: 80},
                {title: "客户名称", field: "name", width: 200, editor: "input"},
                {title: "联系电话", field: "phone", width: 150, editor: "input"},
                {title: "邮箱", field: "email", width: 200, editor: "input"},
                {title: "状态", field: "status", width: 120,
                 formatter: function(cell, formatterParams) {
                     const statusMap = {
                         'active': '<span class="badge bg-success">活跃</span>',
                         'inactive': '<span class="badge bg-secondary">非活跃</span>'
                     };
                     return statusMap[cell.getValue()] || cell.getValue();
                 }
                },
                {title: "创建时间", field: "created_at", width: 180,
                 formatter: "datetime",
                 formatterParams: {
                     inputFormat: "YYYY-MM-DD HH:mm:ss",
                     outputFormat: "YYYY-MM-DD HH:mm:ss",
                     invalidPlaceholder: "-"
                 }
                },
                {title: "操作", field: "actions", width: 150,
                 formatter: function(cell, formatterParams) {
                     const rowData = cell.getRow().getData();
                     return `
                         <button class="btn btn-sm btn-primary" onclick="editCustomer(${rowData.id})">编辑</button>
                         <button class="btn btn-sm btn-danger" onclick="deleteCustomer(${rowData.id})">删除</button>
                     `;
                 }
                }
            ];
            
            initTabulator('customerTable', data, columns);
        });
}

// ==================== 推荐方案对比 ====================
/**
 * 方案对比：
 * 
 * 1. AG Grid (推荐用于复杂场景)
 *    - 适合：大数据量、复杂交互、企业级应用
 *    - 性能：⭐⭐⭐⭐⭐
 *    - 功能：⭐⭐⭐⭐⭐
 *    - 学习曲线：中等
 *    - 许可证：社区版免费，企业版需付费
 * 
 * 2. Tabulator (推荐用于一般场景)
 *    - 适合：中等数据量、常规表格需求
 *    - 性能：⭐⭐⭐⭐
 *    - 功能：⭐⭐⭐⭐
 *    - 学习曲线：简单
 *    - 许可证：完全免费
 * 
 * 3. DataTables (传统方案)
 *    - 适合：简单表格、传统项目
 *    - 性能：⭐⭐⭐
 *    - 功能：⭐⭐⭐
 *    - 学习曲线：简单
 *    - 许可证：免费
 * 
 * 4. Handsontable (Excel风格)
 *    - 适合：数据录入、Excel式编辑
 *    - 性能：⭐⭐⭐⭐
 *    - 功能：⭐⭐⭐⭐
 *    - 学习曲线：中等
 *    - 许可证：免费版功能有限，完整版需付费
 */

