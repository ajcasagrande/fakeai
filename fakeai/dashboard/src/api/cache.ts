/**
 * Response caching system with TTL support
 */

interface CacheEntry<T = any> {
  data: T;
  timestamp: number;
  ttl: number;
}

/**
 * Simple in-memory cache with TTL
 */
class Cache {
  private store: Map<string, CacheEntry>;
  private cleanupInterval: number;
  private cleanupTimer: NodeJS.Timeout | null;

  constructor(cleanupInterval: number = 60000) {
    this.store = new Map();
    this.cleanupInterval = cleanupInterval;
    this.cleanupTimer = null;
    this.startCleanup();
  }

  /**
   * Get cached value
   */
  get<T = any>(key: string): T | null {
    const entry = this.store.get(key);

    if (!entry) {
      return null;
    }

    // Check if entry is expired
    if (this.isExpired(entry)) {
      this.store.delete(key);
      return null;
    }

    return entry.data as T;
  }

  /**
   * Set cached value with TTL
   */
  set<T = any>(key: string, data: T, ttl: number = 60000): void {
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      ttl,
    };

    this.store.set(key, entry);
  }

  /**
   * Check if key exists and is not expired
   */
  has(key: string): boolean {
    const entry = this.store.get(key);

    if (!entry) {
      return false;
    }

    if (this.isExpired(entry)) {
      this.store.delete(key);
      return false;
    }

    return true;
  }

  /**
   * Delete cached value
   */
  delete(key: string): boolean {
    return this.store.delete(key);
  }

  /**
   * Clear all cached values
   */
  clear(): void {
    this.store.clear();
  }

  /**
   * Get cache size
   */
  size(): number {
    return this.store.size;
  }

  /**
   * Get all cache keys
   */
  keys(): string[] {
    return Array.from(this.store.keys());
  }

  /**
   * Check if entry is expired
   */
  private isExpired(entry: CacheEntry): boolean {
    return Date.now() - entry.timestamp > entry.ttl;
  }

  /**
   * Start cleanup timer
   */
  private startCleanup(): void {
    if (typeof window === 'undefined') {
      return; // Don't start cleanup in non-browser environments
    }

    this.cleanupTimer = setInterval(() => {
      this.cleanup();
    }, this.cleanupInterval);
  }

  /**
   * Stop cleanup timer
   */
  private stopCleanup(): void {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }
  }

  /**
   * Remove expired entries
   */
  private cleanup(): void {
    const now = Date.now();
    const keysToDelete: string[] = [];

    this.store.forEach((entry, key) => {
      if (now - entry.timestamp > entry.ttl) {
        keysToDelete.push(key);
      }
    });

    keysToDelete.forEach(key => this.store.delete(key));

    if (keysToDelete.length > 0) {
      console.debug(`[Cache] Cleaned up ${keysToDelete.length} expired entries`);
    }
  }

  /**
   * Destroy cache instance
   */
  destroy(): void {
    this.stopCleanup();
    this.clear();
  }
}

/**
 * Global cache instance
 */
export const cache = new Cache();

/**
 * Create a new cache instance
 */
export function createCache(cleanupInterval?: number): Cache {
  return new Cache(cleanupInterval);
}

/**
 * Cache decorator for functions
 */
export function cached<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  options: {
    ttl?: number;
    keyGenerator?: (...args: Parameters<T>) => string;
  } = {}
): T {
  const { ttl = 60000, keyGenerator } = options;

  return (async (...args: Parameters<T>) => {
    const cacheKey = keyGenerator
      ? keyGenerator(...args)
      : `${fn.name}:${JSON.stringify(args)}`;

    const cachedResult = cache.get(cacheKey);
    if (cachedResult !== null) {
      return cachedResult;
    }

    const result = await fn(...args);
    cache.set(cacheKey, result, ttl);
    return result;
  }) as T;
}
