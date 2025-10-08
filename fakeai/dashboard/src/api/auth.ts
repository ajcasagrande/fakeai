/**
 * Authentication token management
 */

const AUTH_TOKEN_KEY = 'fakeai_auth_token';
const TOKEN_EXPIRY_KEY = 'fakeai_token_expiry';

/**
 * Storage interface for token persistence
 */
interface TokenStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

/**
 * Get storage instance (localStorage with fallback)
 */
function getStorage(): TokenStorage {
  try {
    // Check if localStorage is available
    if (typeof window !== 'undefined' && window.localStorage) {
      return window.localStorage;
    }
  } catch (e) {
    // localStorage not available
  }

  // Fallback to in-memory storage
  const memoryStorage: Map<string, string> = new Map();
  return {
    getItem: (key: string) => memoryStorage.get(key) || null,
    setItem: (key: string, value: string) => memoryStorage.set(key, value),
    removeItem: (key: string) => memoryStorage.delete(key),
  };
}

const storage = getStorage();

/**
 * Get authentication token from storage
 */
export function getAuthToken(): string | null {
  const token = storage.getItem(AUTH_TOKEN_KEY);

  if (!token) {
    return null;
  }

  // Check if token is expired
  if (isTokenExpired()) {
    clearAuthToken();
    return null;
  }

  return token;
}

/**
 * Set authentication token in storage
 */
export function setAuthToken(token: string, expiresIn?: number): void {
  storage.setItem(AUTH_TOKEN_KEY, token);

  if (expiresIn) {
    const expiryTime = Date.now() + expiresIn * 1000;
    storage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
  }
}

/**
 * Clear authentication token from storage
 */
export function clearAuthToken(): void {
  storage.removeItem(AUTH_TOKEN_KEY);
  storage.removeItem(TOKEN_EXPIRY_KEY);
}

/**
 * Check if token is expired
 */
export function isTokenExpired(): boolean {
  const expiryTime = storage.getItem(TOKEN_EXPIRY_KEY);

  if (!expiryTime) {
    return false; // No expiry set
  }

  return Date.now() >= parseInt(expiryTime, 10);
}

/**
 * Get time until token expires (in seconds)
 */
export function getTokenTTL(): number | null {
  const expiryTime = storage.getItem(TOKEN_EXPIRY_KEY);

  if (!expiryTime) {
    return null;
  }

  const ttl = (parseInt(expiryTime, 10) - Date.now()) / 1000;
  return Math.max(0, Math.floor(ttl));
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return getAuthToken() !== null;
}

/**
 * Parse JWT token (basic implementation)
 */
export function parseToken(token: string): Record<string, any> | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      return null;
    }

    const payload = parts[1];
    const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(decoded);
  } catch (e) {
    return null;
  }
}

/**
 * Get token payload
 */
export function getTokenPayload(): Record<string, any> | null {
  const token = getAuthToken();
  if (!token) {
    return null;
  }

  return parseToken(token);
}

/**
 * Refresh token before expiry
 */
export async function refreshTokenIfNeeded(
  refreshFn: () => Promise<{ token: string; expiresIn?: number }>
): Promise<boolean> {
  const ttl = getTokenTTL();

  // Refresh if token expires in less than 5 minutes
  if (ttl !== null && ttl < 300) {
    try {
      const { token, expiresIn } = await refreshFn();
      setAuthToken(token, expiresIn);
      return true;
    } catch (e) {
      clearAuthToken();
      return false;
    }
  }

  return false;
}
