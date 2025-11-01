"""API endpoints for notification system"""
from flask import Blueprint, jsonify
from backend.agent_orchestrator import get_notifications, mark_notification_read, clear_all_notifications

notification_bp = Blueprint('notifications', __name__)

@notification_bp.route('/api/notifications', methods=['GET'])
def get_all_notifications():
    """Get all AI agent notifications"""
    try:
        notifications = get_notifications()
        return jsonify({'success': True, 'notifications': notifications})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@notification_bp.route('/api/notifications/<int:index>/read', methods=['POST'])
def mark_read(index):
    """Mark notification as read"""
    try:
        mark_notification_read(index)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@notification_bp.route('/api/notifications/clear', methods=['POST'])
def clear_notifications():
    """Clear all notifications"""
    try:
        clear_all_notifications()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

