import json
from threading import Lock
from typing import Dict, Set, Optional

class ConnectionManager:
    """
    WebSocket Connection Manager
    Manages active WebSocket connections and room subscriptions.
    """
    def __init__(self):
        # Stores all active connections: {ws_obj: user_id}
        self.active_connections: Dict[object, str] = {}
        
        # Stores room subscriptions: {room_id: {ws_obj1, ws_obj2, ...}}
        self.room_subscriptions: Dict[str, Set[object]] = {}
        
        # Stores user connections: {user_id: {ws_obj1, ws_obj2, ...}}
        self.user_connections: Dict[str, Set[object]] = {}
        
        # Lock for thread safety
        self.lock = Lock()

    def connect(self, ws, user_id: str):
        """Register a new connection"""
        with self.lock:
            self.active_connections[ws] = user_id
            
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(ws)
            print(f"WS Connected: User {user_id}")

    def disconnect(self, ws):
        """Unregister a connection"""
        with self.lock:
            user_id = self.active_connections.pop(ws, None)
            
            # Remove from user connections
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(ws)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove from all rooms
            for room_id in list(self.room_subscriptions.keys()):
                if ws in self.room_subscriptions[room_id]:
                    self.room_subscriptions[room_id].discard(ws)
                    if not self.room_subscriptions[room_id]:
                        del self.room_subscriptions[room_id]
            
            print(f"WS Disconnected: User {user_id}")

    def subscribe(self, ws, room_id: str):
        """Subscribe a connection to a room"""
        with self.lock:
            if room_id not in self.room_subscriptions:
                self.room_subscriptions[room_id] = set()
            self.room_subscriptions[room_id].add(ws)
            print(f"WS Subscribed: Room {room_id}")

    def unsubscribe(self, ws, room_id: str):
        """Unsubscribe a connection from a room"""
        with self.lock:
            if room_id in self.room_subscriptions:
                self.room_subscriptions[room_id].discard(ws)
                if not self.room_subscriptions[room_id]:
                    del self.room_subscriptions[room_id]
            print(f"WS Unsubscribed: Room {room_id}")

    def broadcast_to_room(self, room_id: str, message: dict, exclude_ws=None):
        """Broadcast a message to all connections in a room"""
        # We copy the set to avoid modification during iteration
        # Note: Sending over WS might be blocking depending on implementation, 
        # but simple-websocket usually handles this well.
        # For high concurrency, we might want to put this in a queue.
        connections = set()
        with self.lock:
            if room_id in self.room_subscriptions:
                connections = self.room_subscriptions[room_id].copy()
        
        json_msg = json.dumps(message)
        
        for ws in connections:
            if ws == exclude_ws:
                continue
            try:
                ws.send(json_msg)
            except Exception as e:
                print(f"Error broadcasting to WS: {e}")
                # Ideally we should disconnect dead sockets here, 
                # but the main loop handles that.
                pass

    def send_personal_message(self, user_id: str, message: dict):
        """Send a message to a specific user"""
        connections = set()
        with self.lock:
            if user_id in self.user_connections:
                connections = self.user_connections[user_id].copy()
        
        json_msg = json.dumps(message)
        for ws in connections:
            try:
                ws.send(json_msg)
            except Exception as e:
                print(f"Error sending personal message: {e}")

# Global instance
ws_manager = ConnectionManager()
