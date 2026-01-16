/**
 * 高德地图行政区划选择器组件
 * 维海科技信息化管理平台
 * 版本: 1.0
 * 
 * 使用方法：
 * const selector = new AmapDistrictSelector({
 *     provinceSelectId: 'provinceSelect',
 *     citySelectId: 'citySelect',
 *     districtSelectId: 'districtSelect',
 *     addressFieldId: 'projectAddressField',
 *     detailInputId: 'addressDetailInput',
 *     apiBaseUrl: '/api/customer/districts/'
 * });
 * selector.init();
 */

class AmapDistrictSelector {
    /**
     * 构造函数
     * @param {Object} options 配置选项
     * @param {string} options.provinceSelectId - 省份选择框ID
     * @param {string} options.citySelectId - 城市选择框ID
     * @param {string} options.districtSelectId - 区县选择框ID
     * @param {string} options.addressFieldId - 地址隐藏字段ID（用于存储完整地址）
     * @param {string} options.detailInputId - 详细地址输入框ID（可选）
     * @param {string} options.apiBaseUrl - API基础URL（默认：'/api/customer/districts/'）
     * @param {boolean} options.autoUpdateAddress - 是否自动更新地址字段（默认：true）
     * @param {boolean} options.enableLogging - 是否启用日志（默认：false）
     */
    constructor(options = {}) {
        // 默认配置
        this.config = {
            provinceSelectId: options.provinceSelectId || 'provinceSelect',
            citySelectId: options.citySelectId || 'citySelect',
            districtSelectId: options.districtSelectId || 'districtSelect',
            addressFieldId: options.addressFieldId || 'projectAddressField',
            detailInputId: options.detailInputId || 'addressDetailInput',
            apiBaseUrl: options.apiBaseUrl || '/api/customer/districts/',
            autoUpdateAddress: options.autoUpdateAddress !== false,
            enableLogging: options.enableLogging || false
        };
        
        // DOM元素引用
        this.provinceSelect = null;
        this.citySelect = null;
        this.districtSelect = null;
        this.addressField = null;
        this.detailInput = null;
        
        // 选中的值
        this.selectedProvince = null;
        this.selectedCity = null;
        this.selectedDistrict = null;
        
        // 省份排序配置（直辖市和特别行政区排在前面）
        this.specialProvinces = ['北京市', '天津市', '上海市', '重庆市', '香港特别行政区', '澳门特别行政区'];
    }
    
    /**
     * 初始化组件
     */
    init() {
        // 获取DOM元素
        this.provinceSelect = document.getElementById(this.config.provinceSelectId);
        this.citySelect = document.getElementById(this.config.citySelectId);
        this.districtSelect = document.getElementById(this.config.districtSelectId);
        this.addressField = document.getElementById(this.config.addressFieldId);
        this.detailInput = this.config.detailInputId ? document.getElementById(this.config.detailInputId) : null;
        
        // 检查必需元素
        if (!this.provinceSelect || !this.citySelect || !this.districtSelect || !this.addressField) {
            console.error('AmapDistrictSelector: 缺少必需的DOM元素');
            return;
        }
        
        // 绑定事件
        this.bindEvents();
        
        // 加载省份列表
        this.loadProvinces();
    }
    
    /**
     * 绑定事件监听器
     */
    bindEvents() {
        // 省份选择变化
        this.provinceSelect.addEventListener('change', () => {
            const selectedOption = this.provinceSelect.options[this.provinceSelect.selectedIndex];
            this.selectedProvince = selectedOption.dataset.name || '';
            this.selectedCity = null;
            this.selectedDistrict = null;
            this.loadCities(this.provinceSelect.value, this.selectedProvince);
            if (this.config.autoUpdateAddress) {
                this.updateAddressField();
            }
        });
        
        // 城市选择变化
        this.citySelect.addEventListener('change', () => {
            const selectedOption = this.citySelect.options[this.citySelect.selectedIndex];
            this.selectedCity = selectedOption.dataset.name || '';
            this.selectedDistrict = null;
            this.loadDistricts(this.citySelect.value, this.selectedCity);
            if (this.config.autoUpdateAddress) {
                this.updateAddressField();
            }
        });
        
        // 区县选择变化
        this.districtSelect.addEventListener('change', () => {
            const selectedOption = this.districtSelect.options[this.districtSelect.selectedIndex];
            this.selectedDistrict = selectedOption.dataset.name || '';
            if (this.config.autoUpdateAddress) {
                this.updateAddressField();
            }
        });
        
        // 详细地址输入变化
        if (this.detailInput) {
            this.detailInput.addEventListener('input', () => {
                if (this.config.autoUpdateAddress) {
                    this.updateAddressField();
                }
            });
        }
    }
    
    /**
     * 加载省份列表
     */
    async loadProvinces() {
        try {
            const response = await fetch(`${this.config.apiBaseUrl}?keywords=&level=province&subdistrict=0`);
            const data = await response.json();
            
            if (this.config.enableLogging) {
                console.log('省份数据响应:', data);
                console.log('省份数量:', data.districts ? data.districts.length : 0);
            }
            
            if (data.success && data.districts && data.districts.length > 0) {
                // 如果返回的省份数量少于30个，尝试使用国家级别查询
                if (data.districts.length < 30) {
                    if (this.config.enableLogging) {
                        console.warn(`只返回${data.districts.length}个省份，尝试使用国家级别查询`);
                    }
                    try {
                        const countryResponse = await fetch(`${this.config.apiBaseUrl}?keywords=中国&level=country&subdistrict=1`);
                        const countryData = await countryResponse.json();
                        if (countryData.success && countryData.districts && countryData.districts.length > 0) {
                            const country = countryData.districts[0];
                            if (country.districts && country.districts.length > data.districts.length) {
                                if (this.config.enableLogging) {
                                    console.log(`使用国家级别查询成功，获取${country.districts.length}个省份`);
                                }
                                data.districts = country.districts;
                            }
                        }
                    } catch (e) {
                        if (this.config.enableLogging) {
                            console.warn('使用国家级别查询失败:', e);
                        }
                    }
                }
                
                // 填充省份下拉框
                this.provinceSelect.innerHTML = '<option value="">选择省份</option>';
                const sortedProvinces = this.sortProvinces(data.districts);
                
                sortedProvinces.forEach(province => {
                    const opt = document.createElement('option');
                    opt.value = province.adcode;
                    opt.textContent = province.name;
                    opt.dataset.name = province.name;
                    this.provinceSelect.appendChild(opt);
                });
                
                if (this.config.enableLogging) {
                    console.log(`成功加载${sortedProvinces.length}个省份`);
                }
                
                // 初始化地址解析（如果有现有地址）
                this.initializeAddress();
            } else {
                console.error('加载省份数据失败:', data.message || '未知错误');
                this.provinceSelect.innerHTML = '<option value="">加载失败，请刷新页面</option>';
            }
        } catch (error) {
            console.error('加载省份数据异常:', error);
            this.provinceSelect.innerHTML = '<option value="">加载失败，请刷新页面</option>';
        }
    }
    
    /**
     * 加载城市列表
     * @param {string} provinceAdcode - 省份行政区划代码
     * @param {string} provinceName - 省份名称
     */
    async loadCities(provinceAdcode, provinceName) {
        this.citySelect.innerHTML = '<option value="">选择城市</option>';
        this.districtSelect.innerHTML = '<option value="">选择区县</option>';
        
        if (!provinceAdcode) return;
        
        try {
            const response = await fetch(`${this.config.apiBaseUrl}?keywords=${provinceAdcode}&subdistrict=1`);
            const data = await response.json();
            
            if (this.config.enableLogging) {
                console.log('城市数据响应:', data);
            }
            
            if (data.success && data.districts && data.districts.length > 0) {
                data.districts.forEach(city => {
                    const opt = document.createElement('option');
                    opt.value = city.adcode;
                    opt.textContent = city.name;
                    opt.dataset.name = city.name;
                    this.citySelect.appendChild(opt);
                });
            } else {
                console.error('加载城市数据失败:', data.message || '未知错误');
                this.citySelect.innerHTML = '<option value="">加载失败</option>';
            }
        } catch (error) {
            console.error('加载城市数据异常:', error);
            this.citySelect.innerHTML = '<option value="">加载失败</option>';
        }
    }
    
    /**
     * 加载区县列表
     * @param {string} cityAdcode - 城市行政区划代码
     * @param {string} cityName - 城市名称
     */
    async loadDistricts(cityAdcode, cityName) {
        this.districtSelect.innerHTML = '<option value="">选择区县</option>';
        
        if (!cityAdcode) return;
        
        try {
            const response = await fetch(`${this.config.apiBaseUrl}?keywords=${cityAdcode}&subdistrict=1`);
            const data = await response.json();
            
            if (this.config.enableLogging) {
                console.log('区县数据响应:', data);
            }
            
            if (data.success && data.districts && data.districts.length > 0) {
                data.districts.forEach(district => {
                    const opt = document.createElement('option');
                    opt.value = district.adcode;
                    opt.textContent = district.name;
                    opt.dataset.name = district.name;
                    this.districtSelect.appendChild(opt);
                });
            } else {
                console.error('加载区县数据失败:', data.message || '未知错误');
                this.districtSelect.innerHTML = '<option value="">加载失败</option>';
            }
        } catch (error) {
            console.error('加载区县数据异常:', error);
            this.districtSelect.innerHTML = '<option value="">加载失败</option>';
        }
    }
    
    /**
     * 更新地址字段
     */
    updateAddressField() {
        const parts = [];
        if (this.selectedProvince) parts.push(this.selectedProvince);
        if (this.selectedCity) parts.push(this.selectedCity);
        if (this.selectedDistrict) parts.push(this.selectedDistrict);
        
        const detail = this.detailInput ? this.detailInput.value.trim() : '';
        if (detail) parts.push(detail);
        
        if (this.addressField) {
            this.addressField.value = parts.join(' ');
        }
    }
    
    /**
     * 初始化地址解析（如果有现有地址）
     */
    initializeAddress() {
        if (!this.addressField) return;
        
        const initial = this.addressField.value.trim();
        if (!initial) return;
        
        // 简单的地址解析：尝试匹配省份、城市、区县
        const parts = initial.split(/\s+/);
        if (parts.length >= 3) {
            // 尝试匹配省份
            const provinceOptions = Array.from(this.provinceSelect.options);
            const matchedProvince = provinceOptions.find(opt => 
                parts[0] && opt.textContent.includes(parts[0])
            );
            
            if (matchedProvince) {
                this.provinceSelect.value = matchedProvince.value;
                this.selectedProvince = matchedProvince.dataset.name;
                
                this.loadCities(matchedProvince.value, matchedProvince.dataset.name).then(() => {
                    // 尝试匹配城市
                    setTimeout(() => {
                        const cityOptions = Array.from(this.citySelect.options);
                        const matchedCity = cityOptions.find(opt => 
                            parts[1] && opt.textContent.includes(parts[1])
                        );
                        
                        if (matchedCity) {
                            this.citySelect.value = matchedCity.value;
                            this.selectedCity = matchedCity.dataset.name;
                            
                            this.loadDistricts(matchedCity.value, matchedCity.dataset.name).then(() => {
                                // 尝试匹配区县
                                setTimeout(() => {
                                    const districtOptions = Array.from(this.districtSelect.options);
                                    const matchedDistrict = districtOptions.find(opt => 
                                        parts[2] && opt.textContent.includes(parts[2])
                                    );
                                    
                                    if (matchedDistrict) {
                                        this.districtSelect.value = matchedDistrict.value;
                                        this.selectedDistrict = matchedDistrict.dataset.name;
                                    }
                                    
                                    // 剩余部分作为详细地址
                                    if (parts.length > 3 && this.detailInput) {
                                        this.detailInput.value = parts.slice(3).join(' ');
                                    }
                                }, 100);
                            });
                        }
                    }, 100);
                });
            }
        }
    }
    
    /**
     * 对省份进行排序
     * @param {Array} provinces - 省份数组
     * @returns {Array} 排序后的省份数组
     */
    sortProvinces(provinces) {
        return [...provinces].sort((a, b) => {
            const aIndex = this.specialProvinces.indexOf(a.name);
            const bIndex = this.specialProvinces.indexOf(b.name);
            
            if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;
            if (aIndex !== -1) return -1;
            if (bIndex !== -1) return 1;
            
            return a.name.localeCompare(b.name, 'zh-CN');
        });
    }
    
    /**
     * 获取当前选中的完整地址
     * @returns {string} 完整地址
     */
    getFullAddress() {
        return this.addressField ? this.addressField.value : '';
    }
    
    /**
     * 设置地址（用于编辑场景）
     * @param {string} address - 完整地址字符串
     */
    setAddress(address) {
        if (this.addressField) {
            this.addressField.value = address || '';
            this.initializeAddress();
        }
    }
    
    /**
     * 重置选择器
     */
    reset() {
        this.provinceSelect.value = '';
        this.citySelect.innerHTML = '<option value="">选择城市</option>';
        this.districtSelect.innerHTML = '<option value="">选择区县</option>';
        this.selectedProvince = null;
        this.selectedCity = null;
        this.selectedDistrict = null;
        if (this.detailInput) {
            this.detailInput.value = '';
        }
        if (this.addressField) {
            this.addressField.value = '';
        }
    }
}

// 导出类（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AmapDistrictSelector;
}

