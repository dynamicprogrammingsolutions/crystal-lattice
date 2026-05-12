# RepoQA Prompted Balanced ChatGPT Config

This config directory is a separate `repoqa-prompted` setup for:

- balanced per-language task slices
- OpenAI Responses runs authenticated with ChatGPT login
- `reasoning_effort: "none"`
- Docker-backed benchmark execution

## Login

Check status:

```bash
agent-evaluations auth status \
  --config-dir evaluations/benchmarks/repoqa_prompted/config/openai_chatgpt_reasoning_none_balanced \
  --agent-id repoqa-prompted-openai-chatgpt-reasoning-none
```

Start ChatGPT login:

```bash
agent-evaluations auth login-chatgpt \
  --config-dir evaluations/benchmarks/repoqa_prompted/config/openai_chatgpt_reasoning_none_balanced
```

Credentials are stored under:

- `auth/chatgpt-auth.json`
- `auth/chatgpt-rate-limits.json`

## Sample profile

The sample profile is:

- `repoqa-prompted-gpt54nano-balanced-sample-chatgpt-docker`

It runs the 20-task balanced sample with:

- `repeat_count = 3`
- schedule `30` task instances per `15` minutes
- `max_parallel_tasks = 2`

So the intended pacing is about `60` task instances in roughly `30` minutes.