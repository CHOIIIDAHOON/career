#!/usr/bin/env node
import { jobkorea } from "./platforms/jobkorea.js";
import { saramin } from "./platforms/saramin.js";
import { JobPlatform, PlatformName, SearchParams, JobPosting } from "./types.js";

const PLATFORMS: Record<string, JobPlatform> = {
  jobkorea,
  saramin,
};

function parseArgs(argv: string[]) {
  const args = [...argv];
  let companyName = "";
  let platform: PlatformName = "all";
  let page = 1;
  let searchType: "company" | "job" = "company";
  let jobCategory = "";

  while (args.length > 0) {
    const token = args.shift() as string;
    if (token === "--platform" || token === "-p") {
      const v = args.shift();
      if (v === "jobkorea" || v === "saramin" || v === "all") {
        platform = v;
      }
      continue;
    }
    if (token === "--page") {
      const v = Number(args.shift());
      if (Number.isFinite(v) && v > 0) page = v;
      continue;
    }
    if (token === "--search-type") {
      const v = args.shift();
      if (v === "company" || v === "job") searchType = v;
      continue;
    }
    if (token === "--job-category") {
      jobCategory = (args.shift() || "").trim();
      continue;
    }
    if (!companyName) {
      companyName = token;
    }
  }

  return { companyName, platform, page, searchType, jobCategory };
}

async function search(companyName: string, platform: PlatformName, page: number) {
  const params: SearchParams = { companyName, page };
  const postings: JobPosting[] = [];
  const errors: string[] = [];

  const callPlatform = async (p: JobPlatform) => {
    try {
      const res = await p.search(params);
      postings.push(...res);
    } catch (e) {
      errors.push(`${p.name}: ${e instanceof Error ? e.message : String(e)}`);
    }
  };

  if (platform === "all") {
    await Promise.all(Object.values(PLATFORMS).map(callPlatform));
  } else {
    const p = PLATFORMS[platform];
    if (p) await callPlatform(p);
  }

  return { postings, errors };
}

async function main() {
  const { companyName, platform, page, searchType, jobCategory } = parseArgs(process.argv.slice(2));
  if (!companyName) {
    console.error("usage: career-mcp-cli <query> [--platform all|jobkorea|saramin] [--page N] [--search-type company|job]");
    process.exit(1);
  }

  const { postings, errors } = await search(companyName, platform, page);
  const q = companyName.toLowerCase();
  const filteredByType =
    searchType === "job"
      ? postings.filter((p) =>
          `${p.title} ${p.jobCategory || ""}`.toLowerCase().includes(q)
        )
      : postings.filter((p) => p.companyName.toLowerCase().includes(q));
  const filtered =
    jobCategory.length > 0
      ? filteredByType.filter((p) =>
          (p.jobCategory || "").toLowerCase().includes(jobCategory.toLowerCase())
        )
      : filteredByType;
  const out = {
    query: {
      company_name: companyName,
      platform,
      page,
      search_type: searchType,
      job_category: jobCategory || null,
    },
    count: filtered.length,
    errors,
    jobs: filtered,
  };
  process.stdout.write(JSON.stringify(out, null, 2));
}

main().catch((e) => {
  console.error(e instanceof Error ? e.message : String(e));
  process.exit(1);
});
