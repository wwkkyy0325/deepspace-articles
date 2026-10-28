# From Expansion to Convergence: The Architecture Evolution of a General-Purpose Agent Runtime

## Thin UI, Thick Capability: Designing and Converging Agent-Native Software

> Version: 2026-10 · Genre: architecture evolution + design philosophy + retrievable engineering record
> For: agent-runtime engineers, AI-infrastructure engineers, backend architects, technical leads

---

## One-Sentence Conclusion

**Compress the human surface to the thinnest possible layer; make the capability surface thick.** Users express intent and see state; agents call structured capabilities directly and never pay the extra cost of "understanding a UI." This article records how one runtime evolved and converged under that principle.

---

## Quick Guide

### If You Only Have Three Minutes (Non-Specialist Readers)

- **Traditional software:** a feature is a button. Users learn the interface, memorize paths, and understand jargon.
- **Agent-native software:** a feature is an interface. Users state a goal; the UI only handles "expressing intent" and "showing state."
- **The hard part is not wiring up a model.** It is three things: keep state consistent, keep context from exploding, and keep answers honest.
- This article is about how one system turned those three things into mechanisms instead of user-facing settings.

An analogy: a restaurant. The customer reads a menu (**thin UI**); the kitchen runs a standardized process (**thick capability**). Good design does not open the kitchen to the customer, nor ask the customer to cook. It makes ordering simple and delivery reliable. Agent-era software turns the kitchen into interfaces an agent can call directly, instead of asking the agent to guess through the window what the chef is doing.

### If You Are Solving a Specific Problem

| Problem you are facing | Section |
|---|---|
| Live view and refreshed history disagree | 4.2, 5.7, 6.2 |
| Context grows without bound; cost runs away | 5.2 |
| Why prefer many turns over one very long turn | 5.2 |
| How compaction can require zero user involvement | 5.2 |
| The model sounds right but has no evidence | 5.3 |
| Serial tool calls are too slow | 5.4 |
| How many agent levels to use, and how to split work | 5.5 |
| Can a local model serve as the thinking layer? | 1.4 |
| Long tasks hang or lose their terminal state | 5.1, 5.7 |
| Make an agent operate software directly, not click a UI | 1, 5.8 |
| How memory is tiered and kept from leaking across sessions | 5.9 |
| Want to delete features but fear deleting the wrong thing | 7, 9 |
| Afraid to refactor a huge file or function | 6 |
| Want a system that manages itself | 1.3, 5.2, 5.6 |

### If You Remember Only Three Sentences

1. **Users should not manage the system.** Any design that requires user management is a mechanism that was never finished.
2. **Deep interfaces are for agents, not users.** They must be structured, semantic, and free of extra cost.
3. **Consistency comes before features.** Without a single source of truth, more features only create more inconsistency.

### How This Article Is Organized

Every design in Section 5 follows the same structure: **problem → decision → mechanism → cost → verification.** A human can start from any section; a machine can extract and reuse the fields. Appendix B is a retrieval-oriented index and a reusable checklist.

---

## Abstract

The engineering difficulty of a general-purpose agent runtime is not a single model call. It is three things over a long run: keeping state consistent across the live view, a refresh, and a reconnect; keeping context cost from growing without bound; and treating model output as an untrusted input that must be reconciled. This article describes the architecture and evolution of a general-purpose agent runtime built by one developer, and summarizes its design philosophy as "thin UI, thick capability": the human surface keeps only intent expression and state visibility; the capability surface exposes structured interfaces to agents and does not require the agent to pay extra for "using software"; the thinking layer stays in the cloud, and the device keeps only the local capabilities it genuinely needs.

The system went through three phases: capability expansion, a consistency crisis, and system convergence. The final form moved verification from a "commit gate" to the tool boundary, turned context compression from a user button into a five-layer automatic ladder, collapsed two streaming protocols into one typed event contract, and converged the agent hierarchy to one level by default and at most two. The article focuses on the criteria and practice of three large refactors (backend, middle layer, frontend), plus reliability mechanisms driven by real incidents.

**Keywords:** agent runtime; thin UI, thick capability; event sourcing; context engineering; trustworthy output; refactoring methodology

---

## 1. Introduction: The First User of Software Is Changing

### 1.1 A Judgment

In the past, the first user of software was a human: a person completed operations through a UI, and APIs were an accessory for developers to integrate.

What is changing now is that **the first user of software is gradually becoming an agent.** People no longer operate software step by step; they express a goal. The agent understands the goal, selects capabilities, executes, and reports. The UI degrades from an "operation panel" into two things:

- **An intent inlet:** let a person state the goal clearly.
- **A state outlet:** let a person know what is happening and whether to intervene.

This is not "adding a chat box to software." A chat box is only the surface. What actually has to change is **how capabilities are exposed.**

### 1.2 Thin UI, Thick Capability

This yields a design principle:

> **The surface is for humans, and thinner is better; the depth is for agents, and thicker is better.**

- **Thin UI:** humans only need to express intent, see state, and make necessary confirmations. Every extra setting, every extra wizard step, is design debt.
- **Thick capability:** every capability should have a name, a parameter schema, a return schema, error codes, permission bits, and an audit record. It should be composable, cancellable, and replayable.

The key constraint is: **a deep interface must not make the agent pay extra.**

Concretely:

- The agent must not **read screenshots and guess coordinates** — that reverse-engineers a human UI into a machine interface. It is expensive, brittle, and breaks whenever the UI changes.
- The agent must not **concatenate shell strings** — natural language into a shell is both a security problem and a parsing burden.
- The agent must not **parse human prose to infer state** — state must be structured data, not "the UI says it is running."

In one sentence: **the UI is for humans to look at; the interface is for agents to use. Both can share the same capability, but the agent must not be forced through the human channel.**

### 1.3 Three Design Corollaries

The principle yields three executable constraints:

| ID | Corollary | Meaning |
|---|---|---|
| **P1** | Users do not manage the system | Compression, thinking effort, recovery, and verification should be automatic; a setting is a patch for a missing mechanism |
| **P2** | Capabilities are exposed as interfaces | Every capability has a schema, error codes, permission bits, and audit; it is not expressed as a "button location" |
| **P3** | The system owns verification and recovery | Users should not have to judge "did it get it right?"; the system provides evidence and a rollbackable correction |

P1 is the most underestimated. It means that whenever someone asks "should we add a switch?", the default answer is no. A knob is allowed only when a mechanism cannot cover the case, and the knob must be replaceable by an automatic path.

### 1.4 A Warning: Do Not Put Models Below 14B in the Agent's Thinking Layer

This is a conclusion from experience, not a model hierarchy.

**In our experience, a local model below 14B cannot serve as the thinking layer of an agent.** It may look plausible on single-turn Q&A, but once it enters multi-step tool use, the problems multiply:

- tool names and argument formats fail more often;
- plans do not hold; the agent drifts while working;
- key constraints are forgotten in long context;
- one bad call creates a longer retry chain, and the final bill is higher than calling the cloud directly.

14B is the floor for "it runs," not the recommended value for "it runs for a long time." We write this down so the next person does not repeat the detour: **do not sculpt the agent's thinking layer on a small local model first; make the workflow and toolchain work first.**

**Local and cloud are not the same class of tool.** Local models have clear gaps in speed, effective context, tool-call reliability, and long-task stability. Cloud prices per call are still falling and quality is still rising. Comparing a local 7B/14B model with a frontier cloud model on "cost-performance" usually counts only VRAM and electricity, not failed retries, debugging time, context length, and user experience.

Local still has value, but in different positions:

| Position | Suitable for local | Why |
|---|---|---|
| Speech recognition | Yes | Privacy, offline, latency-sensitive; SenseVoice ships with the package |
| Embedding / classification / preprocessing | Optional | Narrow tasks, can run offline; vector recall is off by default |
| Agent thinking layer | No (below 14B) | Multi-step planning and tool use amplify errors |
| Long-task workhorse | No | Effective context, stability, and cost are all unfavorable |

This is not "local has no future forever." It is: **at the position of the agent's thinking layer, a small local model is not yet a good deal.** As cloud prices fall and quality rises, this judgment only gets stronger.

### 1.5 A Counterexample: Treating UI Automation as an Agent Interface

"Let the agent look at the screen and click buttons" looks universal, but it forces the agent through the human channel:

- Resolution, animation, occlusion, latency, and theme changes all become maintenance costs for the agent.
- Every step requires visual recognition; tokens and latency are far higher than one structured call.
- The UI is optimized for humans, not for machine parsing; semantic information is already lost at the visual layer.

The correct direction is a **semantic inlet**: a component tree, a capability API, structured state. The UI is only one projection of capability, not capability itself.

This also explains why "zero extra cost for deep interfaces" is a hard constraint rather than an optimization: if the agent must first "understand the UI" every time it uses software, it has not really acquired the capability.

### 1.6 Contributions

- Describe a five-layer, twenty-plus-crate agent runtime and how its three data planes (events, context, capability) are closed.
- Give the decisions and reversals of three architectural convergences, including a dual-protocol decision explicitly recorded as a counterexample.
- Summarize actionable criteria for three large refactors: behavior preservation on the backend, contract-first in the middle layer, and a golden master on the frontend.
- Give an incident-driven reliability mechanism and a method for trimming context stage by stage.
- Give a rule for agent hierarchy (one level by default, at most two) and four ordering principles for context assembly.
- Converge every design into one reusable principle: **thin UI, thick capability, and the agent pays no extra cost for an interface.**

---

## 2. The Problem: Three Default Failures of Agent-Native Software

An agent that runs for hours is, in essence, a **stateful long-running transaction service.** It faces three failures at once:

1. **Consistency failure:** the streaming view, the history after refresh, and the snapshot after reconnect give different answers for the same turn.
2. **Cost failure:** context grows linearly with turns until the model window or the bill collapses first.
3. **Trust failure:** the model claims it did something, but the evidence chain does not exist; verification happens after the draft is written, so the only remedy is a full rewrite.

Most agent projects dodge these three problems during the demo phase. Once the system is used daily, they erupt as "stuck," "the answer disappeared after refresh," and "it answered a different question." This article is about how one system moved from "it runs" to "I dare use it every day."

---

## 3. System Overview

### 3.1 Layers

```
kernel/    shared types, context protocol, telemetry, session model
infra/     database, sandbox, network, MCP, knowledge, vector, update, capability probe
app/       agent loop, server, workflow, A2A, IM, scheduler center
adapters/  first-party platform adapters (registered into the adapter table)
tools/     standalone search/browse/packaging tools
```

Dependency direction is strictly one-way: `kernel ← infra ← app ← adapters/tools`. The server only assembles; reverse dependencies are not allowed. A later pass specifically fixed an inversion where the orchestration layer depended on the route layer, moving card lifecycle, session settings, and discovery configuration back down into orchestration.

### 3.2 Three Data Planes

| Plane | Single entry | Responsibility |
|---|---|---|
| **Event plane** | Session bus (monotonic sequence + ring buffer + incremental fold) | The only truth for run state, UI rendering, and reconnect snapshots |
| **Context plane** | Single assembly entry + stage pipeline | All context enters the model only here |
| **Capability plane** | Tool registry + contribution registry | Tools, skills, workflows, MCP, channels plug in here |

**Single source of truth** is not a slogan; it is a checkable structural constraint: one state may not have a second write entry, and two implementations (Rust server and TypeScript frontend) must share one set of fold rules and assert them with the same fixtures.

### 3.3 Main Path

```
frontend (compiled into the server binary)
  → HTTP/SSE
  → server flow (command dispatch / context assembly / event pump / finalize)
  → agent loop (observe → solve → act → converge → close)
  → tools / sandbox / sub-agent pool
```

The mobile client is not in the main path; it only hosts the same core inside a system-level app. **It is a hosting form, not an architectural fork.**

---

## 4. Evolution: Three Convergences

### 4.1 Phase 1: Capability Expansion (Weeks 1–2)

Starting from an empty workspace, the first step was data models and trait boundaries, then the ReAct loop, permission broker, sandbox, memory, and context stages. The strategy was **expand first**: lay out every capability surface one could imagine, allowing duplication and roughness.

In hindsight, the most important output of this phase was not features but **boundaries**: the tool trait, the context-stage trait, the event contract, and the database interface. Once boundaries were stable, every later refactor had a place to land.

### 4.2 Phase 2: Productization and the Consistency Crisis (Weeks 3–6)

Once real use began, the problem shifted from "missing features" to "inconsistent state." Typical symptoms:

- content seen during streaming disappears after refresh;
- the same turn shows a different number of tool cards in the live view and the history view;
- after a reconnect, terminal events are lost or duplicated.

The root cause was the coexistence of **two streaming protocols** and **two fold implementations**. The second protocol was introduced for "byte compatibility," but the cost was that every fix had to be done twice, and the two sides slowly diverged.

The most important thing to record from this phase is not how many bugs were fixed, but that **the dual protocol was admitted to be a wrong decision**, and a full replacement was planned.

### 4.3 Phase 3: System Convergence (Weeks 7–13)

Convergence used "single source of truth" as its principle and proceeded in four steps:

1. **Delete the protocol:** two streaming protocols converged into one typed event contract; the old frame format was dual-parsed for one release window and then deleted.
2. **Delete capability surfaces:** the role/persona stack, cross-machine UI relay, plugin fleet, manual compact button, zero-consumption routes, and ghost stages were retired together.
3. **Refactor the skeleton:** two-thousand-line flow functions were split into lifecycle segments; eighty flat state fields were grouped by domain.
4. **Replace the frontend:** the old frontend was frozen as a golden master; the new frontend caught up in batches and then took over shipping.

The criterion for the turning point was simple: **did consistency defects fall off a cliff?** After deleting the second protocol, they went from "every day" to "rare and localizable."

### 4.4 Decisions and Reversals

| Decision | Reason at the time | Verdict |
|---|---|---|
| Introduce a second streaming protocol and keep the old encoder | Byte compatibility, gradual migration | **Counterexample:** duplicate implementations caused repeated fixes and divergence |
| Delete the second protocol; build bus + sequence + authoritative view | Single source of truth | Global turning point |
| Retire the manual compact button | The five-layer automatic ladder already covers it | Correct: less user burden |
| Retire cross-machine UI relay; the protocol carries communication only | Single responsibility | Correct: less cross-machine state coupling |
| Turn the phone into a system-level host | Permission and capability ceiling | Correct: decouple the runtime from its form |
| Expose deep capabilities as interfaces, not UI automation | Zero extra cost for agents | The project's long-term main line |

---

## 5. Key Designs

> Every section follows **problem → decision → mechanism → cost → verification**.

### 5.1 Reliability: The Bus as a Liveness Signal

**Problem:** In a real incident, the database worker was stuck behind a slow query. The run had finished, but the terminal event could not be written to the database, so the client stayed at "running" forever.

**Decision:** Do not merely add a database timeout. Switch to a **liveness signal that still works while the database is blocked** — the session bus. The watchdog detects; it does not auto-kill. A human decides whether to recover.

**Mechanism:**

- The bus records the timestamp of the last published event; the watchdog sweeps every 30 seconds and cancels a run that has been silent longer than the threshold (default 900 seconds), sending it an error event.
- Runs parked on user input or confirmation are skipped, so they are not killed by mistake.
- The cancel signal reaches the model provider, the sandbox, and the process tree.
- If a background child still holds the output pipe after the command exits, the drain is abandoned after 2 seconds and the collected output is returned.
- A parked human input has a 24-hour cap; at expiry the system persists a note and converges to disconnected.
- After five consecutive provider failures, the circuit opens for 30 seconds to avoid dragging down the process.

**Cost:** The policy is "detect + manual recovery," not full automation. The watchdog cannot interrupt an already-blocked SQLite statement (that layer has no per-statement timeout); it can only guarantee that the system knows it is stuck.

**Verification:** Unit tests cover "a silent run is cancelled and receives an error event" and "a run parked on ask_user survives the sweep"; after reproducing the real incident, health endpoints and debug logs were rechecked.

### 5.2 Context: One Entry, Per-Stage Budgets, Five-Layer Compression

**Problem:** Context grows linearly with turns. Making "compaction" a button handed the system's judgment back to the user.

**Decision:** Funnel all context through one assembly entry; make compression a five-layer automatic ladder; expose a snapshot per stage so "why context looks like this" becomes an observable, trimmable object.

**Mechanism:**

- 17 stages (counted from the actual registrations in `build_full_pipeline`: 7 default + 10 added), sorted by stable priority, each with its own token budget.
- Compression triggers: **task completion first** — when the TodoWrite list transitions to all-completed, the runtime immediately runs a background rolling compression, rolling the completed task's turns into the durable summary without waiting for a window threshold. The model can also call `roll_summary` itself. The 85%/90% window ladder is the fallback.
- The history window is no longer a fixed number of messages; it is driven by token budget. A summary watermark prevents "summary row + original row" double injection.
- Every stage emits a snapshot: name, description, message count, estimated tokens, whether it contributed. Zero-contribution stages are greyed out in the UI but not hidden; assembly order is preserved.

These **window thresholds** were first aligned with the DeepSeek Harness during the GAIA phase (80% autocompact, 70% observation masking, 16% tail retention), then calibrated to 85/85/90. They are only the fallback; the first trigger is the task boundary. The numbers changed; three principles did not: percentage-of-window, follow the model's window, and never break the prefix cache during compaction.

#### Assembly Order: Not Layout, but Information Priority

The 17 stages fall roughly into four classes:

| Class | Typical stages | Position |
|---|---|---|
| Constraints | system prompt, tool definitions, user rules, answer discipline, verification requirements | first, stable prefix |
| State | task state, workspace, plan, todo | after constraints, before retrieval |
| Knowledge | skills, memory (RRF-ranked), domain knowledge, research project | middle, by budget and relevance |
| Observations | tool results, search results, live usage | last, most volatile |

The order is not a flat list by class; it resolves four things by information priority:

1. **Stable prefix first:** system prompt, tool definitions, and user rules go first; they do not change across turns, so the prompt cache can hit. Mixing volatile content into the prefix invalidates the whole cached span.
2. **Constraints before knowledge:** rules, answer discipline, and verification requirements go before skills and memory (or at least not after them); otherwise the model reads "what it can do" before "what it must not do," and constraints get diluted.
3. **Task state before retrieval:** current task, workspace, and plan go before memory and research material; the model must know "what I am doing" before it knows "what to recall."
4. **Verification near commit:** problem modeling, candidate verification, and commit reconciliation go before the final answer; tool observations and search results go later because they are the most volatile.

In engineering terms, adding a stage is not `push` to the end. It declares a priority and accepts stable sorting; each stage must answer: which class of conflict does it resolve, and why must it be at this position?

This order was settled during the GAIA round with simple comparisons: the same question set, different stage orders, observe the failure modes. Stable prefix + constraints first + state before retrieval + verification near commit are additive; conversely, moving memory or tool observations ahead of rules first breaks "answering the wrong question" and "constraint drift." It does not need a complex ablation to be visible, so it was not changed again.

#### Single-Turn Budget: Prefer Many Turns over One Very Long Turn

Here "turn" means one model call, one context assembly — not one user request. A user request can run many turns. The point is not to make context smaller, but to **move state out of context**:

1. **Cost:** every call resends the current context; the longer the turn, the more expensive every subsequent call. Many turns + a stable prefix cache lowers the marginal cost.
2. **Quality:** long context suffers from lost-in-the-middle and attention dilution; key constraints and evidence get buried. Many turns write intermediate results into todo, files, the evidence ledger, and memory; the next turn assembles only the working set, so the signal is cleaner.
3. **Recoverability:** a very long turn loses everything on failure or cancellation; many turns have natural checkpoints, and each turn can be verified, committed, and rolled back.
4. **Intervenability:** between turns, a user can steer, confirm, or stop; a single long turn has no intervention point.
5. **Observability:** each turn has a clear input, output, and terminal state; debugging does not rely on guesswork.

The number of turns is an outcome, not a goal: the budget limits **how much each turn carries**, not how many turns run. A task runs as many turns as it needs.

So the budget is not a "save tokens" slogan; it is a **forced externalization** mechanism. Anything that does not fit in context must become a file, a todo, evidence, or memory; the next turn reassembles from those durable states. Compression is only the fallback; externalization is the main path.

#### Compression: Task Completion First, Window Thresholds as Fallback

The first trigger of compression is not a window percentage; it is the **task boundary**:

- **Task completion (preferred):** on the turn where the model moves its TodoWrite list to "all completed," the runtime immediately starts a background maintenance pass. It rolls the completed task's turns into the durable summary and advances the watermark. It fires only on the pending→done transition; `in_flight` prevents overlap; the current run's tail is picked up by a later pass. It does not wait for a usage threshold — a large-window model may never reach 90%.
- **Model-initiated:** the model can call `roll_summary` on any turn with a summary and a number of recent turns to keep (1–8, default 2; summary cap 4096 characters). The loop applies it at the next turn boundary and keeps the current working tail verbatim.
- **Window thresholds (fallback):** 85% background rolling / observation masking, 90% autocompact cliff; used for long runs without a clean task boundary or without a todo list.

Why task boundaries win: when a task completes, the outcome is known, so the process can be safely compressed into a summary; the next task starts from a clean working set; the watermark stays low, so the 90% cliff rarely fires.

After a trigger, the work is done in five layers, from cheapest to most expensive:

| Layer | What it does | Cost | Trigger |
|---|---|---|---|
| 1 Snip | Remove empty output, `ok`/`null` placeholders, cancelled results; **never** remove sandbox denials | 0 | Every turn |
| 2 ObsMask | Keep the last 5 tool results in full; compress older ones to headers | 0 | Window 85% |
| 3 Truncate | Head + tail truncation of a single tool output | 0 | Every tool output |
| 4 AutoCompact | Use an LLM to summarize the oldest messages | One LLM call | Window 90% |
| 5 Trim | Hard-drop the oldest messages | 0 | Fallback when summarization fails |

The principle is: **do the cheapest thing first; save the expensive LLM summary for last.** ObsMask waits until 85% because it rewrites the middle of the conversation, and the prefix cache after the rewrite point is invalidated; below 85%, full tool results are kept (cheap when cached); above 85%, old results are trimmed before the compaction cliff.

Several designs that were previously not worth it, but are worth it now:

1. **Append the summary; do not fold it.** The old summary message stays byte-identical, and the new summary is appended as a separate message. The `[system + old summary]` prefix keeps hitting the cache across successive compactions; only the newly appended summary pays full price. Folding rewrites the old summary's bytes and breaks the cache every time.
2. **A structured summary partitioned by durability.** The summary is not prose; it is six sections: `GOALS / CONSTRAINTS / FACTS / DONE / OPEN / NEXT`. The first four are merged deterministically by union and are never fed back to the model; only `OPEN` is fed back so the model can emit `RESOLVED` lines; `NEXT` keeps the active tail. `FACTS` must be byte-exact — paths, numbers, URLs, and commit SHAs may not be paraphrased, rounded, or shortened. This prevents the summary from drifting through "summary of a summary."
3. **The model decides when to roll.** The model can call `roll_summary` when it judges a task is finished; the loop applies it in-band, with no extra background LLM call. Background rolling is incremental: read the durable summary + watermark, fetch only post-watermark messages, merge, and advance the watermark.
4. **Calibrate the budget from real tokens.** The chars/token ratio is calibrated from the provider's real `input_tokens` with an EMA (so CJK text is not underestimated at the English 4-chars/token rate); before calibration, a CJK-aware estimator is used, so compaction and budgeting use the same ruler.
5. **A small model can compact too.** When the compaction model's window is small, messages are packed into chunks of `window - 1536` tokens and summarized one chunk at a time. If the model is unavailable, a deterministic extractive fallback keeps the head + tail + high-value lines, marked `[extractive]`, and never blocks the main loop.

Several conservative constraints from the weak-model era were removed:

| Old constraint | Now | Why |
|---|---|---|
| Compaction only at window thresholds | Task completion + model-initiated + window fallback | A large-window model may never reach 90%; the task boundary is the natural compaction point |
| Early 65% rolling summary | 85% | Early summaries hide still-useful working history |
| Early 70% observation masking | 85% | Keep more raw tool results; the model can handle it |
| Keep a fixed 4 messages | Keep a 16% token tail | Budget, not message count |
| 128k absolute rolling cap | Removed; only an operator env var remains | On a 1M window, 128k is 13%; history was hidden while the model was still mostly empty |
| Manual compact button | Removed | The automatic ladder is complete; users should not manage the system |
| Compaction must fold into the summary | Append-only summary | Preserve the prefix cache |

The last point is about stability: **compaction is a view, not a deletion.** It only deletes rows from the `messages` projection; the original messages remain in the `session_events` append log. History paging can go below the compaction floor, and the first question is still reachable. This is also why users do not need to participate in compaction: compaction does not make history disappear; it only makes the working set the model currently sees smaller.

**Cost:** thresholds are empirical and need calibration; many turns add orchestration overhead and latency; a budget that is too small interrupts too often, and one that is too large degenerates into "one very long turn"; task-boundary compaction fires per completed task, so tasks that are cut too finely cause extra summary calls — **the todo granularity is the compaction granularity**; over-compression loses detail, so history paging must remain; stage snapshots have their own maintenance cost.

**Verification:** fixed task sets + real sessions for stage-by-stage regression; prove equivalence before deleting or merging; task-boundary compaction has a unit test (TodoWrite all-completed → background summary persisted); snapshots ensure the context composition is still explainable after deletion.

### 5.3 Trustworthy Output: From Gatekeeping to Endogenous Verification

**Problem:** Early on, a set of commit gates ran after the draft was written; if it failed, the whole answer was rewritten. That was expensive, destroyed already-streamed content, and the re-prompt was generic.

**Decision:** Move verification left to the action boundary; after the run, only perform **anchored edits**, never a full rewrite.

**Mechanism:**

1. **Bookkeeping at action time:** retrieval tool results enter an evidence ledger; claims are bound with `[E#]`.
2. **Reconciliation at commit:** check coverage only; fill what is missing.
3. **Correction after the run:** independent review edits the text with anchored edits — unique match, deletion budget cap, at most 8 edits, source required, code-fence balance; if any condition fails, the whole batch degrades to failed and the original text is untouched.

**Cost:** only claims that can be bound to evidence are correctable; conclusion-level correctness still needs independent recomputation; anchored edits are conservative, preferring fewer edits to wrong edits.

**Verification:** unit tests for gates and post-verification; per-line diff in the frontend; real-run smoke; a rejected batch must leave the original text unchanged.

### 5.4 Concurrency: Three Kinds of Parallelism, Each with a Gate

**Problem:** N serial searches cost Σ(latency); but blind parallelism degrades results on dependent tasks.

**Decision:** Split into three scenarios, each with its own boundary; do not use a global `join_all`.

**Mechanism:**

| Scenario | Parallel condition | Constraint |
|---|---|---|
| Same-turn tool calls | Read-only whitelist (search, file reads, code search) | N calls from Σ(latency) to max(latency) |
| Sub-agent fan-out | Subtasks decompose into independent parts | At most 6; parallel cost no more than half the remaining wall clock |
| Background tasks | No state dependency on the main loop | Separate registry, cancellable, results persisted |

If subtasks are sequentially dependent, fan-out is explicitly forbidden. The phase machine (Scout → DeepDive → Verify → Commit) advances on the remaining budget, ensuring parallelism does not squeeze out synthesis and close-out time.

**Cost:** the read-only whitelist needs maintenance; fan-out is limited to the DeepDive window; time must be reserved for synthesis.

**Verification:** a case where a dependent task does not fan out; parallel latency behavior; sub-agent result persistence and cancellation paths.

### 5.5 Hierarchy: One Level by Default, at Most Two

**Problem:** multi-agent looks like "more parallelism," but every extra layer adds one context rebuild, one result paraphrase, and one terminal path.

**Decision:** one level by default; open a second level only when the task decomposes into independent subproblems and the sub-results can be synthesized in the current turn; never a third level.

**Mechanism:**

- **One level:** the main loop directly owns the task, tools, memory, and terminal state; a tool call is a capability call, not a "manager → worker" paraphrase.
- **Two levels:** the parent only decomposes and synthesizes; the child receives a controlled context (parent workspace, tool whitelist, permission inheritance, ≤400 characters of T1 memory, orchestrator directive); the full parent history is not copied; results are persisted and the parent is woken or steered back.
- **Fan-out has gates:** subtasks must be declared independent (`SUBTASKS: n`); parallel cost no more than 50% of the remaining wall clock; at most 6 workers.
- **Two kinds of waiting:** only results needed for this turn's synthesis (verification/comparison) are awaited in the foreground with a bounded timeout; everything else completes in the background and wakes the parent.
- **No third level:** the middle layer has no information surface of its own and becomes a message router; every hop attenuates evidence, constraints, and permissions, and terminal state, cancellation, and audit ownership become ambiguous.

The GAIA phase fixed this judgment in ADR 0009: **Supervisor / SubAgent / Verifier are soft role labels, not a hard three-tier cut.** The system has only two execution levels; the Verifier is a role, not a third layer. A hard structural hierarchy was explicitly listed as not done.

**When two levels are needed:**

1. the problem decomposes into 2–6 **independent** subproblems (parallel research, independent verification, multi-source comparison);
2. the subtask needs **isolation** (different workspace, toolset, or permission);
3. the sub-result can be **verified and synthesized**, rather than dumping raw text back into the parent context.

**Why one level is usually best:**

- context needs to be assembled only once; a child agent has to rebuild the task, tools, and constraints;
- the parent-child link is a **lossy channel**: the child's full reasoning cannot be returned losslessly, only a summary;
- terminal state and cancellation have one path; every extra layer adds a "who finished first" race;
- most tasks are sequentially dependent, and parallelism only adds coordination cost.

**Cost:** one level is slower on genuinely parallel research tasks; two levels need extra context isolation, a result format, and a wake mechanism.

**Verification:** the GAIA round did a simple validation — change the level count and the assembly order, observe failure modes, not leaderboard scores. GAIA Level-1 questions are mostly single-threaded retrieval and calculation with few independent subproblems, so one level is usually enough; two levels pay off only on genuinely decomposable tasks such as multi-source comparison and parallel retrieval. The conclusion is not "multi-agent is always worse," but: **on tasks without independent subproblems and a verifiable synthesis point, adding layers only adds failure surface — a third level brings repeated retrieval, evidence paraphrase distortion, and terminal races, not capability.** The three fan-out gates (decomposability, cost, cap 6) are the engineering form of this conclusion. See 8.3 for the per-question failure taxonomy.

### 5.6 Adaptive Thinking Effort

**Problem:** making thinking effort a user knob forces the user to guess the right level and to pay the learning cost of a conversation.

**Decision:** a **one-way ladder**: every run starts low, escalates on difficulty signals, consecutive failures, or a failed verification, and resets at the end of the run.

**Mechanism:** a process-global atomic level; one-way escalation; reset at run start. Per-run isolation is deliberately avoided — it is a per-call reasoning-depth hint, not a correctness state; a concurrent run reading an escalated value costs only a few thinking tokens and does not affect correctness.

**Cost:** concurrent runs share one hint value; in an extreme case, a hard task makes a simultaneous simple task spend slightly more thinking tokens.

**Verification:** unit tests for escalation triggers; token and latency comparisons for simple/hard tasks; a regression proving correctness is unaffected by concurrency.

### 5.7 Terminal State: A Single Exit

**Problem:** the most error-prone part of a long-running service is the exit path: multiple return/continue branches, duplicated or lost terminal events, and a reconnect stream that closes before the async verification result arrives.

**Decision:** split the loop into five segments, each mapping `continue/return` through a sentinel type into an explicit state, so there is exactly one terminal path; change the reconnect exit condition to "all registries empty."

**Mechanism:**

- five segments: `observe → solve → act → converge → close`;
- the convergence and close-out segments each have a sentinel enum, and every branch maps through it;
- the terminal event fires exactly once;
- the reconnect stream closes only when all three registries — `running ∪ background tasks ∪ post-run verification` — are empty.

**Cost:** explicit state types increase refactoring cost; the sentinel enums must match loop semantics exactly, or the loop will "look converged" while missing a branch.

**Verification:** fold fixtures asserted on both sides; unit tests for the exit conditions of silent runs, parked runs, background tasks, and post-run verification; real smoke for reconnect scenarios.

### 5.8 Agent-Facing Interface Design

**Problem:** if an agent can use software only through a human UI, it pays extra to "understand the UI": visual parsing, coordinate guessing, prose understanding, state inference. That is slow, brittle, and tightly coupled to UI changes.

**Decision:** make software capabilities **structured interfaces**; the UI is only one projection of capability. The human surface keeps intent and state; the agent surface exposes the full capability.

**Mechanism:**

- **Capabilities have names and schemas:** structured parameters, structured returns, explicit error codes, not natural-language conventions;
- **State is data:** running, waiting for confirmation, failed, and completed are typed states, not UI copy;
- **Permission is a first-class layer:** capability calls go through a permission broker; high-risk actions enter a privileged service and leave an audit record; confirmation is reserved for genuinely high-risk actions;
- **Cancellable, replayable, auditable:** every long action has a cancellation path and a terminal state; every call is recorded;
- **Semantics before vision:** use a capability API instead of clicking a UI; when a fallback is needed, use a semantic tree, not screenshot coordinates;
- **Deep interfaces are not complexity:** one feature can have one human entrance and N agent entrances; that is the thickness of the capability surface, not product bloat. The criterion is "does calling it cost the agent extra?"

**Cost:** interface design must come first; versions and compatibility must be managed; the permission surface grows and needs stricter audit and deny-by-default; legacy software without capability interfaces can only use semantic fallback.

**Verification:** every capability must be callable without opening a UI; denial paths and audit records must be inspectable; high-risk actions must have confirmation and rollback.

### 5.9 Memory: The Second Layer of State Outside Context

**Problem:** context is a working set, not a warehouse. Stuffing all history into context is expensive and noisy; throwing all history away means repeating mistakes.

**Decision:** keep long-term state outside context, sedimented through "diary → themes → facts"; context recalls only what it needs.

**Mechanism:**

- **LIGHT:** triggered by a timer/nudge; raw conversation is trimmed and appended to the diary (`diary/YYYY-MM-DD.md`), append-only, no long-term memory writes;
- **REM:** daily; extract themes from the diary into `themes.jsonl`, still no long-term memory writes;
- **DEEP:** score themes on six dimensions (relevance, frequency, query diversity, recency, consolidation, conceptual richness); after passing thresholds, consolidate with ADD / UPDATE / DELETE / NOOP, then write `facts/*.md` + SQLite FTS5 + graph;
- **Recall:** RRF-ranked injection; vector recall is optional and off by default, falling back to keywords; sub-agents receive at most 400 characters of T1 memory and no parent history.

#### Why Promotion Is Strict, Not Loose

Memory errors are asymmetric: missing a recall costs one retrieval; promoting a bad global fact pollutes every later session. The old design fell into exactly this trap — themes were stamped `global` at creation, DEEP called `passes_gates(1, 1)` while the recall threshold was 2, so it effectively looked only at confidence; a test session's temporary conclusion became permanent global memory, retrievable from every related session afterward.

The current rules are four gates:

| Gate | Rule | What it prevents |
|---|---|---|
| Birth scope | New themes/facts land only in **session working memory**; never write global at creation | A session's temporary conclusion becoming global directly |
| Promotion condition | **At least 3 real recalls** in the birth session before graduating to global/T1 | False promotion from a single LLM confidence score or a single pattern match |
| No LLM labeling | Do not ask an LLM to tag themes with "source session/type" | Labels hallucinate; that would add another drifting trust layer |
| Deletion semantics | Deleting a session purges session-scoped facts; global facts survive as "generalizations," backed by stale sweep, full-store archive, and manual deletion | Leftovers after session deletion, or an unbounded global pool |

Retrieval is also closed: a session sees only "its own session facts + global facts"; nothing is injected across sessions before graduation.

**Why strict is better:** memory pollution is a trust problem, not a recall-rate problem. Missing one recall means the user asks again; promoting one bad fact means every later session may be misled by it. A slower cold start is cheaper than "every session polluted by one dirty fact."

**Cost:** the three-stage pipeline has latency; a fact is not "globally visible immediately after the conversation"; graduation needs three real recalls, so cold start is slow; with vectors off, recall quality depends on keywords.

**Verification:** unit tests for consolidation actions (ADD/UPDATE/DELETE/NOOP); three-recall graduation, stale sweep, and cross-session non-leakage; memory audit and export.

---

## 6. The Methodology of Large Refactors

### 6.1 Backend: Behavior Preservation + Per-Commit Green + Move Audit

A two-thousand-line flow function was split into four modules (command dispatch, context assembly, event pump, finalize); a two-thousand-line loop was split into five segments (intervention, act, converge, close-out); eighty flat state fields were grouped by domain.

Rules:

- decide whether to split only by **code lines excluding tests**; do not split for uniform line counts;
- every commit passes the full test suite independently; any step can be rolled back alone;
- pure moves are audited segment by segment with `--color-moved`, proving "this is only a move";
- control-flow changes use sentinel enums, not an extra `if` wrapper.

### 6.2 Middle Layer: Contract First, Migrate Later, Delete Old Last

The middle layer is the easiest place to "change only half." The fixed order is:

1. **Survey:** map the real call surface of two protocols, two folds, and two adapters;
2. **Contract first:** define a single typed event and add cross-language fixtures;
3. **Isomorphic ends:** the server and frontend implement the same fold rules; fixtures are asserted on both sides;
4. **Delete the old path:** the old shim and old frame format are dual-parsed for one release window, then deleted entirely after confirming no callers remain.

### 6.3 Frontend: Golden Master + Batch Parity + Zero Backend Changes

The old frontend was frozen as a **golden master**, used only for comparison and as a rollback baseline. The new frontend caught up in batches (session skeleton → conversation experience → visual system), each batch verified independently. The visual rewrite insisted on "change only tokens and component forms," zero server changes and zero contract changes; existing variable names were preserved to avoid rewriting component class names as a side effect.

### 6.4 Common Rules

1. Survey before cutting;
2. Every step is rollbackable;
3. Behavior preservation needs machine criteria (tests, fixtures, move audits);
4. Delete the old path last, and leave one release window;
5. Keep the docs in sync; mark stale descriptions as "description drift" instead of pretending they did not happen.

---

## 7. How Maintainability Is Designed In

| Lever | Practice | Effect |
|---|---|---|
| Single entry | Context, events, and extensions each have one entry | New capabilities do not require changing N call sites |
| Single protocol | Two streaming protocols converged into one | Eliminates "fix it on both sides" duplicate defects |
| Contract as test | Fixtures asserted by two languages | Cross-language drift is caught in CI |
| Measurement surface | Stage snapshots, token ledger, ring-buffer logs, slow-query alerts | Problems are localizable, not guessed |
| Deletion mechanism | Three maps (crate / route / feature) + item-by-item decisions | Deletion is possible without removing ops or AI call surfaces |
| Quality gate | fmt + static checks + full tests + frontend build, pinned toolchain | Refactors do not quietly break elsewhere |
| Documentation system | Current state, task steps, and change reasons recorded separately | Context survives across sessions |

One criterion deserves its own paragraph: when deleting, **"the frontend never calls it" is not sufficient**; operations surfaces and AI call surfaces must also be excluded. Otherwise a capability that "no human clicks today but an agent calls" gets deleted by mistake. This is the other side of "thin UI, thick capability": **the interface users do not click may be exactly the interface agents need most.**

---

## 8. Evidence and Evaluation

### 8.1 Reproducible Process Metrics

- 27 crates, about 180k lines of Rust, 34k lines of frontend code;
- 1,814 automated tests; 18 cross-language golden fixtures;
- 1,084 commits in 84 days (1,139 by day 90), 55 productive working days;
- 40+ releases; peak 58 commits in one day;
- 463k lines inserted / 200k deleted; during convergence, one month's deletions reached 62% of insertions.

### 8.2 A Real Development Load: A Six-Day Mini-Program Project

Beyond those metrics, there is a complete real run: from 2026-10-22 to 10-28, the runtime was used to build a WeChat mini-program merchant client (`mp-merchant`, about 13.5k lines; the same repository had 283 commits, feat 113 / fix 89 / docs 38).

| Metric | Value |
|---|---|
| Active days / calendar span | 5 days / 7 days |
| User inputs | 252 (plus 124 system notifications) |
| Model calls | 10,419 |
| Tool calls | 11,424 (shell 9,669 / write_file 575 / read_file 526) |
| Input / output tokens | 28.6M / 4.56M |
| Cache-read tokens | 1.002B |
| Cache hit rate | 97.2% |
| Average prompt per call | about 99k tokens (about 96k from cache) |
| Average output per call | about 438 tokens |
| Tool execution latency (excluding human waits) | p50 470ms / p90 5.1s / p95 9.1s / p99 31.1s |
| Permission denials / prompts | 24 / 3 |

This table does not show "how much a mechanism improved"; it shows that **the system kept working for five active days and ten thousand model calls without degenerating into a one-off demo.** It cannot replace a controlled experiment, but it turns "is the architecture usable?" from a claim into a checkable run record.

### 8.3 Failure Taxonomy from the GAIA Phase

The internal baseline for GAIA L1 (53 questions, official type-aware scoring) was 27/53; after a per-question audit, the 26 failures fell into seven classes:

| Failure class | Count | Typical symptom |
|---|---:|---|
| Answer-shape error (computed correctly but not submitted in a scorer-readable form) | 11 | The value is in the prose, but there is no `Final answer:`, or units, commas, and explanations are mixed in |
| Wrong answer submitted | 6 | Wrong candidate, misread constraint, wrong list order |
| Retrieval dead end / anti-bot | 3 | Page moved, IP blocked, empty result treated as failure |
| Computation / tool timeout | 2 | Exact DP killed by a 30s subprocess timeout; a long crawl exceeded the wall clock |
| Vision / OCR gap | 2 | Text-only model has no image path |
| Attachment not seeded into the sandbox | 1 | The path was injected, but the sandbox did not contain only the attachment |
| Value computed but never submitted | 1 | The conclusion is in the reasoning; the final answer never states it |

Two conclusions directly changed the design:

1. **Answer shape was the largest single failure source** (11/26). Turning "computed correctly" into "submitted in a scorer-readable form" was more effective than adding another reasoning layer; this later became `AnswerDisciplineStage` (priority 2) and the final-answer contract.
2. **Changing the extractor alone did not help.** Mechanical extraction ("last sentence / any label / trailing chunk") over the 26 failures recovered only 0–2 and broke 3–4 previously passing questions; the real lever was model-side submission discipline, not the harness guessing at answers.

Later fixes pushed the internal baseline to L1 45/53 and full-165 134/165. These numbers are used only for internal regression and failure modes, not as public claims; the per-question raw JSON is lost, and the failure taxonomy was recovered from the audit documents and git records of the time.

### 8.4 Incident-Driven Verification

Three real incidents were recorded end to end as "symptom → evidence → root cause → mechanism → verification":

1. A blocked database worker caused terminal-state loss → bus watchdog + slow-statement alerts;
2. A background child holding the pipe hung the run → drain grace;
3. The device kept powering off → the cause was located from the boot reason, power-management logs, and battery nodes as a framework thermal shutdown; the fix was a read-only filesystem overlay + a supervising daemon clamp.

The value of these fixes is not the individual bug, but that **each became a permanent mechanism**, so the same class of problem does not recur.

### 8.5 Threats to Validity

Honest disclosure:

- this is a **single-developer system with limited real workloads**; process metrics cannot be extrapolated directly to team efficiency;
- stage-by-stage context trimming is **observational regression**, not a randomized controlled trial; equivalence is an engineering judgment, not a statistical conclusion;
- the per-question raw JSON from the GAIA phase is lost (not found on the local machine, backups, or the Recycle Bin); only the scripts, the 30-question set, the failure taxonomy, and internal aggregate baselines remain (L1 27/53 → 45/53, full-165 134/165). These numbers are internal regression only and are not cited publicly — the sample is small and the contamination risk is high;
- some version numbers are missing from the history, so the release process was not fully strict.

---

## 9. Lessons and Counterexamples

1. **Consistency before features.** Without a single source of truth, every new feature adds another inconsistent entry.
2. **Subtraction needs a criterion.** "Nobody uses it" is not a criterion; "does it constitute the agent's capability surface?" is.
3. **Refactoring needs machine proof.** Green builds, fixtures, and move audits turn "I think I did not break it" into "I proved I did not break it."
4. **Incidents must sediment into mechanisms.** Fixing a bug is not done; removing the conditions that let that class of bug exist is done.
5. **The thinner the UI, the thicker the interface.** One less button on the user surface means one more piece of structure on the capability surface.
6. **Do not let the agent walk through the human channel.** Screenshots, coordinates, shell concatenation, and prose parsing are all extra cost.
7. **User settings are mechanism debt.** Every knob left behind should be asked: can an automatic path replace it?
8. **Counterexamples are valuable too.** The dual-protocol decision was recorded and reviewed; that is more useful than pretending to have been right all along.
9. **Hierarchy is a cost, not a capability.** One level by default; open two only when independent subproblems and a verifiable synthesis point both hold; a third level only adds failure surface.
10. **Put the thinking layer in the cloud.** Do not use a local model below 14B as a testbed for the agent's thinking layer; the API money saved comes back as failed retries, debugging time, and user experience.
11. **Memory should prefer a missed recall over a bad promotion.** One dirty global fact pollutes every session; a missed recall only means asking again. Strict promotion is how trust is protected.

---

## 10. Conclusion

The maturity of a general-purpose agent runtime is not determined by how many tools it integrates, but by whether three things are structurally solved: whether state has only one truth, whether context can be trimmed measurably, and whether output is treated as an untrusted input that must be reconciled.

The maturity of agent-native software depends on one more thing: **whether capabilities are made into interfaces an agent can use directly, rather than functions reachable only through a human UI.**

The evolution path in this article can be compressed into one sentence:

> **Expand capabilities to their boundary first, then converge them into a system with a single source of truth; the surface is for humans and thinner is better; the depth is for agents and thicker is better, without making the agent pay extra.**

The cost of convergence is continuous deletion and refactoring; the benefit is that the system becomes predictable — and that is the difference between "usable every day" and "demoable."

---

## Appendix A: Personal Contribution and Engineering Scale

This project was completed independently by one developer, covering architecture design, core implementation, frontend, mobile hosting, deployment, and long-term maintenance.

- **Duration:** about 90 days, 55 productive working days;
- **Commits:** 1,139 (as of 2026-10-28), peak 58 in one day;
- **Scale:** 27 crates, about 180k lines of Rust, 34k lines of frontend, 5.5k lines of mobile;
- **Quality:** 1,814 tests, 18 cross-language fixtures, a complete local quality gate;
- **Delivery:** 40+ releases; desktop, mobile, and scheduler center all run.

These numbers only describe the intensity of effort; the real work is in the three convergences and three refactors in the body.

---

## Appendix B: Retrieval-Oriented Index

### B.1 Concept Dictionary

| Concept | Definition | Aliases / search terms |
|---|---|---|
| **Thin UI, thick capability** | The human surface keeps only intent and state; the capability surface exposes structured interfaces to agents | thin UI, thick API, agent-native software |
| **Single source of truth** | One authoritative write entry and one set of fold rules for a state | single source of truth, authoritative view |
| **Event bus** | Per-session monotonic sequence + ring buffer + incremental fold, the only truth for run state | session bus, event log, seq |
| **Evidence ledger** | Tool results are booked at action time; claims are bound with `[E#]` | evidence ledger, grounding, citation |
| **Anchored edit** | After the run, replace only uniquely matched spans with a budget; never rewrite the whole text | anchored edit, bounded edit |
| **Stage snapshot** | Name, message count, tokens, and contribution of each context stage | stage snapshot, context observability |
| **Sentinel terminal state** | Map continue/return through an explicit enum to a single exit | sentinel terminal state, single exit |
| **Capability interface** | A structured capability with schema, error codes, permission bits, and audit | capability API, structured tool |

### B.2 Reusable Checklist (Check Each Item When Building a Similar System)

- [ ] Is there exactly one context assembly entry?
- [ ] Is there exactly one state write entry, with the frontend and server sharing fold rules?
- [ ] Does every cross-language contract have fixtures asserted on both sides?
- [ ] Does a long task have a liveness signal, a cancellation path, and exactly one terminal state?
- [ ] Is context compression fully automatic, with an observable snapshot at every layer?
- [ ] Is verification booked at the action boundary, rather than rewriting the whole draft afterward?
- [ ] Does parallelism have three gates: whitelist, decomposability, and budget?
- [ ] Can every user-visible setting be replaced by an automatic path?
- [ ] Can every agent capability be called without opening a UI?
- [ ] Do high-risk actions have a permission broker, confirmation, audit, and rollback?
- [ ] Before deleting a feature, did you distinguish "users do not click it" from "agents call it"?
- [ ] Does every refactor commit pass independently, and is every pure move auditable?

### B.3 Scope

The method applies to: long-running agent services, software where humans and agents share one capability surface, and systems that require state consistency and traceability.

It does not fully apply to: one-off scripts, stateless Q&A, systems centered on model training/inference optimization, and pure local toy projects with no permission boundary.

---

*Company names, client names, device identifiers, and internal addresses have been removed; this article is safe to publish.*
