"""
测试学校管理页面视图 - 直接显示学校列表，绕过所有认证
"""
from django.shortcuts import render
from django.http import HttpResponse
import traceback


def test_school_list(request):
    """测试学校列表页面 - 直接返回简单HTML，确保能访问"""
    # 先返回一个简单的测试页面，确认路由工作
    simple_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>学校管理测试页面</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f0f0f0; }
            .container { background: white; padding: 30px; border-radius: 8px; max-width: 800px; margin: 0 auto; }
            h1 { color: #667eea; border-bottom: 3px solid #667eea; padding-bottom: 10px; }
            .success { color: green; font-size: 18px; margin: 20px 0; }
            pre { background: #f5f5f5; padding: 15px; border-radius: 4px; overflow-x: auto; }
            ul { list-style-type: none; padding: 0; }
            li { padding: 10px; margin: 5px 0; background: #f9f9f9; border-left: 3px solid #667eea; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✅ 学校管理测试页面</h1>
            <div class="success">页面路由正常工作！</div>
            <p>如果您看到这个页面，说明URL路由配置正确。</p>
    """
    
    try:
        from backend.apps.customer_management.models import School
        schools = School.objects.all()[:100]
        school_count = School.objects.count()
        
        simple_html += f"""
            <h2>数据库查询结果</h2>
            <p><strong>学校总数：{school_count}</strong></p>
        """
        
        if schools:
            simple_html += """
            <h3>学校列表：</h3>
            <ul>
            """
            for school in schools[:20]:  # 只显示前20个
                tags = []
                if school.is_985:
                    tags.append('985')
                if school.is_211:
                    tags.append('211')
                if school.is_double_first_class:
                    tags.append('双一流')
                tag_str = ', '.join(tags) if tags else '无'
                region_display = dict(School.REGION_CHOICES).get(school.region, school.region)
                simple_html += f"<li><strong>{school.name}</strong> - {region_display} [{tag_str}]</li>"
            simple_html += "</ul>"
        else:
            simple_html += "<p>数据库中没有学校数据。</p>"
            
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        simple_html += f"""
            <h2>❌ 数据库查询错误</h2>
            <p><strong>错误信息：</strong>{error_msg}</p>
            <pre>{error_trace}</pre>
        """
    
    simple_html += """
        </div>
    </body>
    </html>
    """
    
    return HttpResponse(simple_html)
