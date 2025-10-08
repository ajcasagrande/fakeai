# Organization Management Dashboard

A comprehensive admin dashboard for managing organizations, users, projects, and service accounts with a professional NVIDIA-themed interface.

## Features

### 1. Organization Users Management
- **List all organization users** with roles (owner, reader)
- **Add new users** with role assignment
- **Modify user roles** inline editing
- **Remove users** with cascade deletion from all projects
- **User details** display with avatar, email, and join date

### 2. Organization Invitations
- **Send email invitations** to new users
- **View all invitations** with status tracking (pending, accepted, expired)
- **Delete pending invitations**
- **Expiration tracking** - invites expire after 7 days
- **Status badges** for quick visual feedback

### 3. Projects Management
- **Create projects** with descriptive names
- **List all projects** with grid view
- **Archive projects** to hide from active list
- **Restore archived projects** via toggle
- **Rename projects** with inline editing
- **Project metadata** showing creation and archive dates
- **Navigate to project details** for user and service account management

### 4. Project Users Management
- **Add organization users** to specific projects
- **Assign project roles** (owner, member)
- **Modify user roles** within projects
- **Remove users** from projects
- **List all project users** with detailed information

### 5. Service Accounts Management
- **Create service accounts** for API access
- **Assign roles** (owner, member) to service accounts
- **View account details** including ID and permissions
- **Delete service accounts** when no longer needed
- **Permission display** showing what each account can do

### 6. API Key Management
- Service accounts provide the foundation for API key management
- Each account has clear permission levels
- Ready for integration with API key generation endpoints

## API Endpoints

All API calls are made to `/v1/organization/*` endpoints:

### Organization Users
- `GET /v1/organization/users` - List users
- `GET /v1/organization/users/{user_id}` - Get user details
- `POST /v1/organization/users` - Create user
- `POST /v1/organization/users/{user_id}` - Modify user
- `DELETE /v1/organization/users/{user_id}` - Delete user

### Organization Invites
- `GET /v1/organization/invites` - List invites
- `GET /v1/organization/invites/{invite_id}` - Get invite details
- `POST /v1/organization/invites` - Create invite
- `DELETE /v1/organization/invites/{invite_id}` - Delete invite

### Organization Projects
- `GET /v1/organization/projects` - List projects
- `GET /v1/organization/projects/{project_id}` - Get project details
- `POST /v1/organization/projects` - Create project
- `POST /v1/organization/projects/{project_id}` - Modify project
- `POST /v1/organization/projects/{project_id}/archive` - Archive project

### Project Users
- `GET /v1/organization/projects/{project_id}/users` - List project users
- `GET /v1/organization/projects/{project_id}/users/{user_id}` - Get user details
- `POST /v1/organization/projects/{project_id}/users` - Add user to project
- `POST /v1/organization/projects/{project_id}/users/{user_id}` - Modify user role
- `DELETE /v1/organization/projects/{project_id}/users/{user_id}` - Remove user

### Service Accounts
- `GET /v1/organization/projects/{project_id}/service_accounts` - List accounts
- `GET /v1/organization/projects/{project_id}/service_accounts/{account_id}` - Get details
- `POST /v1/organization/projects/{project_id}/service_accounts` - Create account
- `DELETE /v1/organization/projects/{project_id}/service_accounts/{account_id}` - Delete account

## Role Permissions

### Organization Roles
- **Owner**: Full access to all organization resources and settings
- **Reader**: Read-only access to organization resources

### Project Roles
- **Owner**: Full control over project resources and members
- **Member**: Can use project resources via API

### Service Account Roles
- **Owner**: Full access to project resources and settings
- **Member**: Can use project resources

## Components

### Main Component
- `Organization.tsx` - Main dashboard with tab navigation

### Sub-Components
- `UsersManagement.tsx` - Organization users management
- `InvitesManagement.tsx` - Invitation management
- `ProjectsManagement.tsx` - Projects grid with archive/restore
- `ProjectUsersManagement.tsx` - Project-specific user management
- `ServiceAccountsManagement.tsx` - Service accounts for API access

### Supporting Files
- `api.ts` - API client with all endpoint calls
- `types.ts` - TypeScript type definitions
- `styles.css` - NVIDIA-themed styles

## Usage

```tsx
import Organization from '@/pages/Organization';

function App() {
  return <Organization />;
}
```

## Styling

The dashboard uses the NVIDIA design system with:
- **NVIDIA Green** (#76B900) as the primary brand color
- **Dark theme** with deep blacks and subtle grays
- **Professional admin interface** design patterns
- **Smooth animations** and transitions
- **Responsive design** for mobile and desktop

## Design Patterns

### Data Tables
- Sortable columns
- Inline editing for quick updates
- Action buttons for common operations
- Loading states and error handling

### Cards
- Project cards with hover effects
- Service account cards with permission details
- Info cards for documentation

### Modals
- Create/edit forms in centered modals
- Confirmation dialogs for destructive actions
- Keyboard navigation support (ESC to close)

### Empty States
- Helpful messaging when no data exists
- Quick action buttons to get started
- Icon-based visual feedback

### Loading States
- Spinners for async operations
- Inline loading for button actions
- Skeleton screens for data fetching

## Error Handling

All components include:
- Try-catch blocks for API calls
- User-friendly error messages
- Error banners with dismiss functionality
- Graceful degradation on failures

## Accessibility

- Semantic HTML structure
- ARIA labels where appropriate
- Keyboard navigation support
- Focus management in modals
- Color contrast meets WCAG standards

## Future Enhancements

1. **API Key Generation** - Direct key creation from service accounts
2. **Usage Analytics** - Per-project and per-user usage metrics
3. **Billing Integration** - Cost tracking and limits
4. **Audit Logs** - Track all admin actions
5. **Bulk Operations** - Multi-select for batch actions
6. **Advanced Filtering** - Search and filter across all tables
7. **Export Functionality** - CSV/JSON export of user lists
8. **Email Templates** - Customizable invitation emails

## File Structure

```
Organization/
├── Organization.tsx          # Main dashboard component
├── api.ts                    # API client
├── types.ts                  # TypeScript types
├── styles.css                # NVIDIA-themed styles
├── index.ts                  # Exports
├── README.md                 # This file
└── components/
    ├── UsersManagement.tsx
    ├── InvitesManagement.tsx
    ├── ProjectsManagement.tsx
    ├── ProjectUsersManagement.tsx
    └── ServiceAccountsManagement.tsx
```

## Integration

To add this dashboard to your app's routing:

```tsx
import Organization from '@/pages/Organization';

// In your router configuration
{
  path: '/organization',
  element: <Organization />,
}
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- Lazy loading for large lists
- Optimized re-renders with React hooks
- Efficient API calls with caching potential
- Minimal bundle size impact

## License

Apache-2.0
