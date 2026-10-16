import { test, expect } from '@playwright/test';

test.beforeEach(async ({ request }) => {
  // Ensure seeded reports are active for idempotent test runs
  const res = await request.get('/api/reports?context=live');
  if (res.ok()) {
    const data = await res.json();
    for (const r of data.reports || []) {
      if (r.status === 'closed' || r.status === 'resolved') {
        await request.post(`/api/reports/${r.id}/status?context=live`, {
          data: { status: 'new' }
        });
      }
    }
  }
});

test('citizen reports page displays AI triage cards, KPI strip, and repeat device history', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1040 });
  await page.goto('/');
  await expect(page.getByText('LIVE MONITORING', { exact: true })).toBeVisible();

  // 1. Navigate to Citizen Reports tab
  const reportsNavBtn = page.getByRole('button', { name: /Citizen reports/ });
  await expect(reportsNavBtn).toBeVisible();
  await reportsNavBtn.click();

  // 2. Check header and KPI summary strip
  await expect(page.getByRole('heading', { name: 'Ground & Citizen Reports' })).toBeVisible();
  await expect(page.locator('.kpi-card').first()).toBeVisible({ timeout: 15000 });
  await expect(page.locator('.kpi-critical')).toBeVisible();

  // 3. Verify Gemini AI callout is rendered on report cards
  await expect(page.locator('.gemini-box-header').first()).toContainText('GEMINI DISASTER TRIAGE');
  await expect(page.locator('.urgency-badge').first()).toBeVisible();
  await expect(page.locator('.ai-score-pill').first()).toBeVisible();

  // 4. Verify repeat device alert button
  const repeatBtn = page.locator('.repeat-device-alert').first();
  if (await repeatBtn.isVisible()) {
    await repeatBtn.click();
    await expect(page.locator('.device-history-collapse').first()).toBeVisible();
  }

  // 5. Test search filter
  const searchInput = page.getByPlaceholder('Search reports, sender, phone, village, or keywords…');
  await expect(searchInput).toBeVisible();
  await searchInput.fill('Kadam');
  await expect(page.locator('.report-card').first()).toBeVisible();
  await searchInput.fill('');

  // 6. Test Close Request action
  const closeBtn = page.locator('.btn-close-report').first();
  if (await closeBtn.isVisible()) {
    await closeBtn.click();
    // Switch filter to closed view to verify closed badge
    const statusSelect = page.locator('.reports-filter-selects select').first();
    await statusSelect.selectOption('closed');
    await expect(page.locator('.closed-status-badge').first()).toBeVisible();
    // Switch back to active view
    await statusSelect.selectOption('active');
  }

  // 7. Test mobile layout and verify no page overflow
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
});


