import { test, expect } from '@playwright/test';

test.describe.parallel('Parallel tests', () => {
  test.setTimeout(120000);
  for (let i = 0; i < 30; i++) { // Adjust the number of times you want to run the test
    test(`test run ${i}`, async ({ page }) => {
  await page.goto('about:blank');
  await page.goto('http://chat.cenia.cl/');
  await page.getByTestId('textbox').click();
  await page.getByTestId('textbox').click();
  await page.getByTestId('textbox').fill('gptlas-chile');
  await page.getByTestId('textbox').press('Tab');
  await page.getByTestId('password').fill('cenia1');
  await page.getByTestId('password').press('Enter');
  await page.locator('#component-6').click();
  await page.getByTestId('textbox').click();
  await page.getByTestId('textbox').fill(' como fue la revolucion venezolana?');
  await page.getByRole('button', { name: 'Enviar' }).click();
  await page.waitForSelector('button:has-text("🤝 Tie")', { state: 'visible', timeout: 60000 });
  await page.getByRole('button', { name: '🤝 Tie' }).click();
  await page.getByRole('button', { name: '🎲 Nueva Ronda' }).click();
});
}
});
