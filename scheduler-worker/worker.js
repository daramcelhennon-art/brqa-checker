// Cloudflare Worker that fires the BR QA Checker GitHub Actions workflow
// on a real cron schedule, working around GH's own scheduler skipping runs.
//
// Deployed with wrangler (see README.md in this directory). Requires the
// `GH_TOKEN` secret to be a fine-scoped GitHub PAT with "Actions: read &
// write" permission on the brqa-checker repo. Nothing else — the Worker
// does not need Slack/BR access; it only rings GH's doorbell.

const OWNER = "daramcelhennon-art";
const REPO = "brqa-checker";
const WORKFLOW = "qa-dispatch.yml";
const REF = "main";

export default {
  async scheduled(event, env, ctx) {
    const url = `https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW}/dispatches`;
    const resp = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.GH_TOKEN}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "brqa-scheduler-worker",
      },
      body: JSON.stringify({ ref: REF }),
    });

    // GH returns 204 No Content on success; anything else means the
    // dispatch didn't land. Log and re-throw so Cloudflare marks the
    // cron invocation as failed and it shows up in wrangler tail.
    if (!resp.ok) {
      const body = await resp.text();
      console.error(
        `GH dispatch ${resp.status} at ${new Date().toISOString()}: ${body.slice(0, 500)}`,
      );
      throw new Error(`GH dispatch failed ${resp.status}`);
    }
    console.log(`GH dispatch OK at ${new Date().toISOString()}`);
  },
};
