from flask import Blueprint, request, jsonify
from models import db, User, ProjectGroup, GroupMessage, Task, SharedFile
from auth import token_required

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/rooms', methods=['GET'])
@token_required
def get_chat_rooms(current_user):
    """获取当前用户的聊天室列表"""
    # 获取用户所在的所有项目组
    groups = current_user.project_groups

    chat_rooms = []
    for group in groups:
        # 获取最新的消息
        last_message = GroupMessage.query.filter_by(group_id=group.id).order_by(GroupMessage.sent_at.desc()).first()

        # 获取未读消息数 (需要 MessageReadStatus 模型支持)
        # 此处为简化实现，未读消息数暂时为0
        unread_count = 0

        chat_rooms.append({
            'id': group.id,
            'name': group.name,
            'lastMessage': last_message.content if last_message else None,
            'lastMessageTimestamp': last_message.sent_at if last_message else None,
            'unreadCount': unread_count
        })

    return jsonify(chat_rooms)


@chat_bp.route('/rooms/<room_id>/messages', methods=['GET'])
@token_required
def get_messages(current_user, room_id):
    """分页获取指定聊天室的历史消息"""
    # 验证用户是否是该项目组成员
    group = ProjectGroup.query.filter_by(id=room_id).first()
    if not group or current_user not in group.members:
        return jsonify({'message': 'Chat room not found or access denied'}), 404

    # 分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # 查询历史消息（排除已删除的消息）
    messages = GroupMessage.query.filter_by(
        group_id=room_id,
        is_deleted=False
    ).order_by(GroupMessage.sent_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    response = []
    for msg in messages.items:
        sender = User.query.get(msg.sender_id)
        message_dict = {
            'id': msg.id,
            'roomId': msg.group_id,
            'senderId': msg.sender_id,
            'senderName': sender.username if sender else 'Unknown',
            'messageType': msg.message_type,
            'content': msg.content,
            'timestamp': msg.sent_at,
            'updatedTime': msg.updated_time if hasattr(msg, 'updated_time') else None
        }
        
        # 添加回复消息ID（如果存在）
        if msg.reply_to_id:
            message_dict['replyToId'] = msg.reply_to_id
        
        # 添加文件URL（如果是文件类型消息）
        if msg.file_url:
            message_dict['fileUrl'] = msg.file_url
        
        # 添加任务信息（如果是任务类型消息）
        if msg.task_id:
            task = Task.query.filter_by(id=msg.task_id, is_deleted=False).first()
            if task:
                message_dict['task'] = task.to_dict()
                message_dict['taskId'] = msg.task_id
        
        response.append(message_dict)

    return jsonify({
        'messages': response,
        'page': messages.page,
        'pages': messages.pages,
        'total': messages.total
    })


@chat_bp.route('/rooms/<room_id>/messages', methods=['POST'])
@token_required
def send_message(current_user, room_id):
    """向指定聊天室发送消息（支持多种消息类型）"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request body'}), 400

    # 验证用户是否是该项目组成员
    group = ProjectGroup.query.filter_by(id=room_id).first()
    if not group or current_user not in group.members:
        return jsonify({'success': False, 'message': 'Chat room not found or access denied'}), 404

    # 获取消息类型，默认为text
    message_type = data.get('messageType', 'text')
    if message_type not in ['text', 'image', 'video', 'audio', 'file', 'task']:
        return jsonify({'success': False, 'message': 'Invalid message type'}), 400
    
    content = data.get('content', '')
    file_url = data.get('fileUrl')
    task_id = data.get('taskId')
    reply_to_id = data.get('replyToId')  # 支持回复消息功能
    
    # 验证文件URL（如果是文件类型消息）
    if message_type in ['image', 'video', 'audio', 'file']:
        if not file_url:
            return jsonify({'success': False, 'message': f'File URL or File ID is required for {message_type} message'}), 400
        
        # 从file_url中提取文件ID（可能是完整URL或文件ID）
        file_id = file_url
        if '/' in file_url:
            # 如果是URL，尝试提取文件ID（假设是/files/{fileId}格式）
            parts = file_url.split('/')
            file_id = parts[-1] if parts else file_url
        
        # 验证文件存在且有权限访问
        file = SharedFile.query.filter_by(id=file_id, is_deleted=False).first()
        if not file:
            return jsonify({'success': False, 'message': 'File not found'}), 404
        
        # 检查权限
        if file.user_id != current_user.id:
            if file.group_id != room_id:
                return jsonify({'success': False, 'message': 'Permission denied: File does not belong to this group'}), 403
    
    # 验证任务ID（如果是任务类型消息）
    if message_type == 'task':
        if not task_id:
            return jsonify({'success': False, 'message': 'Task ID is required for task message'}), 400
        
        task = Task.query.filter_by(id=task_id, is_deleted=False).first()
        if not task:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        # 验证任务权限：任务所有者或项目组成员
        if task.user_id != current_user.id:
            if task.project_id != room_id:
                return jsonify({'success': False, 'message': 'Permission denied: Task does not belong to this group'}), 403
    
    # 验证回复消息ID（如果提供）
    if reply_to_id:
        reply_message = GroupMessage.query.filter_by(id=reply_to_id, group_id=room_id, is_deleted=False).first()
        if not reply_message:
            return jsonify({'success': False, 'message': 'Reply message not found'}), 404
    
    # 创建新消息
    new_message = GroupMessage(
        group_id=room_id,
        sender_id=current_user.id,
        content=content,
        message_type=message_type,
        file_url=file_url,
        task_id=task_id,
        reply_to_id=reply_to_id
    )
    db.session.add(new_message)
    db.session.commit()

    # 构造完整的消息对象用于返回和WebSocket广播
    sender = User.query.get(new_message.sender_id)
    message_data = {
        'id': new_message.id,
        'roomId': new_message.group_id,
        'senderId': new_message.sender_id,
        'senderName': sender.username if sender else 'Unknown',
        'messageType': new_message.message_type,
        'content': new_message.content,
        'timestamp': new_message.sent_at,
        'updatedTime': new_message.updated_time if hasattr(new_message, 'updated_time') else None
    }
    
    # 添加回复消息ID
    if new_message.reply_to_id:
        message_data['replyToId'] = new_message.reply_to_id
    
    # 添加文件URL
    if new_message.file_url:
        message_data['fileUrl'] = new_message.file_url
    
    # 添加任务信息
    if new_message.task_id:
        task = Task.query.filter_by(id=new_message.task_id, is_deleted=False).first()
        if task:
            message_data['task'] = task.to_dict()
            message_data['taskId'] = new_message.task_id

    # 通过WebSocket广播新消息（可选，如果SocketIO可用）
    try:
        from app import socketio
        if socketio:
            socketio.emit('new_message', {'type': 'new_message', 'payload': message_data}, room=str(room_id))
    except (ImportError, AttributeError):
        # SocketIO不可用时不广播，但不影响消息发送
        pass

    return jsonify(message_data), 201