from flask import Blueprint, request, jsonify
from models import db, Task, User
from auth import token_required
from datetime import datetime

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notifications_bp.route('/task-reminder', methods=['POST'])
@token_required
def task_reminder(current_user):
    try:
        data = request.get_json() or {}
        task_id = data.get('task_id')
        user_id = data.get('user_id') or current_user.id

        task = Task.query.filter_by(id=task_id, is_deleted=False).first() if task_id else None
        if task and current_user.id not in [task.user_id, task.assigned_to]:
            return jsonify({'success': False, 'message': 'Permission denied'}), 403

        # 选择提醒日期：优先 due_date，其次 end_date
        reminder_date = (task.due_date if task else None) or (task.end_date if task else None) or data.get('date')
        if not reminder_date:
            return jsonify({'success': False, 'message': 'No reminder date provided'}), 400

        # 这里模拟服务端生成提醒（实际应推送到消息队列或第三方服务）
        payload = {
            'user_id': user_id,
            'task_id': task_id,
            'date': reminder_date,
            'title': task.title if task else data.get('title', 'Task Reminder'),
            'created_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }
        return jsonify({'success': True, 'message': 'Reminder scheduled', 'reminder': payload}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to schedule reminder: {str(e)}'}), 500

