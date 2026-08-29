import { test, expect } from "@playwright/test";

test("onboarding asks which APIs you want", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText(/Ten stories/i).or(page.getByText(/Learn what the model/i))).toBeVisible();
});

test("main nav is live", async ({ page }) => {
  await page.goto("/");
  for (const name of ["Tutor", "Notebooks", "Twins", "Learn"]) {
    await page.getByRole("link", { name }).first().click();
    await expect(page.locator("h1")).toBeVisible();
  }
});
