from flask import Blueprint, request, jsonify
from models import db, User, ProjectGroup, Task, TaskFile, SharedFile, TaskAssignee
from auth import token_required
from sqlalchemy.exc import IntegrityError
from datetime import datetime

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')

def build_task_tree(tasks, parent_id=None):
    """构建任务树结构"""
    tree = []
    for task in tasks:
        if task.parent_task_id == parent_id and not task.is_deleted:
            task_dict = task.to_dict()
            # 递归获取子任务
            children = build_task_tree(tasks, task.id)
            if children:
                task_dict['children'] = children
            tree.append(task_dict)
    return tree

@tasks_bp.route('', methods=['GET'])
@token_required
def get_tasks(current_user):
    """获取任务列表接口"""
    try:
        # 获取查询参数
        project_id = request.args.get('projectId')
        user_id = request.args.get('userId')
        
        query = Task.query.filter(Task.is_deleted == False)
        if project_id:
            project = ProjectGroup.query.filter_by(id=project_id).first()
            if not project:
                return jsonify({'success': False, 'message': 'Project not found'}), 404
            if current_user not in project.members and project.leader_id != current_user.id:
                return jsonify({'success': False, 'message': 'Permission denied: Not a member of this project'}), 403
            query = query.filter(Task.project_id == project_id)
        elif user_id:
            if user_id != current_user.id:
                return jsonify({'success': False, 'message': 'Permission denied'}), 403
            query = query.filter(Task.user_id == user_id)
        else:
            query = query.filter(Task.user_id == current_user.id)
        
        # 按月份筛选（用于月视图）
        month = request.args.get('month')  # YYYY-MM
        if month:
            # 计算该月范围
            try:
                from datetime import datetime as dt
                start = dt.strptime(month + '-01', '%Y-%m-%d')
                if start.month == 12:
                    end = start.replace(year=start.year + 1, month=1)
                else:
                    end = start.replace(month=start.month + 1)
                start_str = start.strftime('%Y-%m-%d')
                end_str = end.strftime('%Y-%m-%d')
            except ValueError:
                return jsonify({'success': False, 'message': 'Invalid month format'}), 400
            # 任务在月视图内的判定：仅使用 start_date/end_date 区间
            tasks = query.order_by(Task.created_at.desc()).all()
            def in_month(t):
                sd = t.start_date or t.end_date
                ed = t.end_date or t.start_date
                if not sd and not ed:
                    return False
                sd = sd or ed
                ed = ed or sd
                return not (ed < start_str or sd >= end_str)
            tasks = [t for t in tasks if in_month(t)]
        else:
            tasks = query.order_by(Task.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'message': 'Tasks retrieved successfully',
            'tasks': [task.to_dict() for task in tasks]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve tasks: {str(e)}'
        }), 500

@tasks_bp.route('', methods=['POST'])
@token_required
def create_task(current_user):
    """创建任务接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid request data'
            }), 400
        
        title = data.get('title', '').strip()
        if not title:
            return jsonify({
                'success': False,
                'message': 'Title is required'
            }), 400
        
        # 验证项目ID（如果提供）
        project_id = data.get('project_id')
        if project_id:
            project = ProjectGroup.query.filter_by(id=project_id).first()
            if not project:
                return jsonify({
                    'success': False,
                    'message': 'Project not found'
                }), 404
            
            if current_user not in project.members and project.leader_id != current_user.id:
                return jsonify({
                    'success': False,
                    'message': 'Permission denied: Not a member of this project'
                }), 403
        
        # 验证父任务ID（如果提供）
        parent_task_id = data.get('parent_task_id')
        if parent_task_id:
            parent_task = Task.query.filter_by(id=parent_task_id, is_deleted=False).first()
            if not parent_task:
                return jsonify({
                    'success': False,
                    'message': 'Parent task not found'
                }), 404
            
            if parent_task.user_id != current_user.id:
                if parent_task.project_id:
                    project = ProjectGroup.query.filter_by(id=parent_task.project_id).first()
                    if not project or (current_user not in project.members and project.leader_id != current_user.id):
                        return jsonify({'success': False, 'message': 'Permission denied'}), 403
                else:
                    return jsonify({'success': False, 'message': 'Permission denied'}), 403
        
        # 处理日期
        def parse_date(value):
            if not value:
                return None
            try:
                dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                return None
        start_date = parse_date(data.get('start_date'))
        end_date = parse_date(data.get('end_date'))
        due_date = parse_date(data.get('due_date'))
        if any(v is None and data.get(k) for k, v in [('start_date', start_date), ('end_date', end_date)]):
            return jsonify({'success': False, 'message': 'Invalid date format, please use ISO format'}), 400
        
        # 创建新任务
        new_task = Task(
            user_id=current_user.id,
            title=title,
            project_id=project_id,
            parent_task_id=parent_task_id,
            description=data.get('description'),
            status=data.get('status', 'pending'),
            priority=data.get('priority', 'medium'),
            start_date=start_date,
            end_date=end_date,
            due_date=due_date,
            assigned_to=data.get('assigned_to')
        )
        
        db.session.add(new_task)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Task created successfully',
            'task': new_task.to_dict()
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
            'message': f'Failed to create task: {str(e)}'
        }), 500

@tasks_bp.route('/<task_id>', methods=['GET'])
@token_required
def get_task(current_user, task_id):
    """获取任务详情接口"""
    try:
        task = Task.query.filter_by(id=task_id, is_deleted=False).first()
        if not task:
            return jsonify({
                'success': False,
                'message': 'Task not found'
            }), 404
        
        # 检查权限
        if task.user_id != current_user.id:
            if task.project_id:
                project = ProjectGroup.query.filter_by(id=task.project_id).first()
                if not project or (current_user not in project.members and project.leader_id != current_user.id):
                    return jsonify({'success': False, 'message': 'Permission denied'}), 403
            else:
                return jsonify({'success': False, 'message': 'Permission denied'}), 403
        
        return jsonify({
            'success': True,
            'message': 'Task retrieved successfully',
            'task': task.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve task: {str(e)}'
        }), 500

@tasks_bp.route('/<task_id>', methods=['PUT', 'PATCH'])
@token_required
def update_task(current_user, task_id):
    """更新任务接口"""
    try:
        task = Task.query.filter_by(id=task_id, is_deleted=False).first()
        if not task:
            return jsonify({
                'success': False,
                'message': 'Task not found'
            }), 404
        
        if task.user_id != current_user.id:
            if task.project_id:
                project = ProjectGroup.query.filter_by(id=task.project_id).first()
                if not project or (current_user not in project.members and project.leader_id != current_user.id):
                    return jsonify({'success': False, 'message': 'Permission denied'}), 403
            else:
                return jsonify({'success': False, 'message': 'Permission denied'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid request data'
            }), 400
        
        # 更新任务字段
        if 'title' in data:
            title = data['title'].strip()
            if title:
                task.title = title
        
        if 'description' in data:
            task.description = data['description']
        
        if 'status' in data:
            status = data['status']
            if status in ['pending', 'in_progress', 'completed', 'cancelled']:
                task.status = status
                if status == 'completed' and not task.completed_at:
                    task.completed_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                elif status != 'completed':
                    task.completed_at = None
        
        if 'priority' in data:
            priority = data['priority']
            if priority in ['low', 'medium', 'high', 'urgent']:
                task.priority = priority
        
        if 'assigned_to' in data:
            task.assigned_to = data['assigned_to']
        
        def parse_date(value, field):
            if value is None:
                return None
            try:
                dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                return jsonify({'success': False, 'message': f'Invalid {field} format, please use ISO format'}), 400
        if 'start_date' in data:
            v = data['start_date']
            if v:
                res = parse_date(v, 'start_date')
                if isinstance(res, tuple):
                    return res
                task.start_date = res
            else:
                task.start_date = None
        if 'end_date' in data:
            v = data['end_date']
            if v:
                res = parse_date(v, 'end_date')
                if isinstance(res, tuple):
                    return res
                task.end_date = res
            else:
                task.end_date = None
        # 移除 due_date 更新逻辑
        
        if 'project_id' in data:
            project_id = data['project_id']
            if project_id:
                project = ProjectGroup.query.filter_by(id=project_id).first()
                if not project:
                    return jsonify({
                        'success': False,
                        'message': 'Project not found'
                    }), 404
                
                if current_user not in project.members and project.leader_id != current_user.id:
                    return jsonify({
                        'success': False,
                        'message': 'Permission denied: Not a member of this project'
                    }), 403
            
            task.project_id = project_id
        
        if 'parent_task_id' in data:
            parent_task_id = data['parent_task_id']
            if parent_task_id:
                # 不能将任务设置为自己的子任务
                if parent_task_id == task_id:
                    return jsonify({
                        'success': False,
                        'message': 'Cannot set task as its own parent'
                    }), 400
                
                # 检查是否会产生循环引用
                parent = Task.query.filter_by(id=parent_task_id, is_deleted=False).first()
                if not parent:
                    return jsonify({
                        'success': False,
                        'message': 'Parent task not found'
                    }), 404
                
                # 检查父任务是否在任务的后代中（防止循环）
                def is_descendant(check_task_id, ancestor_id):
                    check_task = Task.query.filter_by(id=check_task_id, is_deleted=False).first()
                    if not check_task or not check_task.parent_task_id:
                        return False
                    if check_task.parent_task_id == ancestor_id:
                        return True
                    return is_descendant(check_task.parent_task_id, ancestor_id)
                
                if is_descendant(parent_task_id, task_id):
                    return jsonify({
                        'success': False,
                        'message': 'Cannot create circular reference'
                    }), 400
                
                if parent.user_id != current_user.id:
                    return jsonify({
                        'success': False,
                        'message': 'Permission denied: Cannot set parent to other user\'s task'
                    }), 403
            
            task.parent_task_id = parent_task_id
        
        task.updated_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Task updated successfully',
            'task': task.to_dict()
        }), 200
        
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
            'message': f'Failed to update task: {str(e)}'
        }), 500

@tasks_bp.route('/<task_id>', methods=['DELETE'])
@token_required
def delete_task(current_user, task_id):
    """删除任务接口（软删除）"""
    try:
        task = Task.query.filter_by(id=task_id, is_deleted=False).first()
        if not task:
            return jsonify({
                'success': False,
                'message': 'Task not found'
            }), 404
        
        # 检查权限
        if task.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Permission denied'
            }), 403
        
        # 软删除：标记为已删除
        task.is_deleted = True
        task.updated_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Task deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to delete task: {str(e)}'
        }), 500

@tasks_bp.route('/tree/<group_id>', methods=['GET'])
@token_required
def get_task_tree(current_user, group_id):
    """获取项目组的任务树接口"""
    try:
        # 验证项目组存在且用户有权限
        project = ProjectGroup.query.filter_by(id=group_id).first()
        if not project:
            return jsonify({
                'success': False,
                'message': 'Project group not found'
            }), 404
        
        if current_user not in project.members and project.leader_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Permission denied: Not a member of this project'
            }), 403
        
        # 获取该项目组的所有任务（包括所有成员的任务）
        tasks = Task.query.filter(
            Task.project_id == group_id,
            Task.is_deleted == False
        ).order_by(Task.position, Task.created_at).all()
        
        # 构建任务树
        task_tree = build_task_tree(tasks)
        
        return jsonify({
            'success': True,
            'message': 'Task tree retrieved successfully',
            'tree': task_tree
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve task tree: {str(e)}'
        }), 500

@tasks_bp.route('/<task_id>/move', methods=['PUT'])
@token_required
def move_task(current_user, task_id):
    """移动任务接口（更改父任务或项目）"""
    try:
        task = Task.query.filter_by(id=task_id, is_deleted=False).first()
        if not task:
            return jsonify({
                'success': False,
                'message': 'Task not found'
            }), 404
        
        # 检查权限
        if task.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Permission denied'
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid request data'
            }), 400
        
        # 更新父任务
        if 'parent_task_id' in data:
            parent_task_id = data['parent_task_id']  # 可以是null
            if parent_task_id:
                # 不能将任务设置为自己的子任务
                if parent_task_id == task_id:
                    return jsonify({
                        'success': False,
                        'message': 'Cannot set task as its own parent'
                    }), 400
                
                parent = Task.query.filter_by(id=parent_task_id, is_deleted=False).first()
                if not parent:
                    return jsonify({
                        'success': False,
                        'message': 'Parent task not found'
                    }), 404
                
                # 检查是否会产生循环引用
                def is_descendant(check_task_id, ancestor_id):
                    check_task = Task.query.filter_by(id=check_task_id, is_deleted=False).first()
                    if not check_task or not check_task.parent_task_id:
                        return False
                    if check_task.parent_task_id == ancestor_id:
                        return True
                    return is_descendant(check_task.parent_task_id, ancestor_id)
                
                if is_descendant(parent_task_id, task_id):
                    return jsonify({
                        'success': False,
                        'message': 'Cannot create circular reference'
                    }), 400
            
            task.parent_task_id = parent_task_id
        
        # 更新项目
        if 'project_id' in data:
            project_id = data['project_id']  # 可以是null
            if project_id:
                project = ProjectGroup.query.filter_by(id=project_id).first()
                if not project:
                    return jsonify({
                        'success': False,
                        'message': 'Project not found'
                    }), 404
                
                if current_user not in project.members and project.leader_id != current_user.id:
                    return jsonify({
                        'success': False,
                        'message': 'Permission denied: Not a member of this project'
                    }), 403
            
            task.project_id = project_id
        
        # 更新位置（用于排序）
        if 'position' in data:
            position = data.get('position', 0)
            task.position = position
        
        task.updated_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Task moved successfully',
            'task': task.to_dict()
        }), 200
        
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
            'message': f'Failed to move task: {str(e)}'
        }), 500

@tasks_bp.route('/<task_id>/attachments', methods=['POST'])
@token_required
def add_task_attachment(current_user, task_id):
    """添加任务附件接口"""
    try:
        task = Task.query.filter_by(id=task_id, is_deleted=False).first()
        if not task:
            return jsonify({
                'success': False,
                'message': 'Task not found'
            }), 404
        
        # 检查权限
        if task.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Permission denied'
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid request data'
            }), 400
        
        file_id = data.get('file_id')
        if not file_id:
            return jsonify({
                'success': False,
                'message': 'File ID is required'
            }), 400
        
        # 验证文件存在
        file = SharedFile.query.filter_by(id=file_id, is_deleted=False).first()
        if not file:
            return jsonify({
                'success': False,
                'message': 'File not found'
            }), 404
        
        # 检查文件是否已有权限访问（文件所有者或项目组成员）
        if file.user_id != current_user.id:
            # 如果是项目文件，检查用户是否是项目组成员
            if file.group_id:
                project = ProjectGroup.query.filter_by(id=file.group_id).first()
                if not project or (current_user not in project.members and project.leader_id != current_user.id):
                    return jsonify({
                        'success': False,
                        'message': 'Permission denied: Cannot attach file you do not have access to'
                    }), 403
            else:
                return jsonify({
                    'success': False,
                    'message': 'Permission denied: Cannot attach file you do not have access to'
                }), 403
        
        # 检查是否已经关联
        existing = TaskFile.query.filter_by(task_id=task_id, file_id=file_id).first()
        if existing:
            return jsonify({
                'success': False,
                'message': 'File is already attached to this task'
            }), 409
        
        # 创建任务文件关联
        task_file = TaskFile(task_id=task_id, file_id=file_id)
        db.session.add(task_file)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Attachment added successfully',
            'attachment': task_file.to_dict()
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
            'message': f'Failed to add attachment: {str(e)}'
        }), 500

@tasks_bp.route('/<task_id>/attachments', methods=['GET'])
@token_required
def get_task_attachments(current_user, task_id):
    """获取任务附件列表接口"""
    try:
        task = Task.query.filter_by(id=task_id, is_deleted=False).first()
        if not task:
            return jsonify({
                'success': False,
                'message': 'Task not found'
            }), 404
        
        # 检查权限
        if task.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Permission denied'
            }), 403
        
        # 获取任务的所有附件
        task_files = TaskFile.query.filter_by(task_id=task_id).all()
        attachments = []
        for task_file in task_files:
            file = SharedFile.query.filter_by(id=task_file.file_id, is_deleted=False).first()
            if file:
                attachments.append(file.to_dict())
        
        return jsonify({
            'success': True,
            'message': 'Attachments retrieved successfully',
            'attachments': attachments
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve attachments: {str(e)}'
        }), 500

@tasks_bp.route('/<task_id>/attachments/<file_id>', methods=['DELETE'])
@token_required
def delete_task_attachment(current_user, task_id, file_id):
    """删除任务附件接口"""
    try:
        task = Task.query.filter_by(id=task_id, is_deleted=False).first()
        if not task:
            return jsonify({
                'success': False,
                'message': 'Task not found'
            }), 404
        
        # 检查权限
        if task.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Permission denied'
            }), 403
        
        # 查找任务文件关联
        task_file = TaskFile.query.filter_by(task_id=task_id, file_id=file_id).first()
        if not task_file:
            return jsonify({
                'success': False,
                'message': 'Attachment not found'
            }), 404
        
        # 删除关联（不删除文件本身）
        db.session.delete(task_file)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Attachment removed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to remove attachment: {str(e)}'
        }), 500
@tasks_bp.route('/<task_id>/assign', methods=['POST'])
@token_required
def assign_task(current_user, task_id):
    """批量或单项指派任务给成员"""
    try:
        task = Task.query.filter_by(id=task_id, is_deleted=False).first()
        if not task:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        # 只有任务所有者或项目负责人可指派
        project = ProjectGroup.query.filter_by(id=task.project_id).first() if task.project_id else None
        if not (task.user_id == current_user.id or (project and project.leader_id == current_user.id)):
            return jsonify({'success': False, 'message': 'Permission denied'}), 403

        data = request.get_json() or {}
        assignees = data.get('assignees')
        assigned_to = data.get('assigned_to')

        updated = []
        if assigned_to:
            task.assigned_to = assigned_to
        if isinstance(assignees, list):
            for uid in assignees:
                # 必须是项目成员
                if project and (uid not in [m.id for m in project.members] and uid != project.leader_id):
                    continue
                existing = TaskAssignee.query.filter_by(task_id=task_id, user_id=uid).first()
                if not existing:
                    db.session.add(TaskAssignee(task_id=task_id, user_id=uid))
                    updated.append(uid)

        task.updated_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()
        return jsonify({'success': True, 'message': 'Task assigned', 'assigned_to': task.assigned_to, 'assignees_added': updated, 'task': task.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to assign: {str(e)}'}), 500