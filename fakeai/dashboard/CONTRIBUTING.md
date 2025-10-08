# Contributing Guidelines

Thank you for your interest in contributing to the FakeAI Dashboard! This guide will help you get started.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Community](#community)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in your interactions.

### Expected Behavior

- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Personal attacks or trolling
- Publishing others' private information
- Any conduct that could reasonably be considered inappropriate

---

## Getting Started

### Prerequisites

- Node.js 18+ and npm 9+
- Git 2.30+
- Python 3.10+ (for FakeAI server)
- Code editor (VS Code recommended)
- Basic knowledge of React and TypeScript

### Fork and Clone

1. **Fork the repository** on GitHub

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/fakeai.git
   cd fakeai
   ```

3. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/ajcasagrande/fakeai.git
   ```

4. **Install dependencies**
   ```bash
   cd fakeai/dashboard
   npm install
   ```

5. **Start development server**
   ```bash
   npm run dev
   ```

---

## Development Workflow

### 1. Create a Branch

```bash
# Update main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Follow [coding standards](#coding-standards)
- Write meaningful commit messages
- Test your changes thoroughly
- Update documentation if needed

### 3. Keep Branch Updated

```bash
# Fetch upstream changes
git fetch upstream

# Rebase on main
git rebase upstream/main
```

### 4. Push Changes

```bash
git push origin feature/your-feature-name
```

### 5. Create Pull Request

- Go to GitHub and create a pull request
- Fill out the PR template
- Link related issues
- Request review from maintainers

---

## Coding Standards

### TypeScript

#### Type Safety

Always use explicit types, avoid `any`:

```typescript
// Bad
const data: any = await fetchData();

// Good
interface Data {
  id: string;
  value: number;
}
const data: Data = await fetchData();
```

#### Interfaces vs Types

```typescript
// Use interfaces for object shapes
interface User {
  id: string;
  name: string;
}

// Use types for unions/intersections
type Status = 'pending' | 'success' | 'error';
type UserWithStatus = User & { status: Status };
```

### React Components

#### Component Structure

```typescript
/**
 * ComponentName - Brief description
 *
 * Detailed description if needed
 */

import React, { useState, useEffect } from 'react';
import './ComponentName.css';

interface ComponentNameProps {
  /** Description of prop */
  requiredProp: string;
  /** Optional prop with default */
  optionalProp?: number;
  /** Callback handler */
  onAction?: (value: string) => void;
}

export const ComponentName: React.FC<ComponentNameProps> = ({
  requiredProp,
  optionalProp = 0,
  onAction,
}) => {
  // 1. State declarations
  const [state, setState] = useState<string>('');

  // 2. Effects
  useEffect(() => {
    // Effect logic
  }, [requiredProp]);

  // 3. Event handlers
  const handleClick = () => {
    if (onAction) {
      onAction(state);
    }
  };

  // 4. Render helpers (if needed)
  const renderContent = () => {
    // Complex rendering logic
  };

  // 5. Main render
  return (
    <div className="component-name">
      <h2>{requiredProp}</h2>
      <button onClick={handleClick}>Action</button>
    </div>
  );
};

export default ComponentName;
```

#### Naming Conventions

- **Components**: PascalCase - `MetricsOverview`
- **Files**: PascalCase - `MetricsOverview.tsx`
- **Props interfaces**: ComponentName + Props - `MetricsOverviewProps`
- **Handlers**: handle + Action - `handleClick`, `handleSubmit`
- **Boolean props**: is/has/should - `isLoading`, `hasError`, `shouldRender`

### CSS

#### BEM Naming

```css
/* Block */
.metrics-overview {
  padding: 1rem;
}

/* Element */
.metrics-overview__header {
  font-weight: bold;
}

/* Modifier */
.metrics-overview--loading {
  opacity: 0.5;
}
```

#### Use CSS Variables

```css
/* Bad */
.component {
  color: #3b82f6;
  padding: 16px;
}

/* Good */
.component {
  color: var(--primary-color);
  padding: var(--spacing-md);
}
```

### File Organization

```
ComponentName/
├── ComponentName.tsx      # Component implementation
├── ComponentName.css      # Component styles
├── ComponentName.test.tsx # Unit tests (future)
├── types.ts              # Type definitions
└── index.ts              # Public exports
```

---

## Commit Guidelines

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Build process, dependencies, tooling

### Examples

```bash
feat(chat): add streaming metrics component

Add StreamingMetrics component to display streaming vs non-streaming
request statistics with visual breakdown.

Closes #123

---

fix(api): handle network timeout errors

Add proper error handling for network timeouts in API client.
Includes retry logic with exponential backoff.

---

docs(readme): update installation instructions

Add Node.js version requirement and improve clarity of setup steps.

---

refactor(hooks): extract data fetching logic

Extract common data fetching pattern into reusable useApiData hook
to reduce code duplication.
```

### Commit Best Practices

- **One logical change per commit**
- **Write clear, descriptive messages**
- **Reference related issues**
- **Keep commits atomic**
- **Test before committing**

---

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass (when applicable)
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] Branch is up to date with main
- [ ] Self-review completed

### PR Title

Use same format as commit messages:

```
feat(chat): add streaming metrics component
fix(api): handle network timeout errors
docs(readme): update installation instructions
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Closes #123
Related to #456

## Changes Made
- Added StreamingMetrics component
- Updated API client error handling
- Added unit tests

## Testing
- [ ] Tested locally
- [ ] Tested in production build
- [ ] Manual testing completed
- [ ] Automated tests pass

## Screenshots
(If applicable)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
```

### Review Process

1. **Maintainer review** - Code review by maintainers
2. **Address feedback** - Make requested changes
3. **Re-review** - Maintainer reviews again
4. **Approval** - PR approved for merge
5. **Merge** - Maintainer merges PR

### After Merge

- Delete your feature branch
- Pull latest main
- Celebrate!

---

## Testing Guidelines

### Manual Testing

Before submitting PR:

1. **Test the feature**
   - Verify feature works as expected
   - Test edge cases
   - Test error handling

2. **Test in different browsers**
   - Chrome
   - Firefox
   - Safari

3. **Test responsive design**
   - Desktop
   - Tablet
   - Mobile

4. **Check console**
   - No errors
   - No warnings
   - No 404s

### Unit Tests (Future)

When tests are added:

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { MetricsOverview } from './MetricsOverview';

describe('MetricsOverview', () => {
  it('renders metrics correctly', () => {
    const metrics = {
      total_requests: 1000,
      total_tokens: 50000,
      total_cost: 25.50,
    };

    render(<MetricsOverview metrics={metrics} />);

    expect(screen.getByText('1,000')).toBeInTheDocument();
    expect(screen.getByText('50,000')).toBeInTheDocument();
    expect(screen.getByText('$25.50')).toBeInTheDocument();
  });

  it('handles loading state', () => {
    render(<MetricsOverview metrics={{}} loading />);
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });
});
```

---

## Documentation

### Code Documentation

#### JSDoc Comments

```typescript
/**
 * Fetches chat completion metrics from the API
 *
 * @param filters - Optional filters for the query
 * @returns Promise resolving to model metrics
 * @throws {ApiError} If the request fails
 *
 * @example
 * const metrics = await fetchChatMetrics({ model: 'gpt-4' });
 */
export async function fetchChatMetrics(
  filters?: DashboardFilters
): Promise<ModelMetrics> {
  // Implementation
}
```

#### Inline Comments

Use comments sparingly, only for complex logic:

```typescript
// Calculate cache hit rate as percentage
// Note: Avoid division by zero
const hitRate = totalRequests > 0
  ? (cacheHits / totalRequests) * 100
  : 0;
```

### Component Documentation

Each component should have:

1. **Purpose** - What it does
2. **Props** - Interface with JSDoc
3. **Usage example**
4. **Location** in project

### Updating Documentation

When making changes:

- Update relevant .md files
- Update component JSDoc
- Add examples if needed
- Update screenshots (if applicable)

---

## Community

### Communication Channels

- **GitHub Issues** - Bug reports, feature requests
- **GitHub Discussions** - General questions, ideas
- **Pull Requests** - Code contributions

### Getting Help

- Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- Search existing issues
- Ask in GitHub Discussions
- Tag maintainers if needed

### Recognition

Contributors are recognized in:
- GitHub contributors page
- Release notes
- Special mentions for significant contributions

---

## Areas to Contribute

### Good First Issues

Look for issues labeled `good first issue`:
- Simple bug fixes
- Documentation improvements
- Small feature additions
- Test coverage

### Feature Requests

Check issues labeled `enhancement`:
- New components
- UI improvements
- Performance optimizations
- New pages

### Bug Fixes

Issues labeled `bug`:
- Fix reported bugs
- Add error handling
- Improve stability

### Documentation

Always welcome:
- Improve existing docs
- Add examples
- Fix typos
- Add tutorials

---

## Questions?

If you have questions about contributing:

1. Check this guide
2. Read [DEVELOPMENT.md](./DEVELOPMENT.md)
3. Search GitHub issues
4. Ask in GitHub Discussions

---

## Thank You!

Thank you for contributing to the FakeAI Dashboard! Your contributions make this project better for everyone.

---

**Happy coding!**
