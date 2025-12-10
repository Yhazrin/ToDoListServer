import json
import time
from flask import request
from simple_websocket import ConnectionClosed
from app import sock
from utils.websocket_manager import ws_manager
from models import User, ProjectGroup, GroupMessage, Task
from models import db
from utils.serializers import serialize_message

@sock.route('/chat/ws')
def chat_socket(ws):
    """
    WebSocket endpoint for chat.
    URL: ws://domain/chat/ws?token=xxx&room_id=xxx
    """
    # 1. Authentication
    token = request.args.get('token')
    if not token:
        # Try headers (Flask-Sock allows access to request)
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split('Bearer ', 1)[1].strip()

    if not token:
        ws.send(json.dumps({
            "type": "error",
            "message": "Authentication failed: Token missing",
            "code": 401
        }))
        ws.close()
        return

    # Validate token (Logic from auth.token_required)
    user = User.query.filter(
        (User.id == token) | (User.username == token) | (User.email == token)
    ).first()

    if not user or not user.is_active:
        ws.send(json.dumps({
            "type": "error",
            "message": "Authentication failed: Invalid token",
            "code": 401
        }))
        ws.close()
        return

    # 2. Register connection
    ws_manager.connect(ws, user.id)
    
    # Send connected confirmation
    try:
        ws.send(json.dumps({
            "type": "connected",
            "message": "Connected successfully",
            "server_time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        }))
    except:
        pass

    # Auto-subscribe if room_id is provided in URL
    initial_room_id = request.args.get('room_id')
    if initial_room_id:
        handle_subscribe(ws, user, {"room_id": initial_room_id})

    # 3. Message Loop
    try:
        while True:
            data = ws.receive()
            if not data:
                break
            
            try:
                message = json.loads(data)
                msg_type = message.get('type')
                
                if msg_type == 'subscribe':
                    handle_subscribe(ws, user, message)
                elif msg_type == 'unsubscribe':
                    handle_unsubscribe(ws, user, message)
                elif msg_type == 'ping':
                    handle_ping(ws, message)
                elif msg_type == 'send_message':
                    handle_send_message(ws, user, message)
                else:
                    # Unknown type, ignore or send error
                    pass
                    
            except json.JSONDecodeError:
                ws.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "code": 400
                }))
            except Exception as e:
                print(f"Error processing message: {e}")
                ws.send(json.dumps({
                    "type": "error",
                    "message": "Internal server error",
                    "code": 500
                }))

    except ConnectionClosed:
        pass
    except Exception as e:
        print(f"WebSocket connection error: {e}")
    finally:
        ws_manager.disconnect(ws)

def handle_subscribe(ws, user, data):
    room_id = data.get('room_id')
    if not room_id:
        return

    # Verify permission (User must be member of the group)
    group = ProjectGroup.query.filter_by(id=room_id).first()
    if not group or user not in group.members:
        ws.send(json.dumps({
            "type": "error",
            "message": "Room not found or access denied",
            "code": 404
        }))
        return

    ws_manager.subscribe(ws, room_id)
    
    ws.send(json.dumps({
        "type": "subscribed",
        "room_id": room_id,
        "message": "Successfully subscribed to room"
    }))

def handle_unsubscribe(ws, user, data):
    room_id = data.get('room_id')
    if room_id:
        ws_manager.unsubscribe(ws, room_id)

def handle_ping(ws, data):
    timestamp = data.get('timestamp')
    ws.send(json.dumps({
        "type": "pong",
        "timestamp": timestamp
    }))

def handle_send_message(ws, user, data):
    """
    Handle sending message via WebSocket.
    This logic mirrors the HTTP POST /messages endpoint.
    """
    room_id = data.get('room_id')
    content = data.get('content', '')
    message_type = data.get('message_type', 'TEXT').lower()
    file_url = data.get('file_url')
    task_id = data.get('task_id')
    reply_to_id = data.get('reply_to_id')
    
    if not room_id:
        return
        
    # Permission check
    group = ProjectGroup.query.filter_by(id=room_id).first()
    if not group or user not in group.members:
        ws.send(json.dumps({
            "type": "error",
            "message": "Access denied",
            "code": 403
        }))
        return

    # Create message
    new_message = GroupMessage(
        group_id=room_id,
        sender_id=user.id,
        content=content,
        message_type=message_type,
        file_url=file_url,
        task_id=task_id,
        reply_to_id=reply_to_id
    )
    
    try:
        db.session.add(new_message)
        db.session.commit()
        
        # Serialize
        payload = serialize_message(new_message)
        
        # Confirmation to sender
        ws.send(json.dumps({
            "type": "message_sent",
            "message_id": new_message.id,
            "success": True,
            "error": None
        }))
        
        # Broadcast to room
        ws_manager.broadcast_to_room(
            room_id, 
            {
                "type": "new_message",
                "payload": payload
            }
        )
        
    except Exception as e:
        db.session.rollback()
        ws.send(json.dumps({
            "type": "message_sent",
            "message_id": None,
            "success": False,
            "error": str(e)
        }))

# Re-export socketio for backward compatibility if needed, though we don't use it here
from app import socketio
