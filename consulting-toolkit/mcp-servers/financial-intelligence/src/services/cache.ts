/**
 * Disk TTL cache under ~/.cache/financial-intelligence/.
 *
 * Best-effort: any filesystem error (unwritable home, corrupted entry, races
 * between concurrent server processes) silently falls through to a fresh
 * fetch — the cache must never turn a working data source into an error.
 *
 * Entries are JSON files named by the SHA-256 of the cache key, grouped into
 * per-namespace subdirectories. Writes go through a temp file + rename so a
 * crashed process cannot leave a half-written entry that parses.
 */

import { createHash, randomBytes } from "node:crypto";
import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import * as path from "node:path";

const HOUR_MS = 60 * 60 * 1000;

/** TTLs per data class (see the wiring in edgar.ts / fred.ts). */
export const CACHE_TTLS = {
  tickerMap: 24 * HOUR_MS, // company_tickers.json — updated ~daily by the SEC
  submissions: 6 * HOUR_MS, // CIK submissions payloads
  companyFacts: 6 * HOUR_MS, // XBRL companyfacts payloads
  fredSeries: 1 * HOUR_MS, // FRED series info + observations
  filingDocument: 7 * 24 * HOUR_MS, // filed documents are immutable once published
  sicBrowse: 24 * HOUR_MS, // browse-edgar SIC company listings
} as const;

const CACHE_ROOT = path.join(homedir(), ".cache", "financial-intelligence");

interface CacheEnvelope<T> {
  fetchedAt: number;
  data: T;
}

function entryPath(namespace: string, key: string): string {
  const digest = createHash("sha256").update(key).digest("hex");
  return path.join(CACHE_ROOT, namespace, `${digest}.json`);
}

async function readEntry<T>(file: string, ttlMs: number): Promise<T | undefined> {
  try {
    const raw = await readFile(file, "utf8");
    const envelope = JSON.parse(raw) as CacheEnvelope<T>;
    if (
      typeof envelope.fetchedAt === "number" &&
      Date.now() - envelope.fetchedAt < ttlMs &&
      "data" in envelope
    ) {
      return envelope.data;
    }
  } catch {
    // Missing, expired-by-parse-failure, or corrupted — treat as a miss.
  }
  return undefined;
}

async function writeEntry<T>(file: string, data: T): Promise<void> {
  try {
    await mkdir(path.dirname(file), { recursive: true });
    const envelope: CacheEnvelope<T> = { fetchedAt: Date.now(), data };
    const tmp = `${file}.${randomBytes(6).toString("hex")}.tmp`;
    await writeFile(tmp, JSON.stringify(envelope), "utf8");
    await rename(tmp, file);
  } catch {
    // Cache writes are best-effort.
  }
}

/**
 * Return the cached value for (namespace, key) if fresher than ttlMs;
 * otherwise call fetcher, persist its result, and return it.
 * Fetcher errors propagate — only cache I/O errors are swallowed.
 */
export async function cachedFetch<T>(
  namespace: string,
  key: string,
  ttlMs: number,
  fetcher: () => Promise<T>
): Promise<T> {
  const file = entryPath(namespace, key);
  const hit = await readEntry<T>(file, ttlMs);
  if (hit !== undefined) return hit;

  const data = await fetcher();
  if (data !== undefined) {
    await writeEntry(file, data);
  }
  return data;
}
