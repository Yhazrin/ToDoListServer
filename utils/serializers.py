from datetime import datetime
from models import Task, User

def serialize_message(message_obj):
    """
    Serialize a GroupMessage object to a dictionary compatible with ChatMessageDto.
    Ensures consistency between HTTP API and WebSocket payloads.
    """
    
    # Fetch sender info
    sender = User.query.get(message_obj.sender_id)
    sender_name = sender.username if sender else 'Unknown'
    sender_avatar = sender.avatar_url if sender else None
    
    # Format updated_time
    updated_str = None
    try:
        if getattr(message_obj, 'updated_time', None) is not None:
            if isinstance(message_obj.updated_time, (int, float)):
                updated_str = datetime.utcfromtimestamp(int(message_obj.updated_time)).strftime('%Y-%m-%d %H:%M:%S')
            else:
                updated_str = str(message_obj.updated_time)
    except Exception:
        updated_str = None

    # Base dictionary
    message_dict = {
        'id': message_obj.id,
        'room_id': message_obj.group_id,
        'sender_id': message_obj.sender_id,
        'sender_name': sender_name,
        'sender_avatar': sender_avatar,
        'content': message_obj.content,
        'message_type': (message_obj.message_type or 'text').upper(),
        'file_url': message_obj.file_url,
        'task_id': message_obj.task_id,
        'created_at': message_obj.sent_at,
        'updated_time': updated_str
    }
    
    # Add reply_to_id
    if message_obj.reply_to_id:
        message_dict['reply_to_id'] = message_obj.reply_to_id
        
    # Add task info if exists
    if message_obj.task_id:
        task = Task.query.filter_by(id=message_obj.task_id, is_deleted=False).first()
        if task:
            message_dict['task'] = task.to_dict()

    return message_dict
