"""
Backward compatibility shim for user models.

This module provides backward compatibility by importing models from the new
user package structure.
"""
from .user import (Group, GroupInvitation, GroupMembership, LoginCode,
                   PasswordResetToken, UserProfile, get_user_by_email)

__all__ = [
    'get_user_by_email',
    'Group',
    'GroupInvitation',
    'GroupMembership',
    'UserProfile',
    'LoginCode',
    'PasswordResetToken',
]
