import {test, expect} from '@playwright/test';

test.beforeEach(async ({request})=>{await request.post('/api/scenario/stop');});

test('historical playback is labeled, reset is empty, return to live removes stepping', async ({page}) => {
  const errors: string[] = []; page.on('pageerror', e => errors.push(e.message));
  await page.goto('/');
  await page.getByRole('button',{name:'Replay & exercises',exact:true}).click();
  await expect(page.locator('.exercise-banner')).toContainText('Choose a dataset');
  await page.getByRole('button',{name:'Load historical weather'}).click();
  await expect(page.locator('.exercise-banner')).toContainText('REPLAY:');
  await expect(page.locator('.exercise-banner')).toContainText('2024');
  await expect(page.locator('.exercise-banner')).toContainText('Step 1');
  await page.getByRole('button',{name:'Advance 1 hour'}).click();
  await expect(page.locator('.exercise-banner')).toContainText('Step 2');
  await page.getByRole('button',{name:'Play hourly'}).click();
  await expect(page.locator('.exercise-banner')).toContainText('Step 3');
  await page.getByRole('button',{name:'Pause playback'}).click();
  await page.getByRole('button',{name:'Reset replay'}).click();
  await expect(page.locator('.exercise-banner')).toContainText('Step 0');
  await expect(page.locator('tbody tr').first()).toContainText('Unknown');
  await page.getByRole('button',{name:'Return to live'}).click();
  await expect(page.getByText('LIVE MONITORING',{exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'Advance 1 hour'})).toHaveCount(0);
  await expect(page.locator('.exercise-banner')).toHaveCount(0);
  expect(errors).toEqual([]);
});
