from flask import Blueprint, request, jsonify
from models import db, User, Task, CalendarEvent
from auth import token_required
from datetime import datetime

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

