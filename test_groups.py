#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目组接口测试脚本
"""

import requests
import json
import random
import string

# 服务器地址
BASE_URL = 'http://localhost:5000'

def generate_random_string(length=8):
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def test_user_registration():
    """测试用户注册"""
    print("\n=== 测试用户注册 ===")
    
    # 注册测试用户1
    random_suffix = generate_random_string()
    user1_data = {
        'username': f'testuser1_{random_suffix}',
        'password': 'password123',
        'email': f'user1_{random_suffix}@test.com'
    }
    
    response = requests.post(f'{BASE_URL}/auth/register', json=user1_data)
    print(f"注册用户1: {response.status_code}")
    if response.status_code == 201:
        user1_info = response.json()
        print(f"用户1 ID: {user1_info['user']['id']}")
        return user1_info['user']['id']
    else:
        print(f"注册失败: {response.json()}")
        return None

def test_create_group(creator_id):
    """测试创建项目组"""
    print("\n=== 测试创建项目组 ===")
    
    random_suffix = generate_random_string()
    group_data = {
        'leader_id': creator_id,
        'name': f'测试项目组_{random_suffix}',
        'project_title': f'测试项目_{random_suffix}',
        'description': '这是一个测试项目组，用于验证功能',
        'due_date': '2024-12-31T23:59:59'
    }
    
    response = requests.post(f'{BASE_URL}/groups/create', json=group_data)
    print(f"创建项目组: {response.status_code}")
    
    if response.status_code == 201:
        group_info = response.json()
        print(f"项目组创建成功: {group_info['group']['name']}")
        print(f"项目组 ID: {group_info['group']['id']}")
        return group_info['group']['id']
    else:
        print(f"创建失败: {response.json()}")
        return None

def test_join_group(user_id, group_id):
    """测试加入项目组"""
    print("\n=== 测试加入项目组 ===")
    
    # 先注册第二个用户
    random_suffix = generate_random_string()
    user2_data = {
        'username': f'testuser2_{random_suffix}',
        'password': 'password123',
        'email': f'user2_{random_suffix}@test.com'
    }
    
    response = requests.post(f'{BASE_URL}/auth/register', json=user2_data)
    if response.status_code == 201:
        user2_info = response.json()
        user2_id = user2_info['user']['id']
        print(f"注册用户2成功，ID: {user2_id}")
        
        # 用户2加入项目组
        join_data = {
            'user_id': user2_id,
            'group_id': group_id
        }
        
        response = requests.post(f'{BASE_URL}/groups/join', json=join_data)
        print(f"加入项目组: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"用户2成功加入项目组: {result['group']['name']}")
            return user2_id
        else:
            print(f"加入失败: {response.json()}")
            return None
    else:
        print(f"注册用户2失败: {response.json()}")
        return None

def test_list_groups(user_id):
    """测试获取用户项目组列表"""
    print("\n=== 测试获取项目组列表 ===")
    
    response = requests.get(f'{BASE_URL}/groups/list/{user_id}')
    print(f"获取项目组列表: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"用户所属项目组数量: {len(result['groups'])}")
        for group in result['groups']:
            print(f"- {group['name']}: {group['description']}")
    else:
        print(f"获取失败: {response.json()}")

def test_group_info(group_id):
    """测试获取项目组详细信息"""
    print("\n=== 测试获取项目组信息 ===")
    
    response = requests.get(f'{BASE_URL}/groups/info/{group_id}')
    print(f"获取项目组信息: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        group = result['group']
        print(f"项目组名称: {group['name']}")
        print(f"项目组描述: {group['description']}")
        print(f"负责人ID: {group['leader_id']}")
        print(f"成员数量: {len(group['members'])}")
    else:
        print(f"获取失败: {response.json()}")

def test_error_cases():
    """测试错误情况"""
    print("\n=== 测试错误情况 ===")
    
    # 测试创建重复名称的项目组
    print("\n1. 测试创建重复名称的项目组")
    duplicate_group = {
        'creator_id': 'fake_user_id',
        'name': '测试项目组',
        'description': '重复名称测试'
    }
    response = requests.post(f'{BASE_URL}/groups/create', json=duplicate_group)
    print(f"创建重复项目组: {response.status_code} - {response.json()['message']}")
    
    # 测试不存在的用户加入项目组
    print("\n2. 测试不存在的用户加入项目组")
    invalid_join = {
        'user_id': 'nonexistent_user',
        'group_id': 'fake_group_id'
    }
    response = requests.post(f'{BASE_URL}/groups/join', json=invalid_join)
    print(f"无效用户加入: {response.status_code} - {response.json()['message']}")
    
    # 测试获取不存在的项目组信息
    print("\n3. 测试获取不存在的项目组信息")
    response = requests.get(f'{BASE_URL}/groups/info/nonexistent_group')
    print(f"获取不存在项目组: {response.status_code} - {response.json()['message']}")

def main():
    """主测试函数"""
    print("开始测试项目组接口功能...")
    
    try:
        # 1. 注册用户
        user1_id = test_user_registration()
        if not user1_id:
            print("用户注册失败，终止测试")
            return
        
        # 2. 创建项目组
        group_id = test_create_group(user1_id)
        if not group_id:
            print("项目组创建失败，终止测试")
            return
        
        # 3. 用户加入项目组
        user2_id = test_join_group(user1_id, group_id)
        
        # 4. 获取项目组列表
        test_list_groups(user1_id)
        if user2_id:
            test_list_groups(user2_id)
        
        # 5. 获取项目组详细信息
        test_group_info(group_id)
        
        # 6. 测试错误情况
        test_error_cases()
        
        print("\n=== 测试完成 ===")
        
    except requests.exceptions.ConnectionError:
        print("连接服务器失败，请确保服务器正在运行")
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")

if __name__ == '__main__':
    main()