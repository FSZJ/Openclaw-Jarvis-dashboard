import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import http from 'node:http';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT = resolve(__dirname, '..');
const ARTIFACT_DIR = resolve(ROOT, 'artifacts', 'responsive');
const BASE_URL = 'http://127.0.0.1:4173';
const HEADLESS = process.env.HEADLESS !== '0';

const VIEWPORTS = [
  { name: 'mobile-360x640', width: 360, height: 640 },
  { name: 'mobile-390x844', width: 390, height: 844 },
  { name: 'tablet-768x1024', width: 768, height: 1024 },
  { name: 'desktop-1280x720', width: 1280, height: 720 },
  { name: 'desktop-1366x768', width: 1366, height: 768 },
  { name: 'desktop-1440x900', width: 1440, height: 900 },
  { name: 'desktop-1920x1080', width: 1920, height: 1080 },
  { name: 'desktop-2560x1440', width: 2560, height: 1440 },
  { name: 'desktop-3840x2160', width: 3840, height: 2160 },
];

const NOW = new Date().toISOString();

const DASHBOARD_PAYLOAD = {
  timestamp: NOW,
  node: {
    node_id: 'node-test-1',
    display_name: 'Test Node',
    gateway_host: 'localhost',
    gateway_port: 18789,
  },
  system: {
    cpu_percent: 22.4,
    memory_percent: 37.8,
    disk_usage_percent: 44.3,
    gateway: {
      running: true,
      pid: 12345,
      uptime: '01:12:33',
    },
  },
  agents: {
    main_agent: {
      provider: 'minimax',
      model: 'MiniMax-M1',
      providers: {},
    },
    subagents_running: 2,
    subagent_runs: [
      {
        run_id: 'run-1',
        agent_name: 'planner-agent',
        status: 'running',
        start_time: NOW,
        end_time: null,
        error: null,
      },
      {
        run_id: 'run-2',
        agent_name: 'review-agent',
        status: 'completed',
        start_time: NOW,
        end_time: NOW,
        error: null,
      },
    ],
  },
  channels: {
    telegram: {
      enabled: true,
      bot_token: null,
      stream_mode: 'on',
    },
    imessage: {
      enabled: false,
    },
  },
  logs: [
    {
      file: 'gateway.err.log',
      size: 128,
      last_modified: NOW,
      error_count: 0,
      last_error: null,
    },
  ],
  todos: [
    {
      id: 'todo-1',
      title: 'Smoke-check responsive layout on all breakpoints',
      due_date: null,
      completed: false,
      list_name: '默认列表',
    },
  ],
  completed_tasks: [
    {
      id: 'done-1',
      title: 'Ship responsive foundation',
      completed_at: NOW,
      list_name: '默认列表',
    },
  ],
  minimax: {
    total: 100,
    used: 20,
    remaining: 80,
    unit: 'count',
    window_end_time: Date.now() + 60 * 60 * 1000,
    models: [{ model_name: 'MiniMax-M1', total: 100, used: 20, remaining: 80 }],
  },
  usage_panels: [
    {
      key: 'minimax',
      title: 'MiniMax',
      type: 'quota',
      panel_state: 'ready',
      source: '真实计数',
      status: 'ok',
      message: null,
      missing_fields: [],
      used: 20,
      total: 100,
      percent: 20,
      remaining_text: '80',
      refresh_window: '59m',
      models: ['MiniMax-M1'],
      updated_at: NOW,
      notes: null,
    },
  ],
};

const INTEGRATIONS_PAYLOAD = {
  version: 2,
  providers: {
    minimax: {
      enabled: true,
      group_id: '',
      quota_url: '',
      usage_is_remaining: true,
      has_api_key: true,
      api_key_masked: 'sk-cp-****abcd',
    },
    openai: {
      enabled: false,
      project_id: '',
      organization_id: '',
      has_api_key: false,
      api_key_masked: '',
    },
    gemini: {
      enabled: false,
      project_id: '',
      has_api_key: false,
      api_key_masked: '',
    },
    glm: {
      enabled: false,
      base_url: 'https://open.bigmodel.cn/api/paas/v4',
      has_api_key: false,
      api_key_masked: '',
    },
  },
};

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function waitForServer(url, timeoutMs = 30_000) {
  const start = Date.now();
  return new Promise((resolveReady, rejectReady) => {
    const probe = () => {
      const req = http.get(url, (res) => {
        res.resume();
        if (res.statusCode && res.statusCode >= 200 && res.statusCode < 500) {
          resolveReady();
        } else if (Date.now() - start > timeoutMs) {
          rejectReady(new Error(`Preview server not ready within ${timeoutMs}ms`));
        } else {
          setTimeout(probe, 300);
        }
      });
      req.on('error', () => {
        if (Date.now() - start > timeoutMs) {
          rejectReady(new Error(`Preview server not reachable within ${timeoutMs}ms`));
        } else {
          setTimeout(probe, 300);
        }
      });
    };
    probe();
  });
}

function startPreviewServer() {
  return spawn('npm', ['run', 'preview', '--', '--host', '127.0.0.1', '--port', '4173'], {
    cwd: ROOT,
    stdio: 'pipe',
    env: process.env,
  });
}

async function setupMockApi(page) {
  await page.route('**/api/**', async (route) => {
    const req = route.request();
    const method = req.method();
    const url = new URL(req.url());
    const path = url.pathname;

    if (method === 'GET' && (path === '/api/dashboard' || path === '/api/status/')) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(DASHBOARD_PAYLOAD) });
      return;
    }

    if (method === 'GET' && path === '/api/integrations/models') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(INTEGRATIONS_PAYLOAD) });
      return;
    }

    if (method === 'GET' && path === '/api/tasks/history') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
      return;
    }

    if (method === 'PUT' && path === '/api/integrations/models') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, message: 'ok', data: INTEGRATIONS_PAYLOAD }),
      });
      return;
    }

    if (method === 'POST' && path.startsWith('/api/integrations/models/') && path.endsWith('/validate')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, message: 'ok', panel: DASHBOARD_PAYLOAD.usage_panels[0] }),
      });
      return;
    }

    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }) });
  });
}

async function assertNoHorizontalOverflow(page) {
  const hasOverflow = await page.evaluate(() => {
    const root = document.documentElement;
    return root.scrollWidth > root.clientWidth + 1;
  });
  assert(!hasOverflow, 'Detected horizontal overflow on document root');
}

async function assertWithinViewportWidth(page, locator, label) {
  const box = await locator.boundingBox();
  assert(!!box, `${label} is not visible`);
  const viewport = page.viewportSize();
  assert(!!viewport, 'Viewport size unavailable');
  assert(box.x >= -1, `${label} starts outside viewport: x=${box.x}`);
  assert(box.x + box.width <= viewport.width + 1, `${label} overflows viewport width: right=${box.x + box.width}, vw=${viewport.width}`);
}

async function runViewportCase(browser, viewport) {
  const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height } });
  const page = await context.newPage();

  await page.addInitScript(() => {
    localStorage.setItem('token', 'test-token');
    localStorage.setItem('user', JSON.stringify({ username: 'tester', must_change_password: false }));
  });

  await setupMockApi(page);
  await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' });

  await page.getByText('OpenClaw Jarvis').waitFor({ state: 'visible', timeout: 10_000 });

  await assertNoHorizontalOverflow(page);
  await assertWithinViewportWidth(page, page.locator('header').first(), 'Header');
  await assertWithinViewportWidth(page, page.locator('.dashboard-main').first(), 'Main container');
  await assertWithinViewportWidth(page, page.locator('.hero-panel').first(), 'Hero panel');
  await assertWithinViewportWidth(page, page.locator('.task-main-card').first(), 'Task panel');

  await page.getByRole('button', { name: 'alerts' }).click();
  await page.getByText('异常提醒').waitFor({ state: 'visible' });
  await assertWithinViewportWidth(page, page.locator('div').filter({ hasText: '异常提醒' }).first(), 'Alerts dropdown');

  await page.getByRole('button', { name: '历史任务' }).click();
  const historyModal = page.locator('.card.glass').filter({ has: page.getByRole('heading', { name: '历史任务' }) }).first();
  await historyModal.waitFor({ state: 'visible' });
  await assertWithinViewportWidth(page, historyModal, 'History modal');
  await historyModal.getByRole('button', { name: '关闭' }).click();

  await page.getByRole('button', { name: '+ 新建任务' }).click();
  const createModal = page.locator('.card.glass').filter({ has: page.getByRole('heading', { name: '新建任务' }) }).first();
  await createModal.waitFor({ state: 'visible' });
  await assertWithinViewportWidth(page, createModal, 'Create modal');
  await createModal.getByRole('button', { name: '关闭' }).click();

  await page.getByRole('button', { name: '模型设置' }).click();
  const configModal = page.locator('.card.glass').filter({ has: page.getByRole('heading', { name: '模型配置' }) }).first();
  await configModal.waitFor({ state: 'visible' });
  await assertWithinViewportWidth(page, configModal, 'Model config modal');

  await page.screenshot({
    path: resolve(ARTIFACT_DIR, `${viewport.name}.png`),
    fullPage: true,
  });

  await context.close();
}

async function main() {
  await mkdir(ARTIFACT_DIR, { recursive: true });

  const preview = startPreviewServer();
  let previewLogs = '';
  preview.stdout.on('data', (chunk) => {
    previewLogs += chunk.toString();
  });
  preview.stderr.on('data', (chunk) => {
    previewLogs += chunk.toString();
  });

  try {
    await waitForServer(BASE_URL, 30_000);

    const browser = await chromium.launch({ headless: HEADLESS });
    const failures = [];

    for (const viewport of VIEWPORTS) {
      try {
        // eslint-disable-next-line no-console
        console.log(`Checking ${viewport.name} ...`);
        await runViewportCase(browser, viewport);
      } catch (error) {
        failures.push({ viewport: viewport.name, error: String(error?.message || error) });
      }
    }

    await browser.close();

    if (failures.length > 0) {
      // eslint-disable-next-line no-console
      console.error('\nResponsive checks failed:');
      for (const item of failures) {
        // eslint-disable-next-line no-console
        console.error(`- ${item.viewport}: ${item.error}`);
      }
      process.exitCode = 1;
      return;
    }

    // eslint-disable-next-line no-console
    console.log(`\nResponsive checks passed for ${VIEWPORTS.length} viewports.`);
  } finally {
    preview.kill('SIGTERM');
    if (previewLogs.trim().length && process.env.DEBUG_RESPONSIVE === '1') {
      // eslint-disable-next-line no-console
      console.log(previewLogs);
    }
  }
}

main().catch((error) => {
  // eslint-disable-next-line no-console
  console.error(error);
  process.exit(1);
});
