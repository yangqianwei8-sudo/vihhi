/**
 * 布局诊断脚本
 * 在浏览器控制台中运行此脚本，检查两栏布局的各种属性
 * 使用方法：在控制台中输入 layoutDiagnostic() 或直接运行此脚本
 */

(function() {
    'use strict';
    
    function layoutDiagnostic() {
        console.log('========================================');
        console.log('两栏布局诊断报告');
        console.log('========================================\n');
        
        // 1. 检查视口和窗口尺寸
        console.log('【1. 视口和窗口尺寸】');
        console.log('  - window.innerHeight:', window.innerHeight, 'px');
        console.log('  - window.innerWidth:', window.innerWidth, 'px');
        console.log('  - document.documentElement.clientHeight:', document.documentElement.clientHeight, 'px');
        console.log('  - document.documentElement.clientWidth:', document.documentElement.clientWidth, 'px');
        console.log('  - document.body.scrollHeight:', document.body.scrollHeight, 'px');
        console.log('  - document.body.clientHeight:', document.body.clientHeight, 'px');
        console.log('');
        
        // 2. 检查顶部导航栏
        console.log('【2. 顶部导航栏】');
        const navbar = document.querySelector('.navbar') || document.querySelector('nav') || document.querySelector('header');
        let navbarRect = null;
        let navbarHeight = 56; // 默认高度
        if (navbar) {
            navbarRect = navbar.getBoundingClientRect();
            navbarHeight = navbarRect.height;
            const navbarStyle = window.getComputedStyle(navbar);
            console.log('  ✓ 找到导航栏元素');
            console.log('  - 元素:', navbar.tagName, navbar.className);
            console.log('  - 高度:', navbarRect.height, 'px');
            console.log('  - 宽度:', navbarRect.width, 'px');
            console.log('  - top:', navbarRect.top, 'px');
            console.log('  - position:', navbarStyle.position);
            console.log('  - z-index:', navbarStyle.zIndex);
        } else {
            console.log('  ✗ 未找到导航栏元素 (.navbar, nav, header)');
            console.log('  - 使用默认高度:', navbarHeight, 'px');
        }
        console.log('');
        
        // 3. 检查 .two-column-layout
        console.log('【3. .two-column-layout 容器】');
        let twoColLayout = document.querySelector('.two-column-layout');
        if (twoColLayout) {
            const layoutRect = twoColLayout.getBoundingClientRect();
            const layoutStyle = window.getComputedStyle(twoColLayout);
            console.log('  ✓ 找到 .two-column-layout');
            console.log('  - 高度:', layoutRect.height, 'px');
            console.log('  - 宽度:', layoutRect.width, 'px');
            console.log('  - top:', layoutRect.top, 'px');
            console.log('  - left:', layoutRect.left, 'px');
            console.log('  - display:', layoutStyle.display);
            console.log('  - flex-direction:', layoutStyle.flexDirection);
            console.log('  - align-items:', layoutStyle.alignItems);
            console.log('  - min-height:', layoutStyle.minHeight);
            console.log('  - height:', layoutStyle.height);
            console.log('  - margin-top:', layoutStyle.marginTop);
            console.log('  - margin-bottom:', layoutStyle.marginBottom);
            console.log('  - padding-top:', layoutStyle.paddingTop);
            console.log('  - padding-bottom:', layoutStyle.paddingBottom);
            console.log('  - overflow:', layoutStyle.overflow);
            console.log('  - 计算后的 min-height:', layoutStyle.minHeight);
            console.log('  - 计算后的 height:', layoutStyle.height);
            
            // 检查子元素
            const children = Array.from(twoColLayout.children);
            console.log('  - 子元素数量:', children.length);
            children.forEach((child, index) => {
                const childRect = child.getBoundingClientRect();
                const childStyle = window.getComputedStyle(child);
                const relativeTop = childRect.top - layoutRect.top;
                console.log(`  - 子元素 ${index + 1}:`);
                console.log('    * 标签:', child.tagName);
                console.log('    * 类名:', child.className);
                console.log('    * 相对于父容器的 top:', relativeTop, 'px');
                console.log('    * height:', childRect.height, 'px');
                console.log('    * display:', childStyle.display);
                console.log('    * position:', childStyle.position);
                console.log('    * visibility:', childStyle.visibility);
                if (Math.abs(relativeTop) > 10 && childRect.height > 10) {
                    console.log('    ⚠ 警告：此子元素可能占用了空间，导致布局问题');
                }
            });
            
            // 检查 .two-col-main 是否在子元素中
            const mainInChildren = children.find(child => child.classList.contains('two-col-main'));
            if (!mainInChildren) {
                console.log('  ⚠ 警告：.two-col-main 不在 .two-column-layout 的直接子元素中');
                console.log('  - 尝试查找 .two-col-main 元素...');
                const mainElement = document.querySelector('.two-col-main');
                if (mainElement) {
                    console.log('  - 找到 .two-col-main，检查其父元素:');
                    let parent = mainElement.parentElement;
                    let level = 0;
                    while (parent && level < 5) {
                        console.log(`    * 第 ${level + 1} 层父元素:`, parent.tagName, parent.className);
                        if (parent === twoColLayout) {
                            console.log('    ✓ .two-col-main 在 .two-column-layout 内（但不是直接子元素）');
                            break;
                        }
                        parent = parent.parentElement;
                        level++;
                    }
                }
            }
            
            // 计算预期高度
            const expectedHeight = window.innerHeight - navbarHeight;
            console.log('  - 预期高度 (100vh - 顶部栏):', expectedHeight, 'px');
            console.log('  - 高度差异:', layoutRect.height - expectedHeight, 'px');
        } else {
            console.log('  ✗ 未找到 .two-column-layout');
        }
        console.log('');
        
        // 4. 检查 .two-col-sidebar
        console.log('【4. .two-col-sidebar 侧边栏】');
        const sidebar = document.querySelector('.two-col-sidebar');
        if (sidebar) {
            const sidebarRect = sidebar.getBoundingClientRect();
            const sidebarStyle = window.getComputedStyle(sidebar);
            console.log('  ✓ 找到 .two-col-sidebar');
            console.log('  - 高度:', sidebarRect.height, 'px');
            console.log('  - 宽度:', sidebarRect.width, 'px');
            console.log('  - top:', sidebarRect.top, 'px');
            console.log('  - left:', sidebarRect.left, 'px');
            console.log('  - position:', sidebarStyle.position);
            console.log('  - z-index:', sidebarStyle.zIndex);
            console.log('  - --sidebar-width:', sidebarStyle.getPropertyValue('--sidebar-width') || '224px (默认)');
        } else {
            console.log('  ✗ 未找到 .two-col-sidebar');
        }
        console.log('');
        
        // 5. 检查 .two-col-main
        console.log('【5. .two-col-main 主内容区】');
        const twoColMain = document.querySelector('.two-col-main');
        if (twoColMain) {
            const mainRect = twoColMain.getBoundingClientRect();
            const mainStyle = window.getComputedStyle(twoColMain);
            // 确保获取正确的父容器（.two-column-layout）
            // 优先使用之前找到的 twoColLayout，确保是同一个元素
            let parentLayout = twoColLayout;
            // 如果 twoColLayout 不存在，尝试从 twoColMain 向上查找
            if (!parentLayout) {
                parentLayout = twoColMain.parentElement;
                while (parentLayout && !parentLayout.classList.contains('two-column-layout')) {
                    parentLayout = parentLayout.parentElement;
                }
            }
            // 验证父容器是否正确
            if (parentLayout && !parentLayout.classList.contains('two-column-layout')) {
                console.log('  ⚠ 警告：父容器不是 .two-column-layout');
                console.log('  - 父容器标签:', parentLayout.tagName);
                console.log('  - 父容器类名:', parentLayout.className);
            }
            const parentRect = parentLayout ? parentLayout.getBoundingClientRect() : null;
            
            console.log('  ✓ 找到 .two-col-main');
            console.log('  - 高度:', mainRect.height, 'px');
            console.log('  - 宽度:', mainRect.width, 'px');
            console.log('  - top (绝对位置):', mainRect.top, 'px');
            console.log('  - left:', mainRect.left, 'px');
            console.log('  - display:', mainStyle.display);
            console.log('  - position:', mainStyle.position);
            console.log('  - flex:', mainStyle.flex);
            console.log('  - flex-direction:', mainStyle.flexDirection);
            console.log('  - min-height:', mainStyle.minHeight);
            console.log('  - height:', mainStyle.height);
            console.log('  - margin-left:', mainStyle.marginLeft);
            console.log('  - margin-top:', mainStyle.marginTop);
            console.log('  - padding-top:', mainStyle.paddingTop);
            console.log('  - overflow-y:', mainStyle.overflowY);
            console.log('  - overflow-x:', mainStyle.overflowX);
            
            if (parentLayout && parentRect) {
                const relativeTop = mainRect.top - parentRect.top;
                const parentStyle = window.getComputedStyle(parentLayout);
                console.log('  - 父容器 (.two-column-layout) 信息:');
                console.log('    * 父容器 top (相对于视口):', parentRect.top, 'px');
                console.log('    * 父容器 bottom (相对于视口):', parentRect.bottom, 'px');
                console.log('    * 父容器 height:', parentRect.height, 'px');
                console.log('    * 父容器 display:', parentStyle.display);
                console.log('    * 父容器 flex-direction:', parentStyle.flexDirection);
                console.log('    * 父容器 align-items:', parentStyle.alignItems);
                console.log('    * 父容器 position:', parentStyle.position);
                console.log('    * 父容器 margin-top:', parentStyle.marginTop);
                console.log('    * 父容器 computed height:', parentStyle.height);
                console.log('  - .two-col-main 相对于父容器的 top:', relativeTop, 'px');
                console.log('  - .two-col-main 应该在父容器内的位置: 接近 0px');
                if (Math.abs(relativeTop) > 10) {
                    console.log('  ⚠ 警告：.two-col-main 相对于父容器有', relativeTop, 'px 的偏移，应该接近 0px');
                    console.log('  ⚠ 可能原因：');
                    console.log('    1. .two-col-main 被绝对定位到了错误的位置');
                    console.log('    2. 父容器的高度计算有问题');
                    console.log('    3. 有其他 CSS 或 JavaScript 影响了布局');
                    console.log('    4. Flex 布局的对齐方式有问题');
                } else {
                    console.log('  ✓ .two-col-main 相对于父容器的位置正确');
                }
            } else {
                console.log('  ⚠ 无法获取父容器信息');
                if (twoColMain.parentElement) {
                    console.log('  - 父元素标签:', twoColMain.parentElement.tagName);
                    console.log('  - 父元素类名:', twoColMain.parentElement.className);
                }
            }
            
            // 计算预期高度
            const expectedMainHeight = window.innerHeight - navbarHeight;
            console.log('  - 预期高度 (100vh - 顶部栏):', expectedMainHeight, 'px');
            console.log('  - 高度差异:', mainRect.height - expectedMainHeight, 'px');
            
            // 检查预期位置
            const expectedTop = navbarHeight + (parentRect ? parentRect.top : 0);
            console.log('  - 预期 top 位置 (导航栏高度 + 父容器top):', expectedTop, 'px');
            console.log('  - 实际 top 位置:', mainRect.top, 'px');
            console.log('  - top 位置差异:', mainRect.top - expectedTop, 'px');
        } else {
            console.log('  ✗ 未找到 .two-col-main');
        }
        console.log('');
        
        // 6. 检查 .two-col-content
        console.log('【6. .two-col-content 内容区】');
        const twoColContent = document.querySelector('.two-col-content');
        if (twoColContent) {
            const contentRect = twoColContent.getBoundingClientRect();
            const contentStyle = window.getComputedStyle(twoColContent);
            console.log('  ✓ 找到 .two-col-content');
            console.log('  - 高度:', contentRect.height, 'px');
            console.log('  - 宽度:', contentRect.width, 'px');
            console.log('  - top:', contentRect.top, 'px');
            console.log('  - left:', contentRect.left, 'px');
            console.log('  - display:', contentStyle.display);
            console.log('  - min-height:', contentStyle.minHeight);
            console.log('  - padding:', contentStyle.padding);
            console.log('  - overflow:', contentStyle.overflow);
        } else {
            console.log('  ✗ 未找到 .two-col-content');
        }
        console.log('');
        
        // 7. 检查页面标题区域
        console.log('【7. 页面标题区域】');
        const pageHeader = document.querySelector('.two-col-content > .d-flex.align-items-end.justify-content-between.mb-4');
        if (pageHeader) {
            const headerRect = pageHeader.getBoundingClientRect();
            const headerStyle = window.getComputedStyle(pageHeader);
            console.log('  ✓ 找到页面标题区域');
            console.log('  - 高度:', headerRect.height, 'px');
            console.log('  - top:', headerRect.top, 'px');
            console.log('  - margin-top:', headerStyle.marginTop);
            console.log('  - padding-top:', headerStyle.paddingTop);
            console.log('  - padding-bottom:', headerStyle.paddingBottom);
        } else {
            console.log('  ✗ 未找到页面标题区域');
        }
        console.log('');
        
        // 8. 检查 body 和 html 样式
        console.log('【8. body 和 html 样式】');
        const bodyStyle = window.getComputedStyle(document.body);
        const htmlStyle = window.getComputedStyle(document.documentElement);
        console.log('  - body.height:', bodyStyle.height);
        console.log('  - body.overflow-y:', bodyStyle.overflowY);
        console.log('  - body.margin:', bodyStyle.margin);
        console.log('  - body.padding:', bodyStyle.padding);
        console.log('  - html.height:', htmlStyle.height);
        console.log('  - html.overflow-y:', htmlStyle.overflowY);
        console.log('  - html.margin:', htmlStyle.margin);
        console.log('  - html.padding:', htmlStyle.padding);
        console.log('');
        
        // 9. 检查空白区域
        console.log('【9. 空白区域分析】');
        if (navbar && twoColLayout && navbarRect) {
            const navbarBottom = navbarRect.bottom;
            const layoutTop = twoColLayout.getBoundingClientRect().top;
            const gap = layoutTop - navbarBottom;
            console.log('  - 导航栏底部位置:', navbarBottom, 'px');
            console.log('  - 布局容器顶部位置:', layoutTop, 'px');
            console.log('  - 两者之间的空白:', gap, 'px');
            if (gap > 5) {
                console.log('  ⚠ 警告：导航栏和布局容器之间存在', gap, 'px 的空白');
            } else {
                console.log('  ✓ 导航栏和布局容器之间没有明显空白');
            }
        } else if (twoColLayout) {
            const layoutTop = twoColLayout.getBoundingClientRect().top;
            console.log('  - 布局容器顶部位置:', layoutTop, 'px');
            if (layoutTop > navbarHeight + 5) {
                console.log('  ⚠ 警告：布局容器顶部位置异常，可能存在空白');
            }
        }
        
        if (twoColMain && twoColContent) {
            const mainTop = twoColMain.getBoundingClientRect().top;
            const contentTop = twoColContent.getBoundingClientRect().top;
            const contentGap = contentTop - mainTop;
            console.log('  - 主内容区顶部位置:', mainTop, 'px');
            console.log('  - 内容区顶部位置:', contentTop, 'px');
            console.log('  - 两者之间的空白:', contentGap, 'px');
        }
        console.log('');
        
        // 10. 总结和建议
        console.log('【10. 诊断总结】');
        const issues = [];
        
        if (!navbar) {
            issues.push('  ✗ 未找到顶部导航栏元素');
        }
        
        if (!twoColLayout) {
            issues.push('  ✗ 未找到 .two-column-layout 容器');
        } else {
            const layoutRect = twoColLayout.getBoundingClientRect();
            const expectedHeight = window.innerHeight - navbarHeight;
            if (Math.abs(layoutRect.height - expectedHeight) > 10) {
                issues.push('  ⚠ .two-column-layout 高度不正确（预期: ' + expectedHeight + 'px, 实际: ' + layoutRect.height + 'px）');
            }
        }
        
        if (!twoColMain) {
            issues.push('  ✗ 未找到 .two-col-main 容器');
        } else {
            const mainRect = twoColMain.getBoundingClientRect();
            const mainStyle = window.getComputedStyle(twoColMain);
            if (mainStyle.display !== 'flex') {
                issues.push('  ⚠ .two-col-main 的 display 不是 flex（当前: ' + mainStyle.display + '）');
            }
        }
        
        if (!sidebar) {
            issues.push('  ⚠ 未找到 .two-col-sidebar 侧边栏（如果页面不需要侧边栏，可忽略）');
        }
        
        if (issues.length === 0) {
            console.log('  ✓ 未发现明显问题');
        } else {
            console.log('  发现以下问题：');
            issues.forEach(issue => console.log(issue));
        }
        
        console.log('\n========================================');
        console.log('诊断完成');
        console.log('========================================');
        
        // 返回诊断结果对象
        return {
            viewport: {
                innerHeight: window.innerHeight,
                innerWidth: window.innerWidth,
                bodyHeight: document.body.scrollHeight
            },
            navbar: navbar && navbarRect ? {
                found: true,
                height: navbarRect.height,
                position: window.getComputedStyle(navbar).position
            } : { found: false, height: navbarHeight },
            twoColumnLayout: twoColLayout ? {
                found: true,
                height: twoColLayout.getBoundingClientRect().height,
                top: twoColLayout.getBoundingClientRect().top,
                computedHeight: window.getComputedStyle(twoColLayout).height,
                computedMinHeight: window.getComputedStyle(twoColLayout).minHeight
            } : { found: false },
            twoColMain: twoColMain ? {
                found: true,
                height: twoColMain.getBoundingClientRect().height,
                display: window.getComputedStyle(twoColMain).display,
                overflowY: window.getComputedStyle(twoColMain).overflowY
            } : { found: false },
            sidebar: sidebar ? {
                found: true,
                height: sidebar.getBoundingClientRect().height,
                width: sidebar.getBoundingClientRect().width
            } : { found: false },
            issues: issues
        };
    }
    
    // 将函数暴露到全局作用域
    window.layoutDiagnostic = layoutDiagnostic;
    
    // 如果脚本直接运行，自动执行诊断
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            console.log('布局诊断脚本已加载，在控制台输入 layoutDiagnostic() 运行诊断');
        });
    } else {
        console.log('布局诊断脚本已加载，在控制台输入 layoutDiagnostic() 运行诊断');
    }
})();
