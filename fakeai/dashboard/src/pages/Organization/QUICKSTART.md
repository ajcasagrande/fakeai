# Organization Dashboard - Quick Start Guide

## Installation

The Organization Management Dashboard is ready to use. No additional dependencies required beyond your existing React/TypeScript setup.

## Basic Usage

### 1. Import the Component

```tsx
import Organization from './pages/Organization';

function App() {
  return <Organization />;
}
```

### 2. Add to Router (React Router)

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Organization from './pages/Organization';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/organization" element={<Organization />} />
      </Routes>
    </BrowserRouter>
  );
}
```

## Feature Overview

### Tab 1: Users
- View all organization users
- Add new users with email and role
- Change user roles (Owner/Reader)
- Remove users from organization

### Tab 2: Invitations
- Send email invitations
- Track invitation status
- Delete pending invitations
- View expiration dates

### Tab 3: Projects
- Create new projects
- Rename existing projects
- Archive/restore projects
- Access project details

### From Projects
- Click "Manage Project" to access:
  - **Project Users**: Add/remove users, assign roles
  - **Service Accounts**: Create API access accounts

## Common Workflows

### Adding a User to the Organization

1. Go to **Users** tab
2. Click **Add User** button
3. Enter email address
4. Select role (Owner or Reader)
5. Click **Add User**

### Creating a Project with Users

1. Go to **Projects** tab
2. Click **Create Project**
3. Enter project name
4. Click **Create Project**
5. Click **Manage Project** on the new project card
6. Navigate to project users
7. Click **Add User** and select from organization users

### Setting Up API Access

1. Go to **Projects** tab
2. Click **Manage Project**
3. From project view, access **Service Accounts**
4. Click **Create Service Account**
5. Enter account name and select role
6. Click **Create Account**
7. Note the account ID for API key generation

## API Endpoints Reference

All endpoints use `/v1/organization/*` base path:

```typescript
// List users
GET /v1/organization/users

// Create user
POST /v1/organization/users
Body: { email: string, role: "owner" | "reader" }

// Send invitation
POST /v1/organization/invites
Body: { email: string, role: "owner" | "reader" }

// Create project
POST /v1/organization/projects
Body: { name: string }

// Add user to project
POST /v1/organization/projects/{project_id}/users
Body: { user_id: string, role: "owner" | "member" }

// Create service account
POST /v1/organization/projects/{project_id}/service_accounts
Body: { name: string, role?: "owner" | "member" }
```

## Keyboard Shortcuts

- **ESC**: Close any modal
- **Enter**: Submit forms
- **Tab**: Navigate between form fields

## Role Permissions Quick Reference

| Role | Organization Level | Project Level |
|------|-------------------|---------------|
| **Owner** | Full access to settings | Full control over resources |
| **Reader** | View-only access | - |
| **Member** | - | Can use project resources |

## Customization

### Changing Colors

Edit `/pages/Organization/styles.css`:

```css
/* Change primary brand color */
--nvidia-green: #YOUR_COLOR;
--nvidia-green-light: #YOUR_LIGHT_COLOR;
```

### Adding Fields

1. Update types in `types.ts`
2. Modify API calls in `api.ts`
3. Update component forms in `components/`

## Troubleshooting

### Users not appearing
- Check API endpoint is responding
- Verify pagination limit (default: 100)
- Check browser console for errors

### Cannot delete user
- Ensure user is not the last owner
- Check for backend validation errors
- User will be removed from all projects

### Project archived accidentally
- Go to Projects tab
- Enable "Show archived" toggle
- Find project and note its ID
- Contact admin to restore

## Tips & Best Practices

1. **Start with Users**: Add organization users before creating projects
2. **Use Invites**: For new team members, send invitations first
3. **Project Organization**: Create separate projects for different environments
4. **Service Accounts**: Use descriptive names like "Production API" or "CI/CD Pipeline"
5. **Archive vs Delete**: Archive projects instead of deleting to preserve history

## Next Steps

1. Add your first user
2. Send an invitation
3. Create a project
4. Add users to the project
5. Create a service account for API access

## Support

For issues or questions:
- Check README.md for detailed documentation
- Review IMPLEMENTATION_SUMMARY.md for technical details
- Inspect browser console for error messages

## Quick Links

- **Users**: Manage organization members
- **Invitations**: Send and track invites
- **Projects**: Create and organize projects
- **Project Users**: Assign team members to projects
- **Service Accounts**: Set up API access

---

**Dashboard Status**: ✅ Production Ready
**NVIDIA Theme**: ✅ Applied
**All Features**: ✅ Implemented
**Documentation**: ✅ Complete
