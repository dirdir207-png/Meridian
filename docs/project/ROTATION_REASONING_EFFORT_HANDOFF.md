# Handoff — `rotation/auto` rejects explicit `reasoningEffort`

**Owner-requested handoff.** This is Harness-repository work. The ORSC / Meridian
session that wrote this document must not apply it; it is addressed to the
**Harness notification session** (workspace `/Users/stephenwest/deepseek-harness`).

## Symptom

```
This turn failed
provider "rotation" model "rotation/auto" does not support reasoning effort "high"
UNSUPPORTED_REASONING_EFFORT
```

Any turn routed through the `rotation` alias while an explicit `reasoningEffort`
is attached fails before dispatch.

## Root cause

`dsh` validates a request's `reasoningEffort` against the **declared capabilities
of the resolved model** (`packages/llm/llm/src/index.ts`, `resolveCallWithInfo`):
when `info.reasoning === undefined` and a `reasoningEffort` is requested, it
throws `UNSUPPORTED_REASONING_EFFORT`.

`rotation/auto` is a dispatcher alias, not a concrete model. `llm-fallback`
deliberately declares it with no reasoning capability
(`packages/llm/llm-fallback/src/index.ts` — `listModels` / `resolveModel` return
only `inputModalities: ['text']`).

The `agent/request` listener rewrites the winning config to the alias
(`if (selection.chainIndex < 0) return selection.config` and the
`{ ...selection.config, provider: 'rotation', model: 'rotation/auto' }` return).
If that rewrite keeps `reasoningEffort`, the host validates it against the alias
and kills the turn.

Two separate defects:

1. **Stale build.** `lib/index.js` is the loaded artifact (`main: lib/index.js`,
   `lib/` is gitignored build output). In the current working tree `lib/index.js`
   predates `src/index.ts` and does **not** contain the uncommitted
   effort-stripping edit, so even the chain-won path hands back the effort.
2. **Incomplete fix.** The uncommitted `src` edit strips the effort only on the
   chain-won branch. The `chainIndex < 0` early return still returns
   `selection.config` verbatim, so the no-route fallback hands back
   `rotation/auto` + effort. A context overflow ("nothing fits") then surfaces as
   a bogus `UNSUPPORTED_REASONING_EFFORT` instead of an overflow.

## Patch

Strip the effort on **every** path that hands the alias back. Applies to
`packages/llm/llm-fallback/src/index.ts`:

```diff
@@ -185,6 +185,22 @@
   return { type: 'finish', reason: signal?.aborted ? { kind: 'aborted', failure } : { kind: 'error', failure } }
 }
 
+/**
+ * Strip an explicit `reasoningEffort` from a config dispatched to the
+ * `rotation/auto` alias.
+ *
+ * The alias is a dispatcher with no reasoning capability of its own, so the
+ * host validates the effort against the alias and fails the turn before the
+ * adapter can strip it. The selected rung owns that setting. This must run on
+ * every path that hands the alias back, including the no-route fallback, or a
+ * context overflow surfaces as a bogus UNSUPPORTED_REASONING_EFFORT.
+ */
+function aliasSafeConfig(config: LlmCallConfig): LlmCallConfig {
+  if (config.provider !== 'rotation') return config
+  const { reasoningEffort: _drop, ...rest } = config
+  return rest
+}
+
 export function apply(ctx: Context, config: Config = { chain: [] }): void {
   validateConfig(config)
   if (config.chain.length === 0) return
@@ -264,18 +280,13 @@
         // A proposal-won selection (the session's own model fits) stays direct:
         // the chain does not describe it, so the adapter has nothing to escalate
         // to. A chain-won selection is handed to `rotation` at the measured rung.
-        if (selection.chainIndex < 0) return selection.config
+        if (selection.chainIndex < 0) return aliasSafeConfig(selection.config)
         contextStartIndexes.set(String(requestAgent.session.id), selection.chainIndex)
         lastRouted.set(String(requestAgent.session.id), {
           provider: selection.config.provider,
           model: selection.config.model,
         })
-        // `rotation/auto` is a dispatcher, not a model with a reasoning
-        // capability of its own. Do not validate the caller's effort against
-        // the alias; the selected rung owns that setting (and subStream strips
-        // it before dispatch when the rung does not support it).
-        const { reasoningEffort: _drop, ...rotationConfig } = selection.config
-        return { ...rotationConfig, provider: 'rotation', model: 'rotation/auto' }
+        return { ...aliasSafeConfig(selection.config), provider: 'rotation', model: 'rotation/auto' }
       }
       const disposePreStep = agent.ctx.on('agent/pre-step', preStepListener, { prepend: true })
       const disposeRequest = agent.ctx.on('agent/request', requestListener, { prepend: true })
```

`LlmCallConfig` is already imported in that file.

## Rebuild (required — the fix is inert until `lib/` is rebuilt)

`lib/` is gitignored build output and the running harness loads `lib/index.js`:

```
pnpm run build:lib:host
```

or for just this package: `tsc -b tsconfig.host.json && tsdown --env.DSH_BUILD_FACE host`.

Then re-check `lib/index.js` actually contains `aliasSafeConfig` before retrying a
turn; a fix without a rebuild reproduces the same failure.

## Suggested regression test

In `packages/llm/llm-fallback/tests/request-regulator.spec.ts`, extend the
existing "skips candidates whose call config rejects their reasoning" coverage:
a proposal of `{ provider: 'rotation', model: 'rotation/auto', reasoningEffort: 'high' }`
with a chain that fits must return the alias config **without** `reasoningEffort`,
and the no-route fallback must also return a config with no explicit effort.

## Open question for the owner

`RotationAdapter.subStream` strips `reasoningEffort` unconditionally
(`const { reasoningEffort: _drop, ...rest } = options`). So even after this fix,
an explicit effort may never reach the concrete rung — the rung runs on its
provider default. Confirm whether that is intended; if not, the effort must be
re-applied to the rung's config rather than dropped.
