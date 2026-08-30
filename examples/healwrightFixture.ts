import { test as base } from '@playwright/test';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { SseClientTransport } from '@modelcontextprotocol/sdk/client/sse.js';

/**
 * Custom Playwright test fixture.
 * Intercepts action failures, parses the stack trace to find the failing code coordinates,
 * captures an ARIA snapshot, calls the Healwright MCP server over SSE to self-heal and
 * patch the source spec file via AST, and executes the patched action at runtime.
 */
export const test = base.extend<{
  smartPage: any;
}>({
  smartPage: async ({ page }, use) => {
    // Connect to Healwright MCP Server via SSE
    const transport = new SseClientTransport(new URL("http://localhost:8000/sse"));
    const mcpClient = new Client(
      { name: "playwright-aria-runner", version: "2.0.0" },
      { capabilities: {} }
    );

    try {
      await mcpClient.connect(transport);
      console.log("[SmartPage] Connected to Healwright Self-Healing MCP Server.");
    } catch (err) {
      console.error("[SmartPage] Failed to connect to MCP server. Running without healing.", err);
    }

    // Proxy the page object
    const smartPage = new Proxy(page, {
      get(target, prop) {
        if (prop === 'click') {
          return async (selector: string, options?: any) => {
            try {
              await target.click(selector, { timeout: 3000, ...options });
            } catch (err: any) {
              console.warn(`[SmartPage] Click failed on locator: '${selector}'. Intercepting for self-healing...`);
              
              if (!mcpClient.isConnected()) throw err;

              // 1. Capture ARIA tree snapshot and context
              const ariaSnapshot = await target.ariaSnapshot({ boxes: true });
              const url = target.url();

              // 2. Parse spec file coordinates from the error stack trace
              const coordinates = parseErrorCoordinates(err);
              console.log(`[SmartPage] Failed location coordinates:`, coordinates);

              // 3. Invoke Healwright selector healing tool
              const result = await mcpClient.callTool({
                name: "heal_selector",
                arguments: {
                  broken_selector: selector,
                  error_message: err.message,
                  dom_snapshot: ariaSnapshot, // ARIA snapshot passed here
                  target_url: url,
                  file_path: coordinates.filePath,
                  line_number: coordinates.line,
                  column_number: coordinates.column
                }
              });

              const healingPatch = JSON.parse((result.content[0] as any).text);
              console.log(`[SmartPage] Healing complete!`);
              console.log(` - Proposed Call: ${healingPatch.proposed_playwright_call}`);
              console.log(` - Status: ${healingPatch.verification_status}`);
              console.log(` - Rationale: ${healingPatch.rationale}`);

              if (healingPatch.verification_status === 'failed') {
                console.error("[SmartPage] Self-healing failed. Re-throwing original error.");
                throw err;
              }

              // 4. Evaluate the Playwright call string dynamically inside the current context
              // Inside this scope, 'page' is available for the eval expression (e.g. page.getByRole(...))
              const page = target; 
              const healedLocator = eval(healingPatch.proposed_playwright_call);

              // Retry interaction with healed locator
              await healedLocator.click(options);
            }
          };
        }

        if (prop === 'fill') {
          return async (selector: string, value: string, options?: any) => {
            try {
              await target.fill(selector, value, { timeout: 3000, ...options });
            } catch (err: any) {
              console.warn(`[SmartPage] Fill failed on locator: '${selector}'. Intercepting for self-healing...`);
              
              if (!mcpClient.isConnected()) throw err;

              const ariaSnapshot = await target.ariaSnapshot({ boxes: true });
              const url = target.url();
              const coordinates = parseErrorCoordinates(err);

              const result = await mcpClient.callTool({
                name: "heal_selector",
                arguments: {
                  broken_selector: selector,
                  error_message: err.message,
                  dom_snapshot: ariaSnapshot,
                  target_url: url,
                  file_path: coordinates.filePath,
                  line_number: coordinates.line,
                  column_number: coordinates.column
                }
              });

              const healingPatch = JSON.parse((result.content[0] as any).text);
              console.log(`[SmartPage] Healing complete!`);
              console.log(` - Proposed Call: ${healingPatch.proposed_playwright_call}`);

              if (healingPatch.verification_status === 'failed') {
                throw err;
              }

              const page = target;
              const healedLocator = eval(healingPatch.proposed_playwright_call);
              await healedLocator.fill(value, options);
            }
          };
        }

        return (target as any)[prop];
      }
    });

    await use(smartPage);

    if (mcpClient.isConnected()) {
      await mcpClient.close();
    }
  }
});

/**
 * Extracts the file path, line, and column of the failing locator from an Error stack.
 */
function parseErrorCoordinates(err: Error): { filePath: string | null; line: number | null; column: number | null } {
  const stack = err.stack || "";
  // Regex to match Playwright spec stack traces (e.g., at /path/to/my.spec.ts:12:35)
  const regex = /(?:at\s+.*?\(|at\s+)([^()]*?\.spec\.ts|\.ts):(\d+):(\d+)/i;
  const match = stack.match(regex);
  if (match) {
    return {
      filePath: match[1],
      line: parseInt(match[2], 10),
      column: parseInt(match[3], 10)
    };
  }
  return { filePath: null, line: null, column: null };
}
