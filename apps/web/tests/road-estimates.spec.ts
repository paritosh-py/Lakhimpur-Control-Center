import {test,expect} from '@playwright/test';

function response(eta:number){return {model_version:'lightgbm_v2_candidate',mode:'snapshot_demo',eta_minutes:eta,source:'simulated',fetched_at:'2026-10-11T00:00:00Z',weather_retrieved_at:'2026-10-10T10:27:51.083909Z',rainfall_completion_example:'2026-10-10T10:00:00Z',matched_count:3,prediction_count:3,road_count:4,unmatched_prediction_count:0,roads:[
  {road_id:'test-low',name:'Test NT Road',road_type:'primary',length_m:26.8,recorded_road_status:'unknown',prediction:{probability_unusable:eta===30?.4:.000641,risk_level:eta===30?'MODERATE':'LOW',road_status:'unknown',data_quality_status:'CHECK_REQUIRED'}},
  {road_id:'test-high',name:'Test High Road',road_type:'tertiary',length_m:30,recorded_road_status:'closed',prediction:{probability_unusable:.7,risk_level:'HIGH',road_status:'unknown',data_quality_status:'CHECK_REQUIRED'}},
  {road_id:'test-moderate',name:'Test Moderate Road',road_type:'primary',length_m:30,recorded_road_status:'unknown',prediction:{probability_unusable:.4,risk_level:'MODERATE',road_status:'unknown',data_quality_status:'CHECK_REQUIRED'}},
  {road_id:'test-missing',name:'Test Missing Road',road_type:null,length_m:null,recorded_road_status:'unknown',prediction:null}
]};}

test('team road estimates: percentages, ETA, search, missing data, outage recovery and phone layout',async({page})=>{
  await page.setViewportSize({width:390,height:844});
  let offline=false;const requested:number[]=[];
  await page.route('**/api/ml/roads?*',async route=>{
    const eta=Number(new URL(route.request().url()).searchParams.get('eta'));requested.push(eta);
    await route.fulfill({status:offline?503:200,json:offline?{detail:'Road model unavailable. Check Wi-Fi and retry.'}:response(eta)});
  });
  await page.goto('/?view=roads#token=test-team-token');
  await expect(page.getByText('Saved-weather demo · Not live',{exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:/Test NT Road/})).toContainText('0.0641%');
  await page.getByRole('button',{name:/Test NT Road/}).click();
  await expect(page.getByRole('region',{name:'Selected road'})).toContainText('CHECK_REQUIRED');
  await expect(page.getByRole('region',{name:'Selected road'})).toContainText('unknown');
  await page.screenshot({path:'../../docs/screenshots/road-estimates-mobile.png',fullPage:true});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
  await page.getByLabel('Intended travel time').selectOption('30');
  await expect(page.getByRole('region',{name:'Selected road'})).toContainText('40.0000%');
  await page.getByLabel('Intended travel time').selectOption('120');
  await expect(page.getByRole('region',{name:'Selected road'})).toContainText('120 minutes');
  await page.getByLabel('Risk band',{exact:true}).selectOption('UNKNOWN');
  await expect(page.locator('.road-list li')).toHaveCount(1);
  await page.getByRole('button',{name:/Test Missing Road/}).click();
  await expect(page.getByRole('region',{name:'Selected road'})).toContainText('Unknown');
  await page.getByLabel('Risk band',{exact:true}).selectOption('ALL');
  await page.getByLabel('Search roads').fill('test-high');
  await expect(page.locator('.road-list li')).toHaveCount(1);
  await page.getByRole('button',{name:/Test High Road/}).click();
  await expect(page.getByRole('region',{name:'Selected road'})).toContainText('closed (reference dataset)');
  offline=true;await page.getByRole('button',{name:'Refresh estimates'}).click();
  await expect(page.getByRole('alert')).toContainText('Estimates unavailable');
  await expect(page.locator('.road-list')).toHaveCount(0);
  offline=false;await page.getByRole('button',{name:'Retry connection'}).click();
  await expect(page.locator('.road-list li')).toHaveCount(1);
  expect(requested).toContain(30);expect(requested).toContain(60);expect(requested).toContain(120);
  await expect(page.getByRole('link',{name:'Team assignments'})).toHaveAttribute('href','?view=team#token=test-team-token');
});

test('obsolete ETA responses cannot replace the newly selected arrival horizon',async({page})=>{
  await page.route('**/api/ml/roads?*',async route=>{
    const eta=Number(new URL(route.request().url()).searchParams.get('eta'));
    if(eta===60)await new Promise(resolve=>setTimeout(resolve,500));
    await route.fulfill({json:response(eta)}).catch(()=>{});
  });
  await page.goto('/?view=roads');
  await page.getByLabel('Intended travel time').selectOption('30');
  await expect(page.getByRole('button',{name:/Test NT Road/})).toContainText('40.0000%');
  await page.getByRole('button',{name:/Test NT Road/}).click();
  await expect(page.getByRole('region',{name:'Selected road'})).toContainText('30 minutes');
});
