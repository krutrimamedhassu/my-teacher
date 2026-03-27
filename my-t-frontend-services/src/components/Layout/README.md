# Layout Components

This directory contains reusable layout components for the application.

## Components

### Header.jsx
A reusable header component with:
- Logo linking to homepage
- Search icon button
- Login/Profile button that adapts based on authentication state
- Hide/show animation on scroll

**Props:**
- `isVisible` (boolean) - Controls header visibility
- `onProfileClick` (function) - Callback for profile button click

### Footer.jsx
A comprehensive footer component with:
- Brand section with description and CTA buttons
- Feature links
- Resource links  
- Company links
- Copyright and attribution

**Props:** None (uses authentication context internally)

### PageLayout.jsx
A complete page wrapper that includes header, footer, and profile modal management:
- Automatic scroll handling for header visibility
- Profile modal state management
- Flexible content area
- Configurable header/footer display

**Props:**
- `children` (React node) - Page content
- `showHeader` (boolean, default: true) - Whether to show header
- `showFooter` (boolean, default: true) - Whether to show footer
- `showFloatingButton` (boolean, default: false) - Reserved for floating buttons

## Usage Examples

### Using Individual Components
```jsx
import { Header, Footer } from '../components/Layout';

// In your component
return (
  <div>
    <Header isVisible={true} onProfileClick={handleProfileClick} />
    <main>Your content here</main>
    <Footer />
  </div>
);
```

### Using PageLayout Wrapper
```jsx
import { PageLayout } from '../components/Layout';

const MyPage = () => {
  return (
    <PageLayout>
      <div>
        <h1>My Page Content</h1>
        <p>This content will be wrapped with header and footer</p>
      </div>
    </PageLayout>
  );
};
```

### Page Layout without Header/Footer
```jsx
import { PageLayout } from '../components/Layout';

const ChatPage = () => {
  return (
    <PageLayout showHeader={false} showFooter={false}>
      <div>Chat interface without header/footer</div>
    </PageLayout>
  );
};
```

## Benefits

1. **Consistency** - Ensures consistent header/footer across pages
2. **Reusability** - DRY principle, no duplicate code
3. **Maintainability** - Single place to update header/footer styles
4. **Flexibility** - Components can be used individually or as wrapper
5. **Authentication Integration** - Automatic handling of login/profile states

## Migration Notes

- IndexPage has been updated to use the new components
- Profile modal handling is now centralized in PageLayout
- Scroll behavior for header visibility is handled automatically
- All authentication states are managed through useAuth context