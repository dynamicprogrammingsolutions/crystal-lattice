import { expect, test } from "@playwright/test";

const shellCommand =
  "curl -fsSL https://download.crystallattice.dev/crystal-lattice-cli/install.sh | bash";
const powershellCommand =
  "irm https://download.crystallattice.dev/crystal-lattice-cli/install.ps1 | iex";
const installationDocs =
  "https://docs.crystallattice.dev/packages/application-python/installation/";

test("shows distinct command and manual installation methods", async ({
  page,
}) => {
  await page.goto("/", { waitUntil: "networkidle" });

  const chooser = page.locator("[data-installation-chooser]");
  await expect(chooser).toBeVisible();
  await expect(
    chooser.getByRole("tablist", { name: "Install Crystal Lattice" }),
  ).toBeVisible();

  const macosLinuxTab = chooser.getByRole("tab", {
    name: "macOS/Linux",
  });
  const windowsTab = chooser.getByRole("tab", { name: "Windows" });
  const manualTab = chooser.getByRole("tab", { name: "Manual" });

  await expect(macosLinuxTab).toHaveAttribute("aria-selected", "true");
  await expect(windowsTab).toHaveAttribute("aria-selected", "false");
  await expect(manualTab).toHaveAttribute("aria-selected", "false");

  const macosLinuxPanel = chooser.getByRole("tabpanel", {
    name: "macOS/Linux",
  });
  await expect(macosLinuxPanel).toBeVisible();
  await expect(macosLinuxPanel.locator("[data-install-command]")).toHaveText(
    shellCommand,
  );
  await expect(macosLinuxPanel).toContainText(
    "macOS Intel or Apple silicon · Linux x64 or ARM64",
  );
  await expect(
    macosLinuxPanel.getByRole("link", { name: "Installation guide" }),
  ).toHaveAttribute("href", installationDocs);

  await windowsTab.click();
  await expect(windowsTab).toHaveAttribute("aria-selected", "true");
  const windowsPanel = chooser.getByRole("tabpanel", { name: "Windows" });
  await expect(windowsPanel).toBeVisible();
  await expect(windowsPanel).toContainText("Windows PowerShell");
  await expect(windowsPanel.locator("[data-install-command]")).toHaveText(
    powershellCommand,
  );
  const desktopCommandMetrics = await windowsPanel
    .locator("[data-install-command-scroll]")
    .evaluate((element) => ({
      clientWidth: element.clientWidth,
      scrollWidth: element.scrollWidth,
    }));
  expect(desktopCommandMetrics.scrollWidth).toBeLessThanOrEqual(
    desktopCommandMetrics.clientWidth + 1,
  );
  await expect(windowsPanel).toContainText(
    "Windows x64 or ARM64 · No admin rights, Python, Git Bash, or WSL needed",
  );

  await manualTab.click();
  await expect(manualTab).toHaveAttribute("aria-selected", "true");
  const manualPanel = chooser.getByRole("tabpanel", { name: "Manual" });
  await expect(manualPanel).toBeVisible();
  await expect(manualPanel.locator("[data-install-copy]")).toHaveCount(0);
  await expect(
    manualPanel.getByRole("list", { name: "Available release archives" }),
  ).toContainText("Windows ARM64");
  await expect(
    manualPanel.getByRole("link", { name: "Open latest downloads" }),
  ).toHaveAttribute(
    "href",
    "https://github.com/dynamicprogrammingsolutions/crystal-lattice/releases/latest",
  );
  await expect(
    manualPanel.getByRole("link", { name: "Manual installation guide" }),
  ).toHaveAttribute("href", installationDocs);

  await expect(macosLinuxPanel).toBeHidden();
  await expect(windowsPanel).toBeHidden();
});

test("supports tab-list keyboard navigation", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  const chooser = page.locator("[data-installation-chooser]");
  const macosLinuxTab = chooser.getByRole("tab", {
    name: "macOS/Linux",
  });
  const windowsTab = chooser.getByRole("tab", { name: "Windows" });
  const manualTab = chooser.getByRole("tab", { name: "Manual" });

  await macosLinuxTab.focus();
  await page.keyboard.press("End");
  await expect(manualTab).toBeFocused();
  await expect(manualTab).toHaveAttribute("aria-selected", "true");
  await expect(manualTab).toHaveCSS("outline-style", "solid");

  await page.keyboard.press("ArrowLeft");
  await expect(windowsTab).toBeFocused();
  await expect(windowsTab).toHaveAttribute("aria-selected", "true");
  await expect(windowsTab).toHaveCSS("outline-style", "solid");

  await page.keyboard.press("Home");
  await expect(macosLinuxTab).toBeFocused();
  await expect(macosLinuxTab).toHaveAttribute("aria-selected", "true");

  await page.keyboard.press("ArrowLeft");
  await expect(manualTab).toBeFocused();
  await expect(manualTab).toHaveAttribute("aria-selected", "true");
});

test("copies the exact selected installation command", async ({
  context,
  page,
}) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await context.grantPermissions(["clipboard-read", "clipboard-write"], {
    origin: new URL(page.url()).origin,
  });

  const chooser = page.locator("[data-installation-chooser]");
  await chooser.getByRole("tab", { name: "Windows" }).click();
  const windowsPanel = chooser.getByRole("tabpanel", { name: "Windows" });
  const copyButton = windowsPanel.locator("[data-install-copy]");
  await expect(copyButton).toHaveAttribute(
    "aria-label",
    "Copy Windows install command",
  );
  await copyButton.click();

  await expect(copyButton).toHaveAttribute("data-copied", "true");
  await expect(copyButton).toHaveAttribute(
    "aria-label",
    "Copied Windows install command",
  );
  await expect
    .poll(() => page.evaluate(() => navigator.clipboard.readText()))
    .toBe(powershellCommand);
});

test("contains long commands within the chooser on a narrow phone", async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 760 });
  await page.goto("/", { waitUntil: "networkidle" });

  const chooser = page.locator("[data-installation-chooser]");
  await chooser.getByRole("tab", { name: "Manual" }).click();
  const manualDocumentWidth = await page.evaluate(
    () => document.documentElement.scrollWidth,
  );
  await chooser.getByRole("tab", { name: "Windows" }).click();

  const windowsDocumentWidth = await page.evaluate(
    () => document.documentElement.scrollWidth,
  );
  expect(windowsDocumentWidth).toBeLessThanOrEqual(manualDocumentWidth + 1);

  const chooserMetrics = await chooser.evaluate((element) => {
    const rect = element.getBoundingClientRect();
    return {
      clientWidth: element.clientWidth,
      scrollWidth: element.scrollWidth,
      left: rect.left,
      right: rect.right,
      viewportWidth: document.documentElement.clientWidth,
    };
  });
  expect(chooserMetrics.scrollWidth).toBeLessThanOrEqual(
    chooserMetrics.clientWidth + 1,
  );
  expect(Math.abs(chooserMetrics.left)).toBeLessThanOrEqual(1);
  expect(
    Math.abs(chooserMetrics.right - chooserMetrics.viewportWidth),
  ).toBeLessThanOrEqual(1);

  const macosLinuxTab = chooser.getByRole("tab", { name: "macOS/Linux" });
  const tabMetrics = await macosLinuxTab.evaluate((element) => ({
    clientWidth: element.clientWidth,
    scrollWidth: element.scrollWidth,
  }));
  expect(tabMetrics.scrollWidth).toBeLessThanOrEqual(tabMetrics.clientWidth);

  const windowsPanel = chooser.getByRole("tabpanel", { name: "Windows" });
  const commandScroller = windowsPanel.locator("[data-install-command-scroll]");
  await expect(commandScroller).toHaveCSS("overflow-x", "auto");
  const commandMetrics = await commandScroller.evaluate((element) => ({
    clientWidth: element.clientWidth,
    scrollWidth: element.scrollWidth,
  }));
  expect(commandMetrics.scrollWidth).toBeGreaterThan(
    commandMetrics.clientWidth,
  );

  await chooser.getByRole("tab", { name: "Manual" }).click();
  await expect(
    chooser.getByRole("link", { name: "Open latest downloads" }),
  ).toBeVisible();
});

test("first-success path returns to the canonical installation chooser", async ({
  page,
}) => {
  await page.goto("/", { waitUntil: "networkidle" });

  const guide = page.locator("#computer-to-phone");
  const link = guide.getByRole("link", {
    name: "Choose an installation method",
  });
  await expect(link).toHaveAttribute("href", "#install");
  await expect(guide).toContainText("crystal-lattice --help");
  await expect(guide).not.toContainText("install.sh");
  await expect(guide).not.toContainText("install.ps1");

  await link.click();
  await expect(page).toHaveURL(/#install$/);
  await expect(page.locator("#install")).toBeVisible();
});