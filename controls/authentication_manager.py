import hashlib
import uuid

class AuthenticationManager:
    def __init__(self, database):
        self.database = database
        self.active_sessions_map = {}
        self.max_login_attempts = 3
        self.failed_login_attempts = {}
        
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def login (self, email_address, password):
        user = self.database.execute_query("find_user_by_email", email_address)
        
        if user is None:
            return None

        if user._password != self.hash_password(password):
            return None
        
        session_id = str(uuid.uuid4())
        self.active_sessions_map[session_id] = user
        return session_id
    
    def logout(self, session_id):
        if session_id in self.active_sessions_map:
            del self.active_sessions_map[session_id]
            return True
        return False
    
    def verify_role(self, session_id, role_class):
        user = self.active_sessions_map.get(session_id)
        if user is None:
            return False
        return isinstance(user, role_class)