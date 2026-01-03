from django import forms
from django.core.exceptions import ValidationError
import json
from backend.apps.api_management.models import ApiInterface, ApiTestRecord


class ApiInterfaceForm(forms.ModelForm):
    """API接口表单，增强JSON字段输入"""
    
    class Meta:
        model = ApiInterface
        fields = '__all__'
        widgets = {
            'auth_config': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': '{\n  "api_key": "your-api-key",\n  "header_name": "X-API-Key"\n}',
                'style': 'font-family: monospace; font-size: 12px;'
            }),
            'request_headers': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': '{\n  "Content-Type": "application/json",\n  "Accept": "application/json"\n}',
                'style': 'font-family: monospace; font-size: 12px;'
            }),
            'request_params': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': '{\n  "page": 1,\n  "limit": 20\n}',
                'style': 'font-family: monospace; font-size: 12px;'
            }),
            'request_body_schema': forms.Textarea(attrs={
                'rows': 8,
                'placeholder': '{\n  "type": "object",\n  "properties": {\n    "name": {"type": "string"},\n    "age": {"type": "integer"}\n  }\n}',
                'style': 'font-family: monospace; font-size: 12px;'
            }),
            'response_schema': forms.Textarea(attrs={
                'rows': 8,
                'placeholder': '{\n  "type": "object",\n  "properties": {\n    "code": {"type": "integer"},\n    "data": {"type": "object"}\n  }\n}',
                'style': 'font-family: monospace; font-size: 12px;'
            }),
        }
    
    def clean_auth_config(self):
        """验证认证配置JSON"""
        value = self.cleaned_data.get('auth_config')
        if not value:
            return {}
        return self._parse_json(value, '认证配置')
    
    def clean_request_headers(self):
        """验证请求头JSON"""
        value = self.cleaned_data.get('request_headers')
        if not value:
            return {}
        return self._parse_json(value, '请求头')
    
    def clean_request_params(self):
        """验证请求参数JSON"""
        value = self.cleaned_data.get('request_params')
        if not value:
            return {}
        return self._parse_json(value, '请求参数')
    
    def clean_request_body_schema(self):
        """验证请求体结构JSON"""
        value = self.cleaned_data.get('request_body_schema')
        if not value:
            return {}
        return self._parse_json(value, '请求体结构')
    
    def clean_response_schema(self):
        """验证响应结构JSON"""
        value = self.cleaned_data.get('response_schema')
        if not value:
            return {}
        return self._parse_json(value, '响应结构')
    
    def _parse_json(self, value, field_name):
        """解析JSON字符串"""
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return {}
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                raise ValidationError(
                    f'{field_name}必须是有效的JSON格式。错误：{str(e)}\n\n'
                    f'示例格式：\n'
                    f'{{"key": "value"}}\n\n'
                    f'或者空对象：{{}}'
                )
        return {}


class ApiTestRecordForm(forms.ModelForm):
    """API测试记录表单，增强JSON字段输入"""
    
    class Meta:
        model = ApiTestRecord
        fields = '__all__'
        widgets = {
            'test_params': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': '{\n  "id": 123,\n  "name": "test"\n}',
                'style': 'font-family: monospace; font-size: 12px;'
            }),
        }
    
    def clean_test_params(self):
        """验证测试参数JSON"""
        value = self.cleaned_data.get('test_params')
        if not value:
            return {}
        return self._parse_json(value, '测试参数')
    
    def _parse_json(self, value, field_name):
        """解析JSON字符串"""
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return {}
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                raise ValidationError(
                    f'{field_name}必须是有效的JSON格式。错误：{str(e)}\n\n'
                    f'示例格式：\n'
                    f'{{"key": "value"}}\n\n'
                    f'或者空对象：{{}}'
                )
        return {}

