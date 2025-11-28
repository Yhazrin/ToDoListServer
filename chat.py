from flask import Blueprint, request, jsonify
from models import db, User, ProjectGroup, GroupMessage
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

    # 查询历史消息
    messages = GroupMessage.query.filter_by(group_id=room_id)\
        .order_by(GroupMessage.sent_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    response = []
    for msg in messages.items:
        sender = User.query.get(msg.sender_id)
        response.append({
            'id': msg.id,
            'roomId': msg.group_id,
            'senderId': msg.sender_id,
            'senderName': sender.username if sender else 'Unknown',
            'content': msg.content,
            'timestamp': msg.sent_at
        })

    return jsonify({
        'messages': response,
        'page': messages.page,
        'pages': messages.pages,
        'total': messages.total
    })


@chat_bp.route('/rooms/<room_id>/messages', methods=['POST'])
@token_required
def send_message(current_user, room_id):
    """向指定聊天室发送消息"""
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'message': 'Invalid request body'}), 400

    # 验证用户是否是该项目组成员
    group = ProjectGroup.query.filter_by(id=room_id).first()
    if not group or current_user not in group.members:
        return jsonify({'message': 'Chat room not found or access denied'}), 404

    # 创建新消息
    new_message = GroupMessage(
        group_id=room_id,
        sender_id=current_user.id,
        content=data['content']
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
        'content': new_message.content,
        'timestamp': new_message.sent_at
    }

    # 通过WebSocket广播新消息（可选，如果SocketIO可用）
    try:
        from app import socketio
        if socketio:
            socketio.emit('new_message', {'type': 'new_message', 'payload': message_data}, room=str(room_id))
    except (ImportError, AttributeError):
        # SocketIO不可用时不广播，但不影响消息发送
        pass

    return jsonify(message_data), 201