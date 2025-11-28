from flask import Blueprint, request, jsonify
from models import db, User, ProjectGroup, Task, TaskFile, SharedFile
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
        
        # 构建查询
        query = Task.query.filter(Task.is_deleted == False)
        
        # 如果没有指定userId，默认使用当前用户的任务
        if user_id:
            if user_id != current_user.id:
                # 检查权限：只能查看自己的任务或其他用户共享的任务
                return jsonify({
                    'success': False,
                    'message': 'Permission denied'
                }), 403
            query = query.filter(Task.user_id == user_id)
        else:
            query = query.filter(Task.user_id == current_user.id)
        
        # 按项目筛选
        if project_id:
            # 验证用户是否有权限访问该项目组
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
            
            query = query.filter(Task.project_id == project_id)
        
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
                return jsonify({
                    'success': False,
                    'message': 'Permission denied: Cannot create subtask for other user\'s task'
                }), 403
        
        # 处理日期
        due_date = data.get('due_date')
        if due_date:
            try:
                due_date_obj = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                due_date = due_date_obj.strftime('%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid due date format, please use ISO format'
                }), 400
        
        # 创建新任务
        new_task = Task(
            user_id=current_user.id,
            title=title,
            project_id=project_id,
            parent_task_id=parent_task_id,
            description=data.get('description'),
            status=data.get('status', 'pending'),
            priority=data.get('priority', 'medium'),
            due_date=due_date
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
            return jsonify({
                'success': False,
                'message': 'Permission denied'
            }), 403
        
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

@tasks_bp.route('/<task_id>', methods=['PUT'])
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
        
        if 'due_date' in data:
            due_date = data['due_date']
            if due_date:
                try:
                    due_date_obj = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    task.due_date = due_date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    return jsonify({
                        'success': False,
                        'message': 'Invalid due date format, please use ISO format'
                    }), 400
            else:
                task.due_date = None
        
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

