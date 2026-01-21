/**
 * 通知API测试脚本
 * 
 * 在浏览器控制台中运行此脚本来测试通知API
 * 
 * 使用方法：
 * 1. 打开浏览器开发者工具（F12）
 * 2. 切换到 Console 标签
 * 3. 复制粘贴下面的代码并运行
 */

// ========== 方法1：使用 fetch（支持 session 和 token） ==========
async function testNotificationAPI() {
  console.log('开始测试通知API...');
  
  // 获取API基础URL
  const getBaseURL = () => {
    // 生产环境
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      return '/api';
    }
    // 开发环境
    return 'http://localhost:8001/api';
  };
  
  const baseURL = getBaseURL();
  const token = localStorage.getItem('token');
  
  // 构建请求配置
  const fetchOptions = {
    method: 'GET',
    credentials: 'include', // 支持 session/cookie
    headers: {
      'Content-Type': 'application/json'
    }
  };
  
  // 如果有token，添加Authorization头
  if (token) {
    fetchOptions.headers['Authorization'] = `Bearer ${token}`;
  }
  
  try {
    // 1. 测试获取通知列表
    console.log('\n【1. 测试获取通知列表】');
    const response = await fetch(`${baseURL}/plan/notifications/`, fetchOptions);
    console.log('响应状态:', response.status, response.statusText);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('请求失败:', errorText);
      return;
    }
    
    const data = await response.json();
    console.log('响应数据:', data);
    
    if (Array.isArray(data)) {
      console.log(`✓ 找到 ${data.length} 条通知`);
      if (data.length > 0) {
        console.log('前3条通知:');
        data.slice(0, 3).forEach((n, i) => {
          console.log(`  ${i + 1}. ID: ${n.id}, 标题: ${n.title}, 已读: ${n.is_read}`);
        });
      }
    } else if (data.results) {
      console.log(`✓ 找到 ${data.results.length} 条通知（分页）`);
    } else {
      console.log('⚠️  响应格式异常:', data);
    }
    
    // 2. 测试获取未读通知数量
    console.log('\n【2. 测试获取未读通知数量】');
    const countResponse = await fetch(`${baseURL}/plan/notifications/unread-count/`, fetchOptions);
    if (countResponse.ok) {
      const countData = await countResponse.json();
      console.log('未读通知数:', countData.unread);
    } else {
      console.error('获取未读数失败:', countResponse.status);
    }
    
    // 3. 测试过滤未读通知
    console.log('\n【3. 测试过滤未读通知】');
    const unreadResponse = await fetch(`${baseURL}/plan/notifications/?is_read=0`, fetchOptions);
    if (unreadResponse.ok) {
      const unreadData = await unreadResponse.json();
      if (Array.isArray(unreadData)) {
        console.log(`✓ 找到 ${unreadData.length} 条未读通知`);
      } else {
        console.log('未读通知数据:', unreadData);
      }
    }
    
    console.log('\n✓ 测试完成！');
    
  } catch (error) {
    console.error('❌ 测试失败:', error);
    console.error('错误详情:', error.message);
  }
}

// ========== 方法2：使用 axios（如果页面已加载 axios） ==========
async function testNotificationAPIWithAxios() {
  console.log('使用 axios 测试通知API...');
  
  // 检查是否已加载 axios
  if (typeof axios === 'undefined') {
    console.error('❌ 页面未加载 axios，请使用方法1（fetch）');
    return;
  }
  
  try {
    const baseURL = window.location.hostname !== 'localhost' ? '/api' : 'http://localhost:8001/api';
    
    // 获取通知列表
    const response = await axios.get(`${baseURL}/plan/notifications/`, {
      withCredentials: true
    });
    
    console.log('通知数据:', response.data);
    console.log('通知数量:', Array.isArray(response.data) ? response.data.length : response.data.results?.length || 0);
    
    // 获取未读数
    const countResponse = await axios.get(`${baseURL}/plan/notifications/unread-count/`, {
      withCredentials: true
    });
    console.log('未读通知数:', countResponse.data.unread);
    
  } catch (error) {
    console.error('❌ axios 测试失败:', error);
    if (error.response) {
      console.error('响应状态:', error.response.status);
      console.error('响应数据:', error.response.data);
    }
  }
}

// ========== 执行测试 ==========
// 自动运行测试
testNotificationAPI();

// 如果需要使用 axios，取消下面的注释
// testNotificationAPIWithAxios();
