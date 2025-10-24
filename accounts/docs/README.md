# Admin User Management System

## Overview

Enterprise-level admin user management system for MedixMall e-commerce platform with comprehensive features for managing users, roles, permissions, and analytics.

## 🚀 Features

### User Management
- **CRUD Operations**: Create, Read, Update, Delete users
- **Role Management**: Manage user roles (user, supplier, admin, rx_verifier)
- **Status Management**: Activate/Deactivate user accounts
- **Bulk Operations**: Perform actions on multiple users simultaneously
- **Advanced Filtering**: Filter by role, status, email verification, date ranges
- **Search**: Search users by email, name, or contact
- **CSV Export**: Export user data for reporting

### Analytics & Reporting
- **User Statistics**: Total users, active/inactive, verified/unverified
- **Growth Metrics**: New users (daily, weekly, monthly)
- **Role Distribution**: Users breakdown by role
- **Audit Logs**: Complete audit trail of all admin actions

### Security
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Admin-only access to management endpoints
- **Self-Protection**: Cannot delete or modify own admin account
- **Audit Trail**: All actions logged for compliance

## 📁 File Structure

```
accounts/
├── admin_serializers.py       # Serializers for admin operations
├── admin_views.py              # Admin API views
├── docs/
│   ├── ADMIN_API_DOCUMENTATION.md      # Complete API documentation
│   └── FRONTEND_IMPLEMENTATION_GUIDE.md # Frontend integration guide
└── tests_admin/
    ├── __init__.py
    ├── test_admin_user_management.py  # Comprehensive test suite
    └── run_verification.py            # Verification checklist
```

## 🔗 API Endpoints

### User Management
- `GET /api/accounts/admin/users/` - List all users (with filtering)
- `GET /api/accounts/admin/users/{id}/` - Get user details
- `POST /api/accounts/admin/users/create/` - Create new user
- `PATCH /api/accounts/admin/users/{id}/update/` - Update user
- `DELETE /api/accounts/admin/users/{id}/delete/` - Delete user (soft delete)

### Role & Status Management
- `POST /api/accounts/admin/users/{user_id}/change-role/` - Change user role
- `POST /api/accounts/admin/users/{user_id}/change-status/` - Activate/Deactivate

### Bulk Operations
- `POST /api/accounts/admin/users/bulk-action/` - Bulk actions (activate, deactivate, verify, delete)

### Search & Export
- `GET /api/accounts/admin/users/search/` - Search users
- `GET /api/accounts/admin/users/export/` - Export to CSV

### Analytics
- `GET /api/accounts/admin/statistics/` - User statistics
- `GET /api/accounts/admin/audit-logs/` - Audit logs

### Special
- `POST /api/accounts/admin/rx-verifiers/create/` - Create RX Verifier account

## 🔧 Usage Examples

### List Users with Filters
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.medixmall.com/api/accounts/admin/users/?role=supplier&is_active=true"
```

### Create User
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "full_name": "New User",
    "contact": "9876543210",
    "role": "user",
    "password": "securePassword123",
    "password2": "securePassword123",
    "email_verified": true
  }' \
  "https://api.medixmall.com/api/accounts/admin/users/create/"
```

### Bulk Activate Users
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": [1, 2, 3, 4, 5],
    "action": "activate",
    "reason": "Approved after verification"
  }' \
  "https://api.medixmall.com/api/accounts/admin/users/bulk-action/"
```

## 📚 Documentation

- **API Documentation**: [ADMIN_API_DOCUMENTATION.md](docs/ADMIN_API_DOCUMENTATION.md)
- **Frontend Guide**: [FRONTEND_IMPLEMENTATION_GUIDE.md](docs/FRONTEND_IMPLEMENTATION_GUIDE.md)

## 🧪 Testing

Run tests:
```bash
python manage.py test accounts.tests_admin
```

Run verification:
```bash
python accounts/tests_admin/run_verification.py
```

## 🔒 Security Considerations

1. **Always use HTTPS** in production
2. **Secure token storage** on frontend
3. **Rate limiting** implemented on all endpoints
4. **Audit logging** for compliance
5. **Role-based permissions** enforced
6. **Input validation** on all endpoints

## 🎯 Frontend Integration

See [FRONTEND_IMPLEMENTATION_GUIDE.md](docs/FRONTEND_IMPLEMENTATION_GUIDE.md) for:
- React/Next.js examples
- State management with Zustand/Redux
- API integration with React Query
- Complete component examples
- Error handling patterns
- TypeScript types

## 📊 Admin Statistics Example Response

```json
{
  "total_users": 1500,
  "active_users": 1420,
  "inactive_users": 80,
  "verified_users": 1380,
  "unverified_users": 120,
  "users_by_role": {
    "user": 1200,
    "supplier": 250,
    "admin": 5,
    "rx_verifier": 45
  },
  "new_users_today": 12,
  "new_users_this_week": 85,
  "new_users_this_month": 340,
  "growth_rate": {
    "current_month": 340,
    "previous_month": 280,
    "percentage": 21.43
  }
}
```

## 🆘 Support

For questions or issues:
- **Email**: support@medixmall.com
- **Documentation**: https://docs.medixmall.com
- **API Status**: https://status.medixmall.com

## 📝 License

Proprietary - MedixMall E-commerce Platform

---

**Version**: 1.0.0  
**Last Updated**: October 25, 2025  
**Author**: MedixMall Development Team
