import {test, expect} from '@playwright/test';

test('synthetic warnings match backend, selected map evidence and responsive warning page', async ({page,request}) => {
  await page.goto('/');
  await page.getByRole('button',{name:'Replay & exercises',exact:true}).click();
  await page.getByRole('button',{name:'Load synthetic exercise'}).click();
  await expect(page.locator('.exercise-banner')).toContainText('Step 1');
  for(let i=2;i<=10;i++) {
    await page.getByRole('button',{name:'Advance 1 hour'}).click();
    await expect(page.locator('.exercise-banner')).toContainText(`Step ${i}`);
  }
  const snapshot = await (await request.get('/api/scenario/snapshot')).json();
  await page.getByRole('button',{name:/^Warnings/}).click();
  await expect(page.locator('.warning-row')).toHaveCount(snapshot.assessments.filter((c:any)=>c.affected).length);
  const first = snapshot.assessments.find((c:any)=>c.affected);
  const row = page.locator(`[data-settlement="${first.settlement_id}"]`);
  await expect(row).toContainText(first.why);
  await row.getByText('Evidence, terrain & confidence',{exact:true}).click();
  await expect(row).toContainText(first.confidence_reason);
  await row.scrollIntoViewIfNeeded();
  await expect(page.getByTestId('timeline-label')).toBeInViewport();
  await page.screenshot({path:'../../docs/screenshots/slice2-warnings-desktop.png'});
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
  await row.scrollIntoViewIfNeeded();
  await expect(page.getByTestId('timeline-label')).toBeInViewport();
  await page.screenshot({path:'../../docs/screenshots/slice2-warnings-mobile.png'});
  await row.getByRole('button',{name:'Show on map'}).click();
  await expect(page.locator('.live-details h2')).toHaveText(first.name);
  await expect(page.locator('.live-details')).toContainText(first.why);
  await expect(page.locator('.exercise-banner')).toContainText('SIMULATION');
  await page.getByRole('button',{name:'Load historical weather'}).click();
  await expect(page.locator('.exercise-banner')).toContainText('REPLAY:');
  const replay = await (await request.get('/api/scenario/snapshot')).json();
  expect(replay.assessments.every((c:any)=>c.reports.count===0)).toBeTruthy();
});
