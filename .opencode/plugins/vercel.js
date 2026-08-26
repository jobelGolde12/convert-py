import { tool } from "@opencode-ai/plugin"

export const VercelPlugin = async ({ project, client, $, directory, worktree }) => {
  return {
    tool: {
      vercel_deploy: tool({
        description: "Deploy the current project to Vercel. Handles linking, building, and deploying.",
        args: {
          production: tool.schema.boolean().optional().describe("Deploy to production (default: false)"),
          env: tool.schema.string().optional().describe("Additional env vars as KEY=VALUE"),
        },
        async execute(args, context) {
          const flags = args.production ? "--prod" : ""
          const envFlag = args.env ? `--env ${args.env}` : ""

          // Check if project is linked
          const { stdout: lsOutput } = await $`ls -la .vercel/ 2>/dev/null || echo "NOT_LINKED"`
          if (lsOutput.includes("NOT_LINKED")) {
            return "Project not linked to Vercel. Run `vercel link` first to connect to your Vercel project."
          }

          // Deploy
          const result = await $`vercel deploy ${flags} ${envFlag} --yes 2>&1`
          return result.stdout || result.stderr || "Deploy initiated"
        },
      }),

      vercel_logs: tool({
        description: "Fetch recent Vercel deployment logs for debugging.",
        args: {
          name: tool.schema.string().optional().describe("Deployment name (defaults to latest)"),
        },
        async execute(args, context) {
          const name = args.name || ""
          const result = await $`vercel logs ${name} 2>&1`
          return result.stdout || result.stderr || "No logs found"
        },
      }),

      vercel_env: tool({
        description: "List or set Vercel environment variables.",
        args: {
          key: tool.schema.string().optional().describe("Env var key to set (prompts for value)"),
          value: tool.schema.string().optional().describe("Env var value (required if key is set)"),
        },
        async execute(args, context) {
          if (args.key && args.value) {
            const result = await $`vercel env add ${args.key} production --value ${args.value} 2>&1`
            return result.stdout || result.stderr || "Env var set"
          }
          const result = await $`vercel env ls 2>&1`
          return result.stdout || result.stderr || "No env vars found"
        },
      }),
    },
  }
}
