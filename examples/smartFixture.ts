import { test as base } from '@playwright/test';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { SseClientTransport } from '@modelcontextprotocol/sdk/client/sse.js';

/**
 * Custom Playwright test fixture extending base test.
 * Intercepts timeouts on page.click() and page.fill(), sends page state to AWARSE MCP
 * server over SSE, and retries the action with the healed selector.
 */
export const test = base.extend<{
  smartPage: any;
}>({
  smartPage: async ({ page }, use) => {
    // Initialize connection to AWARSE MCP Server via HTTP/SSE
    const transport = new SseClientTransport(new URL("http://localhost:8000/sse"));
    const mcpClient = new Client(
      { name: "playwright-test-runner", version: "1.0.0" },
      { capabilities: {} }
    );

    try {
      await mcpClient.connect(transport);
      console.log("[SmartPage Fixture] Connected to AWARSE MCP Server via SSE.");
    } catch (err) {
      console.error("[SmartPage Fixture] Failed to connect to AWARSE MCP Server. Continuing without healing.", err);
    }

    // Proxy the Playwright page object to intercept action calls
    const smartPage = new Proxy(page, {
      get(target, prop) {
        if (prop === 'click') {
          return async (selector: string, options?: any) => {
            try {
              // Attempt interaction normally with a short timeout
              await target.click(selector, { timeout: 3000, ...options });
            } catch (err: any) {
              console.warn(`[SmartPage] Click failed on selector '${selector}'. Initializing self-healing...`);
              
              if (!mcpClient.isConnected()) {
                throw err; // MCP Server unavailable, fail test
              }

              // Capture current page DOM content and URL
              const domSnapshot = await target.content();
              const url = target.url();

              // Invoke AWARSE selector healing tool
              const result = await mcpClient.callTool({
                name: "heal_selector",
                arguments: {
                  broken_selector: selector,
                  error_message: err.message,
                  dom_snapshot: domSnapshot,
                  target_url: url
                }
              });

              // Parse healing output
              const textContent = (result.content[0] as any).text;
              const healingPatch = JSON.parse(textContent);

              console.log(`[SmartPage] Healing complete!`);
              console.log(` - Resolved Selector: ${healingPatch.proposed_selector}`);
              console.log(` - Status: ${healingPatch.verification_status}`);
              console.log(` - Confidence: ${(healingPatch.confidence_score * 100).toFixed(1)}%`);
              console.log(` - Rationale: ${healingPatch.rationale}`);

              if (healingPatch.verification_status === 'failed') {
                console.error("[SmartPage] Self-healing failed. Re-throwing original exception.");
                throw err;
              }

              // Retry interaction with healed selector
              await target.click(healingPatch.proposed_selector, options);
            }
          };
        }

        if (prop === 'fill') {
          return async (selector: string, value: string, options?: any) => {
            try {
              await target.fill(selector, value, { timeout: 3000, ...options });
            } catch (err: any) {
              console.warn(`[SmartPage] Fill failed on selector '${selector}'. Initializing self-healing...`);
              
              if (!mcpClient.isConnected()) {
                throw err;
              }

              const domSnapshot = await target.content();
              const url = target.url();

              const result = await mcpClient.callTool({
                name: "heal_selector",
                arguments: {
                  broken_selector: selector,
                  error_message: err.message,
                  dom_snapshot: domSnapshot,
                  target_url: url
                }
              });

              const textContent = (result.content[0] as any).text;
              const healingPatch = JSON.parse(textContent);

              console.log(`[SmartPage] Healing complete!`);
              console.log(` - Resolved Selector: ${healingPatch.proposed_selector}`);
              console.log(` - Status: ${healingPatch.verification_status}`);

              if (healingPatch.verification_status === 'failed') {
                throw err;
              }

              await target.fill(healingPatch.proposed_selector, value, options);
            }
          };
        }

        // Return non-intercepted methods/properties directly
        return (target as any)[prop];
      }
    });

    // Provide the proxy page to the test
    await use(smartPage);

    // Cleanup
    if (mcpClient.isConnected()) {
      await mcpClient.close();
    }
  }
});
