import { test, expect } from '@playwright/test';

test('live overview shows the actual API snapshot, selection and mobile layout', async ({ page, request }) => {
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));
  const response = await request.get('/api/live/conditions');
  expect(response.ok()).toBeTruthy();
  const snapshot = await response.json();
  await page.goto('/');
  await expect(page.getByText('LIVE MONITORING', { exact: true })).toBeVisible();
  await expect(page.locator('tbody tr')).toHaveCount(16);
  await expect(page.getByRole('button', { name: /Step|Start scenario|Reset$/ })).toHaveCount(0);
  const target = snapshot.settlements[0];
  await page.getByRole('button', { name: target.name, exact: true }).click();
  await expect(page.locator('.live-details h2')).toHaveText(target.name);
  await expect(page.locator('.live-details')).toContainText(target.condition);
  await expect(page.locator('.live-details')).toContainText('Open-Meteo model estimate');
  await expect(page.locator('.live-details')).toContainText('Conditions valid at');
  await page.screenshot({ path: '../../docs/screenshots/slice1-live-desktop.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  await page.screenshot({ path: '../../docs/screenshots/slice1-live-mobile.png', fullPage: true });
  expect(errors).toEqual([]);
});

test('six rainy settlements have six rainy markers; live never calls playback or warnings', async ({ page, request }) => {
  const base = await (await request.get('/api/live/conditions')).json();
  const calls: string[] = [];
  page.on('request', r => { if (/\/api\/(scenario|warnings)/.test(r.url())) calls.push(r.url()); });
  base.error = null; base.counts = { current: 16, stale: 0, unavailable: 0 }; base.raining_count = 6;
  base.settlements.forEach((p: any, i: number) => {
    p.status = 'current'; p.rain_status = i < 6 ? 'raining' : 'no_rain';
    p.condition = i < 6 ? 'Rain' : 'Overcast'; p.values.rain = i < 6 ? 2 : 0; p.values.showers = 0;
  });
  await page.route('**/api/live/conditions', r => r.fulfill({ json: base }));
  await page.goto('/');
  await expect(page.getByText('Rain reported by the weather model in 6 settlements', { exact: true })).toBeVisible();
  await expect(page.locator('.live-map path[fill="#63b7f2"]')).toHaveCount(6);
  await page.locator('.live-map path[fill="#63b7f2"]').first().click();
  await expect(page.locator('.live-details h3')).toHaveText('Rain');
  await page.reload();
  await expect(page.getByText('LIVE MONITORING', { exact: true })).toBeVisible();
  expect(calls).toEqual([]);
});

test('unavailable weather never becomes sunny or zero rainfall; map survives outage', async ({ page, request }) => {
  const base = await (await request.get('/api/live/conditions')).json();
  base.error = 'Weather provider unavailable'; base.retrieved_at = null;
  base.counts = { current: 0, stale: 0, unavailable: 16 }; base.raining_count = 0;
  base.settlements.forEach((p: any) => { p.status = 'unavailable'; p.rain_status = 'unknown'; p.condition = 'Conditions unavailable'; p.valid_at = null; Object.keys(p.values).forEach(k => p.values[k] = null); });
  await page.route('**/api/live/conditions', r => r.fulfill({ json: base }));
  await page.goto('/');
  await expect(page.getByRole('alert')).toContainText('Weather provider unavailable');
  await expect(page.locator('tbody tr')).toHaveCount(16);
  await page.getByRole('button', { name: base.settlements[0].name, exact: true }).click();
  await expect(page.locator('.live-details')).toContainText('Unknown');
  await expect(page.locator('.live-details')).not.toContainText('Sunny');
  await expect(page.getByTestId('live-map')).toBeVisible();
  await page.getByRole('button', { name: 'Data sources & coverage' }).click();
  await expect(page.getByRole('heading', { name: 'Data sources & coverage' })).toBeVisible();
});

test('backend loss marks previous readings not current', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Check for updates' })).toBeEnabled();
  await page.route('**/api/live/conditions', r => r.fulfill({ status: 503 }));
  await page.getByRole('button', { name: 'Check for updates' }).click();
  await expect(page.getByRole('alert')).toContainText('Live service could not be reached');
  await expect(page.locator('.live-feed-status')).toContainText('0 of 16');
  await expect(page.locator('tbody tr')).toHaveCount(16);
});
