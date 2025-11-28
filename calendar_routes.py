from flask import Blueprint, request, jsonify
from models import db, User, Task, CalendarEvent
from auth import token_required
from sqlalchemy.exc import IntegrityError
from datetime import datetime

calendar_bp = Blueprint('calendar', __name__, url_prefix='/calendar')

@calendar_bp.route('/events', methods=['GET'])
@token_required
def get_events(current_user):
    """获取用户的日历事件列表接口"""
    try:
        # 获取查询参数
        start_date = request.args.get('start_date')  # YYYY-MM-DD格式
        end_date = request.args.get('end_date')  # YYYY-MM-DD格式
        
        # 构建查询
        query = CalendarEvent.query.filter(
            CalendarEvent.user_id == current_user.id,
            CalendarEvent.is_deleted == False
        )
        
        # 按日期范围筛选
        if start_date:
            query = query.filter(CalendarEvent.start_time >= f'{start_date} 00:00:00')
        if end_date:
            query = query.filter(CalendarEvent.end_time <= f'{end_date} 23:59:59')
        
        events = query.order_by(CalendarEvent.start_time).all()
        
        return jsonify({
            'success': True,
            'message': 'Events retrieved successfully',
            'events': [event.to_dict() for event in events]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve events: {str(e)}'
        }), 500

@calendar_bp.route('/events', methods=['POST'])
@token_required
def create_event(current_user):
    """创建日历事件接口"""
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
        
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if not start_time or not end_time:
            return jsonify({
                'success': False,
                'message': 'Start time and end time are required'
            }), 400
        
        # 验证时间格式
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            if end_dt <= start_dt:
                return jsonify({
                    'success': False,
                    'message': 'End time must be after start time'
                }), 400
            
            start_time_str = start_dt.strftime('%Y-%m-%d %H:%M:%S')
            end_time_str = end_dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid time format, please use ISO format'
            }), 400
        
        # 验证任务ID（如果提供）
        task_id = data.get('task_id')
        if task_id:
            task = Task.query.filter_by(id=task_id, is_deleted=False).first()
            if not task:
                return jsonify({
                    'success': False,
                    'message': 'Task not found'
                }), 404
            
            if task.user_id != current_user.id:
                return jsonify({
                    'success': False,
                    'message': 'Permission denied: Cannot create event for other user\'s task'
                }), 403
        
        # 创建新事件
        new_event = CalendarEvent(
            user_id=current_user.id,
            title=title,
            start_time=start_time_str,
            end_time=end_time_str,
            task_id=task_id,
            description=data.get('description'),
            location=data.get('location')
        )
        
        db.session.add(new_event)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Event created successfully',
            'event': new_event.to_dict()
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
            'message': f'Failed to create event: {str(e)}'
        }), 500

@calendar_bp.route('/events/<event_id>', methods=['GET'])
@token_required
def get_event(current_user, event_id):
    """获取日历事件详情接口"""
    try:
        event = CalendarEvent.query.filter_by(id=event_id, is_deleted=False).first()
        if not event:
            return jsonify({
                'success': False,
                'message': 'Event not found'
            }), 404
        
        # 检查权限
        if event.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Permission denied'
            }), 403
        
        return jsonify({
            'success': True,
            'message': 'Event retrieved successfully',
            'event': event.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve event: {str(e)}'
        }), 500

@calendar_bp.route('/events/<event_id>', methods=['PUT'])
@token_required
def update_event(current_user, event_id):
    """更新日历事件接口"""
    try:
        event = CalendarEvent.query.filter_by(id=event_id, is_deleted=False).first()
        if not event:
            return jsonify({
                'success': False,
                'message': 'Event not found'
            }), 404
        
        # 检查权限
        if event.user_id != current_user.id:
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
        
        # 更新事件字段
        if 'title' in data:
            title = data['title'].strip()
            if title:
                event.title = title
        
        if 'description' in data:
            event.description = data['description']
        
        if 'location' in data:
            event.location = data['location']
        
        if 'start_time' in data or 'end_time' in data:
            start_time = data.get('start_time', event.start_time)
            end_time = data.get('end_time', event.end_time)
            
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                
                if end_dt <= start_dt:
                    return jsonify({
                        'success': False,
                        'message': 'End time must be after start time'
                    }), 400
                
                event.start_time = start_dt.strftime('%Y-%m-%d %H:%M:%S')
                event.end_time = end_dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid time format, please use ISO format'
                }), 400
        
        if 'task_id' in data:
            task_id = data['task_id']  # 可以是null
            if task_id:
                task = Task.query.filter_by(id=task_id, is_deleted=False).first()
                if not task:
                    return jsonify({
                        'success': False,
                        'message': 'Task not found'
                    }), 404
                
                if task.user_id != current_user.id:
                    return jsonify({
                        'success': False,
                        'message': 'Permission denied: Cannot link to other user\'s task'
                    }), 403
            
            event.task_id = task_id
        
        event.updated_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Event updated successfully',
            'event': event.to_dict()
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
            'message': f'Failed to update event: {str(e)}'
        }), 500

@calendar_bp.route('/events/<event_id>', methods=['DELETE'])
@token_required
def delete_event(current_user, event_id):
    """删除日历事件接口（软删除）"""
    try:
        event = CalendarEvent.query.filter_by(id=event_id, is_deleted=False).first()
        if not event:
            return jsonify({
                'success': False,
                'message': 'Event not found'
            }), 404
        
        # 检查权限
        if event.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Permission denied'
            }), 403
        
        # 软删除
        event.is_deleted = True
        event.updated_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Event deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to delete event: {str(e)}'
        }), 500

@calendar_bp.route('/from-task/<task_id>', methods=['POST'])
@token_required
def create_event_from_task(current_user, task_id):
    """从任务创建日历事件接口"""
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
        
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if not start_time or not end_time:
            return jsonify({
                'success': False,
                'message': 'Start time and end time are required'
            }), 400
        
        # 验证时间格式
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            if end_dt <= start_dt:
                return jsonify({
                    'success': False,
                    'message': 'End time must be after start time'
                }), 400
            
            start_time_str = start_dt.strftime('%Y-%m-%d %H:%M:%S')
            end_time_str = end_dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid time format, please use ISO format'
            }), 400
        
        # 从任务创建事件
        new_event = CalendarEvent(
            user_id=current_user.id,
            title=task.title,
            start_time=start_time_str,
            end_time=end_time_str,
            task_id=task_id,
            description=task.description,
            location=data.get('location')
        )
        
        db.session.add(new_event)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Event created from task successfully',
            'event': new_event.to_dict()
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
            'message': f'Failed to create event from task: {str(e)}'
        }), 500

