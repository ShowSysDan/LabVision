from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Monitor(db.Model):
    """Monitor configuration for tracking specific locations"""
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    
    # Webhook configuration
    webhook_enabled = db.Column(db.Boolean, default=False)
    webhook_url = db.Column(db.String(500))
    webhook_method = db.Column(db.String(10), default='POST')  # POST or GET
    webhook_headers = db.Column(db.Text)  # JSON string of headers
    webhook_body_template = db.Column(db.Text)  # Template for POST body
    
    # Status tracking
    is_active = db.Column(db.Boolean, default=False)
    current_event = db.Column(db.Text)  # JSON string
    next_event = db.Column(db.Text)  # JSON string
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Display settings
    enabled = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert monitor to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'webhook_enabled': self.webhook_enabled,
            'webhook_url': self.webhook_url,
            'webhook_method': self.webhook_method,
            'webhook_headers': json.loads(self.webhook_headers) if self.webhook_headers else {},
            'webhook_body_template': self.webhook_body_template,
            'is_active': self.is_active,
            'current_event': json.loads(self.current_event) if self.current_event else None,
            'next_event': json.loads(self.next_event) if self.next_event else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'enabled': self.enabled,
            'order': self.order
        }
    
    def set_webhook_headers(self, headers_dict):
        """Set webhook headers from dictionary"""
        self.webhook_headers = json.dumps(headers_dict) if headers_dict else None
    
    def get_webhook_headers(self):
        """Get webhook headers as dictionary"""
        return json.loads(self.webhook_headers) if self.webhook_headers else {}


class SystemState(db.Model):
    """System-wide state and cached data"""
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get(key, default=None):
        """Get a value by key"""
        state = SystemState.query.filter_by(key=key).first()
        if state:
            try:
                return json.loads(state.value)
            except:
                return state.value
        return default
    
    @staticmethod
    def set(key, value):
        """Set a value by key"""
        state = SystemState.query.filter_by(key=key).first()
        if not state:
            state = SystemState(key=key)
        
        if isinstance(value, (dict, list)):
            state.value = json.dumps(value)
        else:
            state.value = str(value)
        
        state.updated_at = datetime.utcnow()
        db.session.add(state)
        db.session.commit()
