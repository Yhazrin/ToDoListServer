#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API测试脚本
用于测试ToDoList服务器的认证功能
"""

import requests
import json
import sys

# 服务器配置
BASE_URL = 'http://localhost:5000'
HEADERS = {'Content-Type': 'application/json'}

def test_server_status():
    """测试服务器状态"""
    print("\n=== 测试服务器状态 ===")
    try:
        response = requests.get(f'{BASE_URL}/')
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"连接失败: {e}")
        return False

def test_auth_status():
    """测试认证服务状态"""
    print("\n=== 测试认证服务状态 ===")
    try:
        response = requests.get(f'{BASE_URL}/auth/status')
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def test_register(username, email, password):
    """测试用户注册"""
    print(f"\n=== 测试用户注册: {username} ===")
    data = {
        'username': username,
        'email': email,
        'password': password
    }
    
    try:
        response = requests.post(f'{BASE_URL}/auth/register', 
                               headers=HEADERS, 
                               json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 201
    except Exception as e:
        print(f"注册失败: {e}")
        return False

def test_login(username, password):
    """测试用户登录"""
    print(f"\n=== 测试用户登录: {username} ===")
    data = {
        'username': username,
        'password': password
    }
    
    try:
        response = requests.post(f'{BASE_URL}/auth/login', 
                               headers=HEADERS, 
                               json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"登录失败: {e}")
        return False

def test_invalid_cases():
    """测试无效输入情况"""
    print("\n=== 测试无效输入情况 ===")
    
    # 测试空用户名注册
    print("\n--- 测试空用户名注册 ---")
    test_register('', 'test@example.com', 'password123')
    
    # 测试无效邮箱格式
    print("\n--- 测试无效邮箱格式 ---")
    test_register('testuser2', 'invalid-email', 'password123')
    
    # 测试弱密码
    print("\n--- 测试弱密码 ---")
    test_register('testuser3', 'test3@example.com', '123')
    
    # 测试错误密码登录
    print("\n--- 测试错误密码登录 ---")
    test_login('testuser', 'wrongpassword')
    
    # 测试不存在的用户登录
    print("\n--- 测试不存在的用户登录 ---")
    test_login('nonexistentuser', 'password123')

def main():
    """主测试函数"""
    print("ToDoList API 测试脚本")
    print("=" * 50)
    
    # 检查服务器是否运行
    if not test_server_status():
        print("\n❌ 服务器未运行，请先启动服务器: python app.py")
        sys.exit(1)
    
    # 测试认证服务状态
    if not test_auth_status():
        print("\n❌ 认证服务不可用")
        sys.exit(1)
    
    # 测试用户注册
    success_register = test_register('testuser', 'test@example.com', 'password123')
    
    # 测试重复注册（应该失败）
    print("\n--- 测试重复注册（应该失败） ---")
    test_register('testuser', 'test@example.com', 'password123')
    
    # 测试用户登录
    if success_register:
        test_login('testuser', 'password123')
        
        # 测试邮箱登录
        print("\n--- 测试邮箱登录 ---")
        test_login('test@example.com', 'password123')
    
    # 测试无效输入情况
    test_invalid_cases()
    
    print("\n" + "=" * 50)
    print("✅ 测试完成！")
    print("\n💡 提示:")
    print("- 如果看到201状态码，说明注册成功")
    print("- 如果看到200状态码，说明登录成功")
    print("- 如果看到4xx状态码，说明请求有误")
    print("- 如果看到5xx状态码，说明服务器错误")

if __name__ == '__main__':
    main()