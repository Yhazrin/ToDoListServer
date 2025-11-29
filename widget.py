from flask import Blueprint, request, jsonify
from models import db, User, Task, CalendarEvent, ProjectGroup, SharedFile
from auth import token_required
from datetime import datetime, date

widget_bp = Blueprint('widget', __name__, url_prefix='/widget')

@widget_bp.route('/today-tasks', methods=['GET'])
@token_required
def get_today_tasks(current_user):
    """获取今日任务接口（用于Widget）"""
    try:
        today = datetime.utcnow().strftime('%Y-%m-%d')
        
        # 获取今日到期的任务
        today_tasks = Task.query.filter(
            Task.user_id == current_user.id,
            Task.due_date == today,
            Task.is_deleted == False,
            Task.status != 'completed',
            Task.status != 'cancelled'
        ).order_by(
            Task.priority.desc(),  # 高优先级在前
            Task.created_at
        ).all()
        
        # 获取今日需要开始的任务（如果有start_date字段，这里简化处理）
        # 可以扩展Task模型添加start_date字段
        
        tasks_data = []
        for task in today_tasks:
            task_dict = task.to_dict()
            tasks_data.append(task_dict)
        
        return jsonify({
            'success': True,
            'message': 'Today tasks retrieved successfully',
            'date': today,
            'tasks': tasks_data,
            'count': len(tasks_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve today tasks: {str(e)}'
        }), 500

@widget_bp.route('/today-events', methods=['GET'])
@token_required
def get_today_events(current_user):
    """获取今日日历事件接口（用于Widget）"""
    try:
        today = datetime.utcnow().strftime('%Y-%m-%d')
        today_start = f'{today} 00:00:00'
        today_end = f'{today} 23:59:59'
        
        # 获取今日的日历事件
        today_events = CalendarEvent.query.filter(
            CalendarEvent.user_id == current_user.id,
            CalendarEvent.is_deleted == False,
            CalendarEvent.start_time >= today_start,
            CalendarEvent.start_time <= today_end
        ).order_by(CalendarEvent.start_time).all()
        
        events_data = []
        for event in today_events:
            event_dict = event.to_dict()
            events_data.append(event_dict)
        
        return jsonify({
            'success': True,
            'message': 'Today events retrieved successfully',
            'date': today,
            'events': events_data,
            'count': len(events_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve today events: {str(e)}'
        }), 500

@widget_bp.route('/task-stats', methods=['GET'])
@token_required
def get_task_stats(current_user):
    """获取任务统计数据接口（用于Widget）"""
    try:
        # 获取当前用户的所有任务（不包括已删除的）
        all_tasks = Task.query.filter(
            Task.user_id == current_user.id,
            Task.is_deleted == False
        ).all()
        
        # 统计各状态任务数
        total_tasks = len(all_tasks)
        todo_tasks = sum(1 for task in all_tasks if task.status == 'pending')
        in_progress_tasks = sum(1 for task in all_tasks if task.status == 'in_progress')
        completed_tasks = sum(1 for task in all_tasks if task.status == 'completed')
        
        # 统计过期任务（due_date < 当前日期 且 status != completed 且 status != cancelled）
        today = datetime.utcnow().date()
        overdue_tasks = 0
        for task in all_tasks:
            if task.due_date and task.status not in ['completed', 'cancelled']:
                try:
                    due_date_obj = datetime.strptime(task.due_date, '%Y-%m-%d').date()
                    if due_date_obj < today:
                        overdue_tasks += 1
                except (ValueError, TypeError):
                    # 如果日期格式不正确，跳过
                    pass
        
        return jsonify({
            'success': True,
            'message': '获取成功',
            'stats': {
                'total_tasks': total_tasks,
                'todo_tasks': todo_tasks,
                'in_progress_tasks': in_progress_tasks,
                'completed_tasks': completed_tasks,
                'overdue_tasks': overdue_tasks
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取任务统计数据失败: {str(e)}'
        }), 500

@widget_bp.route('/project-progress', methods=['GET'])
@token_required
def get_project_progress(current_user):
    """获取项目进度数据接口（用于Widget）"""
    try:
        project_id = request.args.get('project_id')
        
        # 如果提供了project_id，使用该项目；否则获取用户最近访问的项目
        if project_id:
            project = ProjectGroup.query.filter_by(id=project_id).first()
            if not project:
                return jsonify({
                    'success': True,
                    'message': '获取成功',
                    'progress': None
                }), 200
            
            # 检查用户是否有权限访问该项目
            if current_user not in project.members and project.leader_id != current_user.id:
                return jsonify({
                    'success': False,
                    'message': '无权限访问该项目'
                }), 403
        else:
            # 获取用户最近访问的项目（这里简化处理，返回用户加入的第一个项目）
            user_projects = [p for p in current_user.project_groups if p.is_active]
            if not user_projects:
                return jsonify({
                    'success': True,
                    'message': '获取成功',
                    'progress': None
                }), 200
            project = user_projects[0]
        
        # 获取项目的所有任务（不包括已删除的）
        project_tasks = Task.query.filter(
            Task.project_id == project.id,
            Task.is_deleted == False
        ).all()
        
        # 统计各状态任务数
        total_tasks = len(project_tasks)
        todo_tasks = sum(1 for task in project_tasks if task.status == 'pending')
        in_progress_tasks = sum(1 for task in project_tasks if task.status == 'in_progress')
        completed_tasks = sum(1 for task in project_tasks if task.status == 'completed')
        
        # 计算进度百分比
        if total_tasks > 0:
            progress_percentage = round((completed_tasks / total_tasks) * 100, 2)
        else:
            progress_percentage = 0.0
        
        return jsonify({
            'success': True,
            'message': '获取成功',
            'progress': {
                'project_id': project.id,
                'project_name': project.project_title,
                'total_tasks': total_tasks,
                'todo_tasks': todo_tasks,
                'in_progress_tasks': in_progress_tasks,
                'completed_tasks': completed_tasks,
                'progress_percentage': progress_percentage
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取项目进度数据失败: {str(e)}'
        }), 500

@widget_bp.route('/user-stats', methods=['GET'])
@token_required
def get_user_stats(current_user):
    """获取用户综合统计数据接口（用于Widget）"""
    try:
        # 统计已完成的任务数
        tasks_completed = Task.query.filter(
            Task.user_id == current_user.id,
            Task.status == 'completed',
            Task.is_deleted == False
        ).count()
        
        # 统计用户加入的项目数
        projects_joined = len([p for p in current_user.project_groups if p.is_active])
        
        # 统计用户上传的文件总数
        total_files = SharedFile.query.filter(
            SharedFile.user_id == current_user.id,
            SharedFile.is_deleted == False
        ).count()
        
        # 统计用户共享的文件数（如果文件模型中有is_shared字段）
        # 由于当前模型中没有is_shared字段，暂时使用total_files作为files_shared
        files_shared = total_files
        
        return jsonify({
            'success': True,
            'message': '获取成功',
            'stats': {
                'tasks_completed': tasks_completed,
                'projects_joined': projects_joined,
                'files_shared': files_shared,
                'total_files': total_files
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户统计数据失败: {str(e)}'
        }), 500

