# `spawn_agents_on_csv`

Spawns one worker agent per CSV row (batch jobs).

## Handler behavior (implementation notes)

- This is only present when agent-jobs features are enabled.
- Worker agents are expected to call `report_agent_job_result`.
