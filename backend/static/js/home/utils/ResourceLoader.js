/**
 * 统一资源加载器
 * 简化资源回退逻辑
 * 维海科技信息化管理平台
 */
class ResourceLoader {
    /**
     * 加载CSS文件
     * @param {string} href - 主要CSS路径
     * @param {string} fallback - 回退CSS路径
     * @returns {Promise}
     */
    static async loadCSS(href, fallback) {
        return new Promise((resolve) => {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = href;
            
            link.onload = () => resolve();
            link.onerror = () => {
                if (fallback) {
                    link.href = fallback;
                    link.onerror = null;
                    link.onload = () => resolve();
                }
                resolve(); // 即使失败也resolve，避免阻塞
            };
            
            document.head.appendChild(link);
        });
    }
    
    /**
     * 加载JavaScript文件
     * @param {string} src - 主要JS路径
     * @param {string} fallback - 回退JS路径
     * @param {string} globalVar - 全局变量名（用于检测加载成功）
     * @returns {Promise}
     */
    static async loadJS(src, fallback, globalVar = null) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            
            script.onload = () => {
                if (globalVar && window[globalVar]) {
                    resolve(window[globalVar]);
                } else {
                    resolve(true);
                }
            };
            
            script.onerror = () => {
                if (fallback) {
                    script.src = fallback;
                    script.onerror = null;
                    script.onload = () => {
                        if (globalVar && window[globalVar]) {
                            resolve(window[globalVar]);
                        } else {
                            resolve(true);
                        }
                    };
                } else {
                    reject(new Error(`Failed to load script: ${src}`));
                }
            };
            
            document.head.appendChild(script);
        });
    }
    
    /**
     * 预加载资源
     * @param {string} href - 资源路径
     * @param {string} as - 资源类型（style, script, image等）
     */
    static preload(href, as = 'style') {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.href = href;
        link.as = as;
        document.head.appendChild(link);
    }
}

// 兼容CommonJS和ES6模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ResourceLoader;
}


