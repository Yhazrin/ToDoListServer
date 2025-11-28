from flask_socketio import join_room, leave_room
from app import socketio

@socketio.on('subscribe')
def handle_subscribe(data):
    """客户端订阅房间"""
    room_id = data.get('roomId')
    if room_id:
        join_room(room_id)
        print(f"Client subscribed to room: {room_id}")

@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    """客户端取消订阅房间"""
    room_id = data.get('roomId')
    if room_id:
        leave_room(room_id)
        print(f"Client unsubscribed from room: {room_id}")