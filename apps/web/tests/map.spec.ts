import { test, expect } from '@playwright/test';

test('map layers and honest camp details survive the command upgrade', async ({ page, request }) => {
  const summary = await (await request.get('/api/geography/summary')).json();
  const total = Object.values(summary.counts).reduce((n: number, v) => n + Number(v), 0);
  await page.goto('/');
  await expect(page.locator('.leaflet-interactive')).toHaveCount(total);
  await page.locator('.live-layers summary').click();
  await page.getByRole('checkbox', {name:'Roads', exact:true}).uncheck();
  await expect(page.locator('.leaflet-interactive')).toHaveCount(total - summary.counts.roads);
  await page.getByRole('checkbox', {name:'Settlements', exact:true}).uncheck();
  await page.locator('.live-map path[fill="#f5b85a"]').first().click();
  await expect(page.locator('.live-details')).toContainText('Published relief camp');
  await expect(page.locator('.live-details')).toContainText('Current availability');
  await expect(page.locator('.live-details')).toContainText('Unknown');
});

test('map failure is explicit and mobile has no page overflow', async ({page}) => {
  await page.setViewportSize({width:390,height:844});
  await page.route('**/api/geography/summary', r => r.fulfill({status:503,json:{detail:'offline'}}));
  await page.goto('/');
  await expect(page.getByRole('button',{name:'Reload map'})).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
});
