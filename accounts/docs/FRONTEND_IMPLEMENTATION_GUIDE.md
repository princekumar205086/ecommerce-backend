# Frontend Implementation Guide - Admin User Management

## Table of Contents
1. [Overview](#overview)
2. [Setup & Installation](#setup--installation)
3. [Authentication](#authentication)
4. [State Management](#state-management)
5. [API Integration](#api-integration)
6. [Component Examples](#component-examples)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)

---

## Overview

This guide provides comprehensive examples for implementing the Admin User Management features in your frontend application using React/Next.js.

### Tech Stack Recommendations
- **React 18+** or **Next.js 14+**
- **TypeScript** (strongly recommended)
- **Axios** or **Fetch** for API calls
- **React Query** or **SWR** for data fetching
- **Zustand** or **Redux** for state management
- **React Hook Form** for forms
- **Tailwind CSS** or **Material-UI** for styling

---

## Setup & Installation

### Install Dependencies

```bash
npm install axios react-query @tanstack/react-query zustand react-hook-form
# or
yarn add axios react-query @tanstack/react-query zustand react-hook-form
```

### Create API Configuration

Create `src/lib/api.ts`:

```typescript
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.medixmall.com';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${API_BASE_URL}/api/accounts/token/refresh/`, {
          refresh: refreshToken,
        });

        const { access } = response.data;
        localStorage.setItem('access_token', access);

        originalRequest.headers.Authorization = `Bearer ${access}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Redirect to login
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
```

---

## Authentication

### Auth Store (Zustand)

Create `src/stores/authStore.ts`:

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'admin' | 'user' | 'supplier' | 'rx_verifier';
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAdmin: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,

      login: async (email, password) => {
        try {
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/accounts/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
          });

          if (!response.ok) throw new Error('Login failed');

          const data = await response.json();
          
          set({
            user: data.user,
            accessToken: data.access,
            refreshToken: data.refresh,
          });

          localStorage.setItem('access_token', data.access);
          localStorage.setItem('refresh_token', data.refresh);
        } catch (error) {
          throw error;
        }
      },

      logout: () => {
        set({ user: null, accessToken: null, refreshToken: null });
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      },

      isAdmin: () => {
        const { user } = get();
        return user?.role === 'admin';
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

### Protected Route Component

Create `src/components/ProtectedRoute.tsx`:

```typescript
import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuthStore } from '@/stores/authStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAdmin?: boolean;
}

export default function ProtectedRoute({ children, requireAdmin = false }: ProtectedRouteProps) {
  const router = useRouter();
  const { user, isAdmin } = useAuthStore();

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }

    if (requireAdmin && !isAdmin()) {
      router.push('/unauthorized');
    }
  }, [user, requireAdmin]);

  if (!user || (requireAdmin && !isAdmin())) {
    return <div>Loading...</div>;
  }

  return <>{children}</>;
}
```

---

## State Management

### User Management Store

Create `src/stores/userManagementStore.ts`:

```typescript
import { create } from 'zustand';
import { api } from '@/lib/api';

interface User {
  id: number;
  email: string;
  full_name: string;
  contact: string;
  role: string;
  is_active: boolean;
  email_verified: boolean;
}

interface UserFilters {
  role?: string;
  is_active?: boolean;
  email_verified?: boolean;
  search?: string;
}

interface UserManagementState {
  users: User[];
  loading: boolean;
  error: string | null;
  filters: UserFilters;
  pagination: {
    page: number;
    pageSize: number;
    total: number;
  };
  fetchUsers: () => Promise<void>;
  setFilters: (filters: UserFilters) => void;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
}

export const useUserManagementStore = create<UserManagementState>((set, get) => ({
  users: [],
  loading: false,
  error: null,
  filters: {},
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0,
  },

  fetchUsers: async () => {
    set({ loading: true, error: null });
    
    try {
      const { filters, pagination } = get();
      const params = new URLSearchParams({
        page: pagination.page.toString(),
        page_size: pagination.pageSize.toString(),
        ...filters,
      });

      const response = await api.get(`/api/accounts/admin/users/?${params}`);
      
      set({
        users: response.data.results,
        pagination: {
          ...pagination,
          total: response.data.count,
        },
        loading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.error || 'Failed to fetch users',
        loading: false,
      });
    }
  },

  setFilters: (filters) => {
    set({ filters, pagination: { ...get().pagination, page: 1 } });
    get().fetchUsers();
  },

  setPage: (page) => {
    set({ pagination: { ...get().pagination, page } });
    get().fetchUsers();
  },

  setPageSize: (pageSize) => {
    set({ pagination: { ...get().pagination, pageSize, page: 1 } });
    get().fetchUsers();
  },
}));
```

---

## API Integration

### API Service Layer

Create `src/services/userService.ts`:

```typescript
import { api } from '@/lib/api';

export interface CreateUserData {
  email: string;
  full_name: string;
  contact: string;
  role: string;
  password: string;
  password2: string;
  is_active?: boolean;
  email_verified?: boolean;
  send_credentials_email?: boolean;
}

export interface UpdateUserData {
  full_name?: string;
  contact?: string;
  is_active?: boolean;
  email_verified?: boolean;
}

export interface BulkActionData {
  user_ids: number[];
  action: 'activate' | 'deactivate' | 'verify_email' | 'delete';
  reason?: string;
}

export const userService = {
  // List users
  listUsers: async (params?: Record<string, any>) => {
    const response = await api.get('/api/accounts/admin/users/', { params });
    return response.data;
  },

  // Get user details
  getUserDetails: async (userId: number) => {
    const response = await api.get(`/api/accounts/admin/users/${userId}/`);
    return response.data;
  },

  // Create user
  createUser: async (data: CreateUserData) => {
    const response = await api.post('/api/accounts/admin/users/create/', data);
    return response.data;
  },

  // Update user
  updateUser: async (userId: number, data: UpdateUserData) => {
    const response = await api.patch(`/api/accounts/admin/users/${userId}/update/`, data);
    return response.data;
  },

  // Change role
  changeRole: async (userId: number, role: string, reason?: string) => {
    const response = await api.post(`/api/accounts/admin/users/${userId}/change-role/`, {
      role,
      reason,
    });
    return response.data;
  },

  // Change status
  changeStatus: async (userId: number, is_active: boolean, reason?: string) => {
    const response = await api.post(`/api/accounts/admin/users/${userId}/change-status/`, {
      is_active,
      reason,
    });
    return response.data;
  },

  // Delete user
  deleteUser: async (userId: number) => {
    const response = await api.delete(`/api/accounts/admin/users/${userId}/delete/`);
    return response.data;
  },

  // Bulk actions
  bulkAction: async (data: BulkActionData) => {
    const response = await api.post('/api/accounts/admin/users/bulk-action/', data);
    return response.data;
  },

  // Search users
  searchUsers: async (query: string) => {
    const response = await api.get('/api/accounts/admin/users/search/', {
      params: { q: query },
    });
    return response.data;
  },

  // Get statistics
  getStatistics: async () => {
    const response = await api.get('/api/accounts/admin/statistics/');
    return response.data;
  },

  // Export users
  exportUsers: async (filters?: Record<string, any>) => {
    const response = await api.get('/api/accounts/admin/users/export/', {
      params: filters,
      responseType: 'blob',
    });
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `users_export_${new Date().toISOString()}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },

  // Get audit logs
  getAuditLogs: async (params?: Record<string, any>) => {
    const response = await api.get('/api/accounts/admin/audit-logs/', { params });
    return response.data;
  },
};
```

---

## Component Examples

### 1. User List Component

Create `src/components/admin/UserList.tsx`:

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userService } from '@/services/userService';

export default function UserList() {
  const [filters, setFilters] = useState({
    role: '',
    is_active: '',
    search: '',
  });
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();

  // Fetch users
  const { data, isLoading, error } = useQuery({
    queryKey: ['users', filters, page],
    queryFn: () => userService.listUsers({ ...filters, page }),
  });

  // Delete user mutation
  const deleteMutation = useMutation({
    mutationFn: userService.deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      alert('User deactivated successfully');
    },
  });

  const handleDelete = (userId: number) => {
    if (confirm('Are you sure you want to deactivate this user?')) {
      deleteMutation.mutate(userId);
    }
  };

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading users</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">User Management</h1>

      {/* Filters */}
      <div className="mb-6 grid grid-cols-3 gap-4">
        <input
          type="text"
          placeholder="Search users..."
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          className="px-4 py-2 border rounded"
        />
        
        <select
          value={filters.role}
          onChange={(e) => setFilters({ ...filters, role: e.target.value })}
          className="px-4 py-2 border rounded"
        >
          <option value="">All Roles</option>
          <option value="user">User</option>
          <option value="supplier">Supplier</option>
          <option value="admin">Admin</option>
          <option value="rx_verifier">RX Verifier</option>
        </select>

        <select
          value={filters.is_active}
          onChange={(e) => setFilters({ ...filters, is_active: e.target.value })}
          className="px-4 py-2 border rounded"
        >
          <option value="">All Status</option>
          <option value="true">Active</option>
          <option value="false">Inactive</option>
        </select>
      </div>

      {/* User Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-6 py-3 border-b">ID</th>
              <th className="px-6 py-3 border-b">Email</th>
              <th className="px-6 py-3 border-b">Name</th>
              <th className="px-6 py-3 border-b">Role</th>
              <th className="px-6 py-3 border-b">Status</th>
              <th className="px-6 py-3 border-b">Verified</th>
              <th className="px-6 py-3 border-b">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data?.results?.map((user: any) => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 border-b">{user.id}</td>
                <td className="px-6 py-4 border-b">{user.email}</td>
                <td className="px-6 py-4 border-b">{user.full_name}</td>
                <td className="px-6 py-4 border-b">
                  <span className="px-2 py-1 rounded text-sm bg-blue-100">
                    {user.role}
                  </span>
                </td>
                <td className="px-6 py-4 border-b">
                  <span className={`px-2 py-1 rounded text-sm ${
                    user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-6 py-4 border-b">
                  {user.email_verified ? '✅' : '❌'}
                </td>
                <td className="px-6 py-4 border-b">
                  <button
                    onClick={() => window.location.href = `/admin/users/${user.id}`}
                    className="text-blue-600 hover:underline mr-2"
                  >
                    View
                  </button>
                  <button
                    onClick={() => handleDelete(user.id)}
                    className="text-red-600 hover:underline"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="mt-6 flex justify-between items-center">
        <div>
          Showing {data?.results?.length || 0} of {data?.count || 0} users
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setPage(page - 1)}
            disabled={!data?.previous}
            className="px-4 py-2 border rounded disabled:opacity-50"
          >
            Previous
          </button>
          <span className="px-4 py-2">Page {page}</span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={!data?.next}
            className="px-4 py-2 border rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
```

### 2. Create User Form

Create `src/components/admin/CreateUserForm.tsx`:

```typescript
'use client';

import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { userService } from '@/services/userService';

interface CreateUserFormData {
  email: string;
  full_name: string;
  contact: string;
  role: string;
  password: string;
  password2: string;
  is_active: boolean;
  email_verified: boolean;
  send_credentials_email: boolean;
}

export default function CreateUserForm({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<CreateUserFormData>({
    defaultValues: {
      is_active: true,
      email_verified: false,
      send_credentials_email: true,
    },
  });

  const createMutation = useMutation({
    mutationFn: userService.createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      alert('User created successfully');
      onClose();
    },
    onError: (error: any) => {
      alert(error.response?.data?.error || 'Failed to create user');
    },
  });

  const onSubmit = (data: CreateUserFormData) => {
    createMutation.mutate(data);
  };

  const password = watch('password');

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <h2 className="text-2xl font-bold mb-4">Create New User</h2>

      <div>
        <label className="block mb-1 font-medium">Email *</label>
        <input
          {...register('email', { required: 'Email is required' })}
          type="email"
          className="w-full px-4 py-2 border rounded"
        />
        {errors.email && (
          <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>
        )}
      </div>

      <div>
        <label className="block mb-1 font-medium">Full Name *</label>
        <input
          {...register('full_name', { required: 'Full name is required' })}
          className="w-full px-4 py-2 border rounded"
        />
        {errors.full_name && (
          <p className="text-red-500 text-sm mt-1">{errors.full_name.message}</p>
        )}
      </div>

      <div>
        <label className="block mb-1 font-medium">Contact *</label>
        <input
          {...register('contact', { required: 'Contact is required' })}
          className="w-full px-4 py-2 border rounded"
        />
        {errors.contact && (
          <p className="text-red-500 text-sm mt-1">{errors.contact.message}</p>
        )}
      </div>

      <div>
        <label className="block mb-1 font-medium">Role *</label>
        <select
          {...register('role', { required: 'Role is required' })}
          className="w-full px-4 py-2 border rounded"
        >
          <option value="">Select Role</option>
          <option value="user">User</option>
          <option value="supplier">Supplier</option>
          <option value="admin">Admin</option>
          <option value="rx_verifier">RX Verifier</option>
        </select>
        {errors.role && (
          <p className="text-red-500 text-sm mt-1">{errors.role.message}</p>
        )}
      </div>

      <div>
        <label className="block mb-1 font-medium">Password *</label>
        <input
          {...register('password', {
            required: 'Password is required',
            minLength: { value: 8, message: 'Password must be at least 8 characters' },
          })}
          type="password"
          className="w-full px-4 py-2 border rounded"
        />
        {errors.password && (
          <p className="text-red-500 text-sm mt-1">{errors.password.message}</p>
        )}
      </div>

      <div>
        <label className="block mb-1 font-medium">Confirm Password *</label>
        <input
          {...register('password2', {
            required: 'Please confirm password',
            validate: (value) => value === password || 'Passwords do not match',
          })}
          type="password"
          className="w-full px-4 py-2 border rounded"
        />
        {errors.password2 && (
          <p className="text-red-500 text-sm mt-1">{errors.password2.message}</p>
        )}
      </div>

      <div className="flex items-center space-x-4">
        <label className="flex items-center">
          <input
            {...register('is_active')}
            type="checkbox"
            className="mr-2"
          />
          Active
        </label>

        <label className="flex items-center">
          <input
            {...register('email_verified')}
            type="checkbox"
            className="mr-2"
          />
          Email Verified
        </label>

        <label className="flex items-center">
          <input
            {...register('send_credentials_email')}
            type="checkbox"
            className="mr-2"
          />
          Send Credentials Email
        </label>
      </div>

      <div className="flex gap-4">
        <button
          type="submit"
          disabled={createMutation.isPending}
          className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {createMutation.isPending ? 'Creating...' : 'Create User'}
        </button>
        <button
          type="button"
          onClick={onClose}
          className="px-6 py-2 border rounded hover:bg-gray-100"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
```

### 3. User Statistics Dashboard

Create `src/components/admin/UserStatistics.tsx`:

```typescript
'use client';

import { useQuery } from '@tanstack/react-query';
import { userService } from '@/services/userService';

export default function UserStatistics() {
  const { data, isLoading } = useQuery({
    queryKey: ['user-statistics'],
    queryFn: userService.getStatistics,
  });

  if (isLoading) return <div>Loading statistics...</div>;

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">User Statistics</h2>

      {/* Overview Cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Total Users"
          value={data?.total_users}
          color="bg-blue-100 text-blue-800"
        />
        <StatCard
          title="Active Users"
          value={data?.active_users}
          color="bg-green-100 text-green-800"
        />
        <StatCard
          title="Inactive Users"
          value={data?.inactive_users}
          color="bg-red-100 text-red-800"
        />
        <StatCard
          title="Verified Users"
          value={data?.verified_users}
          color="bg-purple-100 text-purple-800"
        />
      </div>

      {/* New Users */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard
          title="New Today"
          value={data?.new_users_today}
          color="bg-yellow-100 text-yellow-800"
        />
        <StatCard
          title="New This Week"
          value={data?.new_users_this_week}
          color="bg-orange-100 text-orange-800"
        />
        <StatCard
          title="New This Month"
          value={data?.new_users_this_month}
          color="bg-pink-100 text-pink-800"
        />
      </div>

      {/* Role Distribution */}
      <div className="bg-white p-6 rounded shadow mb-8">
        <h3 className="text-xl font-semibold mb-4">Users by Role</h3>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(data?.users_by_role || {}).map(([role, count]) => (
            <div key={role} className="flex justify-between items-center p-3 bg-gray-50 rounded">
              <span className="capitalize">{role}</span>
              <span className="font-bold">{count as number}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Growth Rate */}
      <div className="bg-white p-6 rounded shadow">
        <h3 className="text-xl font-semibold mb-4">Growth Rate</h3>
        <div className="flex items-center gap-4">
          <div>
            <p className="text-sm text-gray-600">Current Month</p>
            <p className="text-2xl font-bold">{data?.growth_rate?.current_month}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Previous Month</p>
            <p className="text-2xl font-bold">{data?.growth_rate?.previous_month}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Growth</p>
            <p className={`text-2xl font-bold ${
              (data?.growth_rate?.percentage || 0) > 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {data?.growth_rate?.percentage}%
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, color }: { title: string; value: number; color: string }) {
  return (
    <div className={`p-6 rounded shadow ${color}`}>
      <p className="text-sm font-medium mb-1">{title}</p>
      <p className="text-3xl font-bold">{value || 0}</p>
    </div>
  );
}
```

### 4. Bulk Actions Component

Create `src/components/admin/BulkActions.tsx`:

```typescript
'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { userService } from '@/services/userService';

interface BulkActionsProps {
  selectedUserIds: number[];
  onClearSelection: () => void;
}

export default function BulkActions({ selectedUserIds, onClearSelection }: BulkActionsProps) {
  const [action, setAction] = useState('');
  const [reason, setReason] = useState('');
  const queryClient = useQueryClient();

  const bulkMutation = useMutation({
    mutationFn: userService.bulkAction,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      alert(`Bulk action completed. ${data.affected_count} users affected.`);
      onClearSelection();
      setAction('');
      setReason('');
    },
    onError: (error: any) => {
      alert(error.response?.data?.error || 'Bulk action failed');
    },
  });

  const handleBulkAction = () => {
    if (!action) {
      alert('Please select an action');
      return;
    }

    if (selectedUserIds.length === 0) {
      alert('Please select at least one user');
      return;
    }

    if (confirm(`Are you sure you want to ${action} ${selectedUserIds.length} user(s)?`)) {
      bulkMutation.mutate({
        user_ids: selectedUserIds,
        action: action as any,
        reason,
      });
    }
  };

  if (selectedUserIds.length === 0) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg p-4">
      <div className="container mx-auto flex items-center gap-4">
        <span className="font-medium">
          {selectedUserIds.length} user(s) selected
        </span>

        <select
          value={action}
          onChange={(e) => setAction(e.target.value)}
          className="px-4 py-2 border rounded"
        >
          <option value="">Select Action</option>
          <option value="activate">Activate</option>
          <option value="deactivate">Deactivate</option>
          <option value="verify_email">Verify Email</option>
          <option value="delete">Delete</option>
        </select>

        <input
          type="text"
          placeholder="Reason (optional)"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          className="px-4 py-2 border rounded flex-1"
        />

        <button
          onClick={handleBulkAction}
          disabled={bulkMutation.isPending}
          className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {bulkMutation.isPending ? 'Processing...' : 'Apply'}
        </button>

        <button
          onClick={onClearSelection}
          className="px-6 py-2 border rounded hover:bg-gray-100"
        >
          Clear
        </button>
      </div>
    </div>
  );
}
```

---

## Error Handling

### Error Boundary Component

Create `src/components/ErrorBoundary.tsx`:

```typescript
'use client';

import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 bg-red-50 border border-red-200 rounded">
          <h2 className="text-xl font-bold text-red-800 mb-2">Something went wrong</h2>
          <p className="text-red-600">{this.state.error?.message}</p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### API Error Handler

Create `src/utils/errorHandler.ts`:

```typescript
export const handleAPIError = (error: any) => {
  if (error.response) {
    // Server responded with error
    const status = error.response.status;
    const data = error.response.data;

    switch (status) {
      case 400:
        return data.error || 'Invalid request';
      case 401:
        return 'Unauthorized. Please login again.';
      case 403:
        return 'Access denied. You don\'t have permission.';
      case 404:
        return 'Resource not found';
      case 500:
        return 'Server error. Please try again later.';
      default:
        return data.error || 'An error occurred';
    }
  } else if (error.request) {
    // Request made but no response
    return 'Network error. Please check your connection.';
  } else {
    // Something else happened
    return error.message || 'An unexpected error occurred';
  }
};
```

---

## Best Practices

### 1. Type Safety with TypeScript

```typescript
// Define types for your data
interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'user' | 'supplier' | 'admin' | 'rx_verifier';
  is_active: boolean;
}

// Use types in your components
const UserCard: React.FC<{ user: User }> = ({ user }) => {
  // TypeScript will provide autocomplete and type checking
  return <div>{user.full_name}</div>;
};
```

### 2. Loading States

```typescript
function UserList() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['users'],
    queryFn: userService.listUsers,
  });

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (isError) {
    return <ErrorMessage />;
  }

  return <div>{/* Render users */}</div>;
}
```

### 3. Optimistic Updates

```typescript
const updateMutation = useMutation({
  mutationFn: userService.updateUser,
  onMutate: async (newData) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['users'] });

    // Snapshot previous value
    const previousUsers = queryClient.getQueryData(['users']);

    // Optimistically update
    queryClient.setQueryData(['users'], (old: any) => ({
      ...old,
      results: old.results.map((user: User) =>
        user.id === newData.id ? { ...user, ...newData } : user
      ),
    }));

    return { previousUsers };
  },
  onError: (err, newData, context) => {
    // Rollback on error
    queryClient.setQueryData(['users'], context?.previousUsers);
  },
  onSettled: () => {
    // Refetch after mutation
    queryClient.invalidateQueries({ queryKey: ['users'] });
  },
});
```

### 4. Debounced Search

```typescript
import { useDebouncedValue } from '@/hooks/useDebouncedValue';

function SearchUsers() {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebouncedValue(searchTerm, 500);

  const { data } = useQuery({
    queryKey: ['users', debouncedSearch],
    queryFn: () => userService.searchUsers(debouncedSearch),
    enabled: debouncedSearch.length > 0,
  });

  return (
    <input
      type="text"
      value={searchTerm}
      onChange={(e) => setSearchTerm(e.target.value)}
      placeholder="Search users..."
    />
  );
}
```

### 5. Custom Hooks

```typescript
// useUser.ts
export function useUser(userId: number) {
  return useQuery({
    queryKey: ['user', userId],
    queryFn: () => userService.getUserDetails(userId),
  });
}

// useUsers.ts
export function useUsers(filters?: Record<string, any>) {
  return useQuery({
    queryKey: ['users', filters],
    queryFn: () => userService.listUsers(filters),
  });
}

// Usage
function UserProfile({ userId }: { userId: number }) {
  const { data: user, isLoading } = useUser(userId);
  
  if (isLoading) return <div>Loading...</div>;
  
  return <div>{user.full_name}</div>;
}
```

---

## Complete Page Example

Create `src/app/admin/users/page.tsx`:

```typescript
'use client';

import { useState } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import UserList from '@/components/admin/UserList';
import UserStatistics from '@/components/admin/UserStatistics';
import CreateUserForm from '@/components/admin/CreateUserForm';
import ErrorBoundary from '@/components/ErrorBoundary';

export default function AdminUsersPage() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showStatistics, setShowStatistics] = useState(false);

  return (
    <ProtectedRoute requireAdmin>
      <ErrorBoundary>
        <div className="min-h-screen bg-gray-50">
          <div className="container mx-auto px-4 py-8">
            <div className="flex justify-between items-center mb-6">
              <h1 className="text-3xl font-bold">User Management</h1>
              <div className="flex gap-4">
                <button
                  onClick={() => setShowStatistics(!showStatistics)}
                  className="px-4 py-2 border rounded hover:bg-gray-100"
                >
                  {showStatistics ? 'Hide Statistics' : 'Show Statistics'}
                </button>
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Create User
                </button>
              </div>
            </div>

            {showStatistics && <UserStatistics />}

            <UserList />

            {showCreateForm && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
                <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                  <CreateUserForm onClose={() => setShowCreateForm(false)} />
                </div>
              </div>
            )}
          </div>
        </div>
      </ErrorBoundary>
    </ProtectedRoute>
  );
}
```

---

## Testing

### Example Test with React Testing Library

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import UserList from '@/components/admin/UserList';

describe('UserList', () => {
  const queryClient = new QueryClient();

  it('renders user list', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <UserList />
      </QueryClientProvider>
    );

    expect(await screen.findByText('User Management')).toBeInTheDocument();
  });

  it('filters users by role', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <UserList />
      </QueryClientProvider>
    );

    const roleFilter = screen.getByRole('combobox', { name: /role/i });
    fireEvent.change(roleFilter, { target: { value: 'supplier' } });

    // Assert filtered results
  });
});
```

---

## Environment Variables

Create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=https://api.medixmall.com
NEXT_PUBLIC_APP_NAME=MedixMall Admin
```

---

## Additional Resources

- [React Query Documentation](https://tanstack.com/query/latest)
- [React Hook Form Documentation](https://react-hook-form.com/)
- [Zustand Documentation](https://zustand-demo.pmnd.rs/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)

---

## Support

For questions or issues:
- **Email:** dev-support@medixmall.com
- **Documentation:** https://docs.medixmall.com
- **GitHub:** https://github.com/medixmall/frontend
