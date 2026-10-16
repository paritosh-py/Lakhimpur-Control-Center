import { test, expect } from '@playwright/test';

test.describe('Team Mobile Navigation & Route Planning', () => {
  test('displays Basecamp origin, 2-leg journey, map, and enters navigation mode', async ({ page }) => {
    // Open team mobile view
    await page.goto('/team-mobile?view=team');

    // 1. Verify Basecamp origin banner
    await expect(page.locator('.basecamp-origin-card')).toContainText('Borimuri');

    // 2. Verify Destination / Route Preview and 2-Leg Journey
    await expect(page.locator('.journey-plan')).toBeVisible();
    await expect(page.locator('.journey-plan')).toContainText('Borimuri Basecamp');

    // 3. Verify Route metrics bar
    await expect(page.locator('.route-metrics-bar')).toContainText('Total Distance');
    await expect(page.locator('.route-metrics-bar')).toContainText('Travel Time');

    // 4. Verify Start Navigation button
    const navBtn = page.locator('.btn-start-navigation');
    await expect(navBtn).toBeVisible();
    await expect(navBtn).toContainText('Start Navigation');

    // 5. Click Start Navigation to enter turn-by-turn mode
    await navBtn.click();

    // 6. Verify Navigation HUD
    await expect(page.locator('.nav-hud')).toBeVisible();
    await expect(page.locator('.nav-instruction-title')).toBeVisible();
    await expect(page.locator('.nav-action-deck')).toBeVisible();
    await expect(page.locator('.nav-steps-list')).toBeVisible();

    // 7. Verify maneuver stepping
    const nextBtn = page.locator('.nav-stepper-btn.primary');
    if (await nextBtn.isEnabled()) {
      await nextBtn.click();
      await expect(page.locator('.nav-hud-step-counter')).toContainText('Step 2');
    }

    // 8. Exit Navigation mode
    await page.locator('.nav-exit-btn').click();
    await expect(page.locator('.btn-start-navigation')).toBeVisible();
  });
});
