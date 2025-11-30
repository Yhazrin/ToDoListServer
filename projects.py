from flask import Blueprint, request, jsonify
from models import db, ProjectGroup, Task
from auth import token_required
from datetime import datetime

projects_bp = Blueprint('projects', __name__, url_prefix='/projects')

@projects_bp.route('/<project_id>/stats', methods=['GET'])
@token_required
def project_stats(current_user, project_id):
    try:
        project = ProjectGroup.query.filter_by(id=project_id).first()
        if not project:
            return jsonify({'success': False, 'message': 'Project not found'}), 404
        if current_user not in project.members and project.leader_id != current_user.id:
            return jsonify({'success': False, 'message': 'Permission denied'}), 403

        tasks = Task.query.filter(Task.project_id == project_id, Task.is_deleted == False).all()
        total = len(tasks)
        completed = len([t for t in tasks if t.status == 'completed'])
        rate = round((completed / total * 100) if total > 0 else 0, 2)

        # 每日分布：按 end_date 统计完成/未完成数量
        daily = {}
        for t in tasks:
            day = t.end_date
            if not day:
                continue
            if day not in daily:
                daily[day] = {'total': 0, 'completed': 0}
            daily[day]['total'] += 1
            if t.status == 'completed':
                daily[day]['completed'] += 1

        return jsonify({
            'success': True,
            'message': 'Project stats retrieved',
            'stats': {
                'total': total,
                'completed': completed,
                'completion_rate': rate,
                'daily_distribution': daily
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to get stats: {str(e)}'}), 500
