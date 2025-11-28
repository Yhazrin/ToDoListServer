from flask import Blueprint, request, jsonify
from models import db, User, ProjectGroup, Task, CalendarEvent, SharedFile
from sqlalchemy.exc import IntegrityError
from auth import token_required
from datetime import datetime
import time

groups_bp = Blueprint('groups', __name__, url_prefix='/groups')

@groups_bp.route('/create', methods=['POST'])
def create_group():
    """创建项目组接口"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid request data'
            }), 400
        
        leader_id = data.get('leader_id', '').strip()
        name = data.get('name', '').strip()
        project_title = data.get('project_title', '').strip()
        description = data.get('description', '').strip()
        due_date = data.get('due_date')
        
        # 验证必填字段
        if not leader_id:
            return jsonify({
                'success': False,
                'message': 'Leader ID cannot be empty'
            }), 400
            
        if not name:
            return jsonify({
                'success': False,
                'message': 'Group name cannot be empty'
            }), 400
            
        if not project_title:
            return jsonify({
                'success': False,
                'message': 'Project title cannot be empty'
            }), 400
        
        # 验证负责人是否存在
        leader = User.query.filter_by(id=leader_id).first()
        if not leader:
            return jsonify({
                'success': False,
                'message': 'Leader user does not exist'
            }), 404
        
        # 检查项目组名称是否已存在
        existing_group = ProjectGroup.query.filter_by(name=name).first()
        if existing_group:
            return jsonify({
                'success': False,
                'message': 'Group name already exists'
            }), 409
        
        # 处理日期格式
        from datetime import datetime
        due_date_str = None
        if due_date:
            try:
                # 解析日期并转换为字符串格式
                due_date_obj = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                due_date_str = due_date_obj.strftime('%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid due date format, please use ISO format'
                }), 400
        
        # 创建新项目组
        new_group = ProjectGroup(
            name=name,
            project_title=project_title,
            leader_id=leader_id,
            due_date=due_date_str,
            description=description
        )
        
        db.session.add(new_group)
        
        # 自动将创建者加入项目组成员
        leader = User.query.filter_by(id=leader_id).first()
        if leader:
            new_group.members.append(leader)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Group created successfully',
            'group': new_group.to_dict()
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Database constraint error'
        }), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to create group: {str(e)}'
        }), 500

@groups_bp.route('/join', methods=['POST'])
def join_group():
    """用户加入项目组接口"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid request data'
            }), 400
        
        user_id = data.get('user_id', '').strip()
        group_id = data.get('group_id', '').strip()
        
        # 验证必填字段
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID cannot be empty'
            }), 400
            
        if not group_id:
            return jsonify({
                'success': False,
                'message': 'Group ID cannot be empty'
            }), 400
        
        # 验证用户是否存在
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': 'User does not exist'
            }), 404
        
        # 验证项目组是否存在
        group = ProjectGroup.query.filter_by(id=group_id).first()
        if not group:
            return jsonify({
                'success': False,
                'message': 'Group does not exist'
            }), 404
        
        # 检查用户是否已经是项目组成员
        if user in group.members:
            return jsonify({
                'success': False,
                'message': 'User is already a member of this group'
            }), 409
        
        # 添加用户到项目组
        group.members.append(user)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Successfully joined the group',
            'group': group.to_dict(),
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to join group: {str(e)}'
        }), 500

@groups_bp.route('/join-by-code', methods=['POST'])
def join_group_by_invite_code():
    """通过邀请码加入项目组接口"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid request data'
            }), 400
        
        user_id = data.get('user_id', '').strip()
        invite_code = data.get('invite_code', '').strip()
        
        # 验证必填字段
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID cannot be empty'
            }), 400
            
        if not invite_code:
            return jsonify({
                'success': False,
                'message': 'Invite code cannot be empty'
            }), 400
        
        # 验证邀请码格式（8位字符）
        if len(invite_code) != 8:
            return jsonify({
                'success': False,
                'message': 'Invalid invite code format'
            }), 400
        
        # 验证用户是否存在
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': 'User does not exist'
            }), 404
        
        # 通过邀请码查找项目组
        group = ProjectGroup.query.filter_by(invite_code=invite_code).first()
        if not group:
            return jsonify({
                'success': False,
                'message': 'Invalid invite code'
            }), 404
        
        # 检查项目组是否处于活跃状态
        if not group.is_active:
            return jsonify({
                'success': False,
                'message': 'This group is not active'
            }), 403
        
        # 检查用户是否已经是项目组成员
        if user in group.members:
            return jsonify({
                'success': False,
                'message': 'User is already a member of this group'
            }), 409
        
        # 添加用户到项目组
        group.members.append(user)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Successfully joined the group',
            'group': group.to_dict(),
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to join group: {str(e)}'
        }), 500

@groups_bp.route('/list/<user_id>', methods=['GET'])
def list_user_groups(user_id):
    """获取用户所属的项目组列表"""
    try:
        # 验证用户是否存在
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': 'User does not exist'
            }), 404
        
        # 获取用户创建的项目组
        created_groups = ProjectGroup.query.filter_by(leader_id=user_id).all()
        
        # 获取用户加入的项目组
        joined_groups = user.project_groups
        
        # 合并并去重
        all_groups = list(set(created_groups + joined_groups))
        
        return jsonify({
            'success': True,
            'message': 'Successfully retrieved group list',
            'groups': [group.to_dict() for group in all_groups]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve group list: {str(e)}'
        }), 500

@groups_bp.route('/info/<group_id>', methods=['GET'])
def get_group_info(group_id):
    """获取项目组详细信息"""
    try:
        # 验证项目组是否存在
        group = ProjectGroup.query.filter_by(id=group_id).first()
        if not group:
            return jsonify({
                'success': False,
                'message': 'Group does not exist'
            }), 404
        
        # 获取项目组成员信息
        members_list = []
        for member in group.members:
            members_list.append({
                'id': member.id,
                'username': member.username,
                'email': member.email
            })
        
        group_dict = group.to_dict()
        group_dict['members'] = members_list
        
        return jsonify({
            'success': True,
            'message': 'Successfully retrieved group information',
            'group': group_dict
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve group information: {str(e)}'
        }), 500

@groups_bp.route('/update/<group_id>', methods=['PUT'])
def update_group(group_id):
    """更新项目组信息接口"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid request data'
            }), 400
        
        # 验证项目组是否存在
        group = ProjectGroup.query.filter_by(id=group_id).first()
        if not group:
            return jsonify({
                'success': False,
                'message': 'Group does not exist'
            }), 404
        
        # 更新项目组信息
        if 'name' in data:
            name = data['name'].strip()
            if name:
                # 检查新名称是否与其他项目组重复
                existing_group = ProjectGroup.query.filter_by(name=name).filter(ProjectGroup.id != group_id).first()
                if existing_group:
                    return jsonify({
                        'success': False,
                        'message': 'Group name already exists'
                    }), 409
                group.name = name
        
        if 'project_title' in data:
            project_title = data['project_title'].strip()
            if project_title:
                group.project_title = project_title
        
        if 'description' in data:
            group.description = data['description'].strip()
        
        if 'due_date' in data:
            due_date = data['due_date']
            if due_date:
                try:
                    from datetime import datetime
                    # 解析日期并转换为字符串格式
                    due_date_obj = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    group.due_date = due_date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    return jsonify({
                        'success': False,
                        'message': 'Invalid due date format, please use ISO format'
                    }), 400
            else:
                group.due_date = None
        
        if 'contact_info' in data:
            group.contact_info = data['contact_info'].strip() if data['contact_info'] else None
        
        if 'is_active' in data:
            group.is_active = bool(data['is_active'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Group updated successfully',
            'group': group.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to update group: {str(e)}'
        }), 500

@groups_bp.route('/delete/<group_id>', methods=['DELETE'])
def delete_group(group_id):
    """删除项目组接口"""
    try:
        # 验证项目组是否存在
        group = ProjectGroup.query.filter_by(id=group_id).first()
        if not group:
            return jsonify({
                'success': False,
                'message': 'Group does not exist'
            }), 404
        
        # 删除项目组（会自动处理关联关系）
        db.session.delete(group)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Group deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to delete group: {str(e)}'
        }), 500

@groups_bp.route('/<group_id>/members', methods=['GET'])
@token_required
def get_group_members(current_user, group_id):
    """获取项目组成员列表接口"""
    try:
        # 验证项目组是否存在
        group = ProjectGroup.query.filter_by(id=group_id).first()
        if not group:
            return jsonify({
                'success': False,
                'message': 'Group does not exist'
            }), 404
        
        # 验证用户是否是项目组成员
        if current_user not in group.members and group.leader_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Permission denied: Not a member of this group'
            }), 403
        
        # 获取项目组成员信息
        members_list = []
        for member in group.members:
            members_list.append({
                'id': member.id,
                'username': member.username,
                'email': member.email,
                'is_active': member.is_active
            })
        
        # 添加负责人信息（如果负责人不在成员列表中）
        leader = User.query.filter_by(id=group.leader_id).first()
        if leader and not any(m['id'] == leader.id for m in members_list):
            members_list.insert(0, {
                'id': leader.id,
                'username': leader.username,
                'email': leader.email,
                'is_active': leader.is_active,
                'is_leader': True
            })
        else:
            # 标记负责人
            for member in members_list:
                if member['id'] == group.leader_id:
                    member['is_leader'] = True
        
        return jsonify({
            'success': True,
            'message': 'Members retrieved successfully',
            'members': members_list,
            'count': len(members_list)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve members: {str(e)}'
        }), 500

@groups_bp.route('/<group_id>/overview', methods=['GET'])
@token_required
def get_group_overview(current_user, group_id):
    """获取项目组概览接口（用于Dashboard）"""
    try:
        # 验证项目组是否存在
        group = ProjectGroup.query.filter_by(id=group_id).first()
        if not group:
            return jsonify({
                'success': False,
                'message': 'Group does not exist'
            }), 404
        
        # 验证用户是否是项目组成员
        if current_user not in group.members and group.leader_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Permission denied: Not a member of this group'
            }), 403
        
        # 获取基本信息
        group_dict = group.to_dict()
        
        # 获取成员统计
        members_count = group.members.count()
        
        # 获取任务统计
        tasks = Task.query.filter(
            Task.project_id == group_id,
            Task.is_deleted == False
        ).all()
        
        tasks_total = len(tasks)
        tasks_completed = len([t for t in tasks if t.status == 'completed'])
        tasks_pending = len([t for t in tasks if t.status == 'pending'])
        tasks_in_progress = len([t for t in tasks if t.status == 'in_progress'])
        
        # 获取今日任务
        today = datetime.utcnow().strftime('%Y-%m-%d')
        today_tasks = [t for t in tasks if t.due_date == today and t.status not in ['completed', 'cancelled']]
        
        # 获取文件统计
        files = SharedFile.query.filter(
            SharedFile.group_id == group_id,
            SharedFile.is_deleted == False
        ).all()
        files_count = len(files)
        
        # 获取最近的日历事件（如果有项目组的日历事件）
        # 这里简化处理，只统计项目组中成员的任务相关的日历事件
        today_start = f'{today} 00:00:00'
        today_end = f'{today} 23:59:59'
        member_ids = [m.id for m in group.members] + [group.leader_id]
        today_events = CalendarEvent.query.filter(
            CalendarEvent.user_id.in_(member_ids),
            CalendarEvent.is_deleted == False,
            CalendarEvent.start_time >= today_start,
            CalendarEvent.start_time <= today_end
        ).count()
        
        overview = {
            'group': group_dict,
            'statistics': {
                'members': members_count,
                'tasks': {
                    'total': tasks_total,
                    'completed': tasks_completed,
                    'pending': tasks_pending,
                    'in_progress': tasks_in_progress,
                    'today': len(today_tasks)
                },
                'files': files_count,
                'events_today': today_events
            },
            'progress': {
                'task_completion_rate': round((tasks_completed / tasks_total * 100) if tasks_total > 0 else 0, 2)
            }
        }
        
        return jsonify({
            'success': True,
            'message': 'Group overview retrieved successfully',
            'overview': overview
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve group overview: {str(e)}'
        }), 500