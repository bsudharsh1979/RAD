import { test, expect } from "@playwright/test";

test("onboarding asks which APIs you want", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText(/which APIs/i).or(page.getByText(/What should I learn/i))).toBeVisible();
});

test("main nav is live", async ({ page }) => {
  await page.goto("/");
  for (const name of ["Tutor", "Notebooks", "Digital Twins", "Assessment"]) {
    await page.getByRole("link", { name }).first().click();
    await expect(page.locator("h1")).toBeVisible();
  }
});
