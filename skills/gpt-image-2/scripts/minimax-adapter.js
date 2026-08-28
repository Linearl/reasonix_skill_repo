#!/usr/bin/env node
/**
 * MiniMax 图片生成适配器
 * 把 MiniMax 的异步任务 API 包装成 OpenAI 兼容的同步格式
 * 供 gpt-image-2 的 generate.js 使用
 *
 * 用法：
 *   node scripts/minimax-adapter.js --prompt "一只猫" --model image-01 --size 1024x1024
 *
 * 环境变量：
 *   MINIMAX_TOKEN_PLAN_KEY — MiniMax Token Plan Key（必需）
 *   MINIMAX_IMAGE_MODEL    — 图片模型（默认 image-01）
 */

import https from "node:https";
import { writeFileSync, mkdirSync, existsSync } from "node:fs";
import path from "node:path";

const DEFAULT_MODEL = "image-01";
const MAX_POLL_ATTEMPTS = 60;
const POLL_INTERVAL_MS = 2000;

function getApiKey() {
  const key = process.env.MINIMAX_TOKEN_PLAN_KEY;
  if (!key) {
    console.error("ERROR: MINIMAX_TOKEN_PLAN_KEY not set");
    process.exit(1);
  }
  return key;
}

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === "--prompt" && argv[i + 1]) {
      args.prompt = argv[++i];
    } else if (argv[i] === "--promptfile" && argv[i + 1]) {
      args.promptFile = argv[++i];
    } else if (argv[i] === "--model" && argv[i + 1]) {
      args.model = argv[++i];
    } else if (argv[i] === "--size" && argv[i + 1]) {
      args.size = argv[++i];
    } else if (argv[i] === "--n" && argv[i + 1]) {
      args.n = parseInt(argv[++i], 10);
    } else if (argv[i] === "--image" && argv[i + 1]) {
      args.image = argv[++i];
    } else if (argv[i] === "--json") {
      args.json = true;
    } else if (argv[i] === "-h" || argv[i] === "--help") {
      console.log(`Usage: node scripts/minimax-adapter.js --prompt "text" [options]

Options:
  --prompt <text>     Prompt text (required)
  --promptfile <path> Load prompt from file
  --model <name>      MiniMax model (default: ${DEFAULT_MODEL})
  --size <WxH>        Output size (default: 1024x1024)
  --n <count>         Number of images (default: 1)
  --image <path>      Output path (default: garden-gpt-image-2/image/<slug>-<ts>.png)
  --json              Print JSON output`);
      process.exit(0);
    }
  }
  return args;
}

function httpPost(url, body, headers) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const options = {
      hostname: u.hostname,
      port: 443,
      path: u.pathname + u.search,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getApiKey()}`,
        ...headers,
      },
    };
    const req = https.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, body: data });
        }
      });
    });
    req.on("error", reject);
    req.write(JSON.stringify(body));
    req.end();
  });
}

function httpGet(url, headers) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const options = {
      hostname: u.hostname,
      port: 443,
      path: u.pathname + u.search,
      method: "GET",
      headers: {
        Authorization: `Bearer ${getApiKey()}`,
        ...headers,
      },
    };
    const req = https.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, body: data });
        }
      });
    });
    req.on("error", reject);
    req.end();
  });
}

function httpGetBuffer(url) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const req = https.get(url, (res) => {
      const chunks = [];
      res.on("data", (chunk) => chunks.push(chunk));
      res.on("end", () => resolve(Buffer.concat(chunks)));
    });
    req.on("error", reject);
  });
}

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fff]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 40);
}

async function createTask(prompt, model, size) {
  const url = "https://api.minimaxi.com/v1/images/generations";
  const [w, h] = (size || "1024x1024").split("x").map(Number);
  const body = {
    model: model || DEFAULT_MODEL,
    prompt: prompt,
    width: w,
    height: h,
  };
  const res = await httpPost(url, body);
  if (res.status !== 200 || !res.body?.task_id) {
    throw new Error(
      `MiniMax API error: HTTP ${res.status} - ${JSON.stringify(res.body)}`
    );
  }
  return res.body.task_id;
}

async function pollTask(taskId) {
  const url = `https://api.minimaxi.com/v1/images/generations?task_id=${taskId}`;
  for (let i = 0; i < MAX_POLL_ATTEMPTS; i++) {
    const res = await httpGet(url);
    if (res.status !== 200) {
      throw new Error(`Poll error: HTTP ${res.status}`);
    }
    const body = res.body;
    if (body.status === "done" || body.status === "completed") {
      return body;
    }
    if (body.status === "failed") {
      throw new Error(`MiniMax task failed: ${JSON.stringify(body)}`);
    }
    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
  }
  throw new Error("MiniMax task timeout");
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args.prompt && !args.promptFile) {
    console.error("ERROR: --prompt or --promptfile required");
    process.exit(1);
  }

  let prompt = args.prompt;
  if (args.promptFile) {
    const { readFile } = await import("node:fs/promises");
    prompt = await readFile(args.promptFile, "utf8");
  }

  const model = args.model || process.env.MINIMAX_IMAGE_MODEL || DEFAULT_MODEL;
  const size = args.size || "1024x1024";
  const n = args.n || 1;

  console.error(`[minimax-adapter] Creating task: model=${model}, size=${size}, n=${n}`);

  // MiniMax 不支持一次生成多张，循环生成
  const results = [];
  for (let i = 0; i < n; i++) {
    const taskId = await createTask(prompt, model, size);
    console.error(`[minimax-adapter] Task ${i + 1}/${n} created: ${taskId}`);
    const result = await pollTask(taskId);
    console.error(`[minimax-adapter] Task ${i + 1}/${n} completed`);
    results.push(result);
  }

  // 下载图片并保存
  const ts = new Date()
    .toISOString()
    .replace(/[-:T]/g, "")
    .slice(0, 14);
  const slug = slugify(prompt.slice(0, 40));
  const imageDir = args.image
    ? path.dirname(args.image)
    : "garden-gpt-image-2/image";

  if (!existsSync(imageDir)) {
    mkdirSync(imageDir, { recursive: true });
  }

  const savedPaths = [];
  for (let i = 0; i < results.length; i++) {
    const r = results[i];
    const imageUrl =
      r.output?.images?.[0]?.url ||
      r.data?.[0]?.url ||
      r.images?.[0]?.url;

    if (!imageUrl) {
      console.error(
        `[minimax-adapter] WARNING: No image URL in response for task ${i + 1}:`,
        JSON.stringify(r).slice(0, 200)
      );
      continue;
    }

    const imageBuffer = await httpGetBuffer(imageUrl);
    const suffix = n > 1 ? `-${i + 1}` : "";
    const outPath = args.image
      ? args.image
      : path.join(imageDir, `${slug}-${ts}${suffix}.png`);
    const outDir = path.dirname(outPath);
    if (!existsSync(outDir)) {
      mkdirSync(outDir, { recursive: true });
    }
    writeFileSync(outPath, imageBuffer);
    savedPaths.push(outPath);
    console.error(`[minimax-adapter] Saved: ${outPath} (${imageBuffer.length} bytes)`);
  }

  // 输出 OpenAI 兼容格式的 JSON
  const openAiFormat = {
    created: Math.floor(Date.now() / 1000),
    data: savedPaths.map((p) => ({
      b64_json: null,
      url: `file://${path.resolve(p)}`,
      revised_prompt: prompt,
    })),
    _minimax_raw: results,
  };

  if (args.json) {
    console.log(JSON.stringify(openAiFormat, null, 2));
  } else {
    for (const p of savedPaths) {
      console.log(`Saved: ${p}`);
    }
  }
}

main().catch((err) => {
  console.error(`[minimax-adapter] ERROR: ${err.message}`);
  process.exit(1);
});
