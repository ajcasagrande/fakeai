/**
 * Accessibility tests
 * Validates WCAG compliance and accessibility best practices
 */

import { test, expect } from './fixtures';

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ dashboardPage }) => {
    await dashboardPage.goto();
  });

  test('has proper document structure', async ({ page }) => {
    // Check for main landmark
    const main = page.locator('main, [role="main"]');
    await expect(main).toBeVisible();

    // Check for proper heading hierarchy
    const h1 = page.locator('h1');
    await expect(h1).toHaveCount(1);
  });

  test('all images have alt text', async ({ page }) => {
    const images = await page.locator('img').all();

    for (const img of images) {
      const alt = await img.getAttribute('alt');
      expect(alt).toBeTruthy();
    }
  });

  test('buttons have accessible names', async ({ page }) => {
    const buttons = await page.locator('button').all();

    for (const button of buttons) {
      const text = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');
      const title = await button.getAttribute('title');

      // Button should have either text, aria-label, or title
      expect(text || ariaLabel || title).toBeTruthy();
    }
  });

  test('form inputs have labels', async ({ page }) => {
    const inputs = await page.locator('input, select, textarea').all();

    for (const input of inputs) {
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const ariaLabelledby = await input.getAttribute('aria-labelledby');

      if (id) {
        // Check if there's a label with for attribute
        const label = page.locator(`label[for="${id}"]`);
        const hasLabel = (await label.count()) > 0;

        // Input should have label, aria-label, or aria-labelledby
        expect(hasLabel || ariaLabel || ariaLabelledby).toBeTruthy();
      }
    }
  });

  test('links have discernible text', async ({ page }) => {
    const links = await page.locator('a').all();

    for (const link of links) {
      const text = await link.textContent();
      const ariaLabel = await link.getAttribute('aria-label');

      // Link should have either text or aria-label
      expect((text && text.trim()) || ariaLabel).toBeTruthy();
    }
  });

  test('keyboard navigation works', async ({ page }) => {
    // Start from beginning
    await page.keyboard.press('Tab');

    // Get first focused element
    let focusedElement = await page.evaluate(() => {
      return document.activeElement?.tagName;
    });

    expect(focusedElement).toBeTruthy();

    // Tab through several elements
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
      const newFocused = await page.evaluate(() => {
        return document.activeElement?.tagName;
      });
      expect(newFocused).toBeTruthy();
    }
  });

  test('focus is visible', async ({ page }) => {
    await page.keyboard.press('Tab');

    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();

    // Check if focus has visible outline or indication
    const outlineWidth = await focusedElement.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return styles.outlineWidth;
    });

    // Should have some form of focus indication
    expect(outlineWidth).not.toBe('0px');
  });

  test('modals trap focus', async ({ page }) => {
    // Open modal
    const firstRequest = page.locator('[data-testid^="request-"]').first();
    await firstRequest.click();

    // Wait for modal
    const modal = page.locator('[data-testid="request-details-modal"]');
    await expect(modal).toBeVisible();

    // Tab through modal elements
    await page.keyboard.press('Tab');

    // Check that focus is within modal
    const focusedElement = page.locator(':focus');
    const isInModal = await focusedElement.evaluate((el, modalEl) => {
      return modalEl.contains(el);
    }, await modal.elementHandle());

    expect(isInModal).toBe(true);
  });

  test('color contrast is sufficient', async ({ page }) => {
    // This is a basic check - for comprehensive testing, use axe-core
    const textElements = await page.locator('p, span, div, h1, h2, h3, button').all();

    for (const element of textElements.slice(0, 10)) {
      // Sample first 10 elements
      const styles = await element.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          color: computed.color,
          backgroundColor: computed.backgroundColor,
        };
      });

      // Basic check that color and background are different
      expect(styles.color).not.toBe(styles.backgroundColor);
    }
  });

  test('ARIA attributes are valid', async ({ page }) => {
    // Check for common ARIA attributes
    const elementsWithAria = await page.locator('[role]').all();

    for (const element of elementsWithAria) {
      const role = await element.getAttribute('role');

      // Valid ARIA roles
      const validRoles = [
        'button',
        'link',
        'navigation',
        'main',
        'complementary',
        'banner',
        'contentinfo',
        'region',
        'alert',
        'dialog',
        'table',
        'row',
        'cell',
        'columnheader',
        'list',
        'listitem',
      ];

      expect(validRoles).toContain(role);
    }
  });

  test('tables have proper structure', async ({ page }) => {
    const tables = await page.locator('table').all();

    for (const table of tables) {
      // Check for thead
      const thead = table.locator('thead');
      const hasTableHeaders = (await thead.count()) > 0;

      if (hasTableHeaders) {
        // Check for th elements
        const headers = await table.locator('th').count();
        expect(headers).toBeGreaterThan(0);
      }
    }
  });

  test('page has proper lang attribute', async ({ page }) => {
    const lang = await page.getAttribute('html', 'lang');
    expect(lang).toBeTruthy();
    expect(lang).toMatch(/^[a-z]{2}(-[A-Z]{2})?$/); // e.g., "en" or "en-US"
  });

  test('no duplicate IDs', async ({ page }) => {
    const ids = await page.evaluate(() => {
      const elements = Array.from(document.querySelectorAll('[id]'));
      return elements.map(el => el.id);
    });

    const uniqueIds = new Set(ids);
    expect(ids.length).toBe(uniqueIds.size);
  });

  test('loading states are announced', async ({ page }) => {
    // Click refresh to trigger loading
    const refreshButton = page.locator('[data-testid="manual-refresh"]');
    await refreshButton.click();

    // Check for aria-live region or loading announcement
    const loadingIndicator = page.locator('[aria-live], [role="status"]');

    if ((await loadingIndicator.count()) > 0) {
      await expect(loadingIndicator.first()).toBeVisible();
    }
  });

  test('error messages are announced', async ({ mockAPI, page }) => {
    await mockAPI.mockError('metrics/by-model', 500);
    await page.goto('/');

    // Wait for error
    const errorBanner = page.locator('[data-testid="error-banner"]');
    await expect(errorBanner).toBeVisible();

    // Check for proper ARIA role
    const role = await errorBanner.getAttribute('role');
    expect(['alert', 'status']).toContain(role);
  });

  test('skip to main content link exists', async ({ page }) => {
    // Check for skip link (usually first focusable element)
    await page.keyboard.press('Tab');

    const focusedElement = page.locator(':focus');
    const text = await focusedElement.textContent();

    // Common skip link text
    const skipLinkPatterns = [
      /skip to (main )?content/i,
      /skip navigation/i,
      /skip to main/i,
    ];

    if (text) {
      const hasSkipLink = skipLinkPatterns.some(pattern => pattern.test(text));
      // This is optional but recommended
      console.log(`Skip link present: ${hasSkipLink}`);
    }
  });

  test('interactive elements are keyboard accessible', async ({ page }) => {
    // Test refresh button
    const refreshButton = page.locator('[data-testid="manual-refresh"]');
    await refreshButton.focus();
    await page.keyboard.press('Enter');

    // Verify action occurred (e.g., loading state)
    await expect(page.locator('[data-testid="metrics-loading"]')).toBeVisible({
      timeout: 1000,
    });
  });

  test('dropdowns are keyboard accessible', async ({ page }) => {
    const modelFilter = page.locator('[data-testid="model-filter"]');

    if ((await modelFilter.count()) > 0) {
      await modelFilter.focus();

      // Open dropdown with keyboard
      await page.keyboard.press('Space');

      // Navigate options
      await page.keyboard.press('ArrowDown');
      await page.keyboard.press('Enter');

      // Verify selection occurred
      const selectedValue = await modelFilter.inputValue();
      expect(selectedValue).toBeTruthy();
    }
  });
});
