---
name: esbuild keepNames fix for Telegraf + abort-controller
description: Why keepNames:true is required in build.mjs to prevent Telegraf polling from crashing
---

## The rule
`keepNames: true` MUST stay in `artifacts/api-server/build.mjs`.

## Why
esbuild renames `abort-controller`'s `class AbortSignal` to `AbortSignal2` inside the bundle
(to avoid shadowing the native global `AbortSignal`).  This changes the class's `.name`
property to `'AbortSignal2'`.

Telegraf's bundled polling code creates an `AbortController` from that renamed abort-controller
and passes its `.signal` to node-fetch.  node-fetch's `isAbortSignal()` checks:
  `proto.constructor.name === 'AbortSignal'`
With the renamed class this returns `false` → `TypeError: Expected signal to be an instanceof AbortSignal`.

## How to apply
`keepNames: true` makes esbuild emit:
  `Object.defineProperty(AbortSignal2, 'name', {value: 'AbortSignal'})`
so the runtime name is still `'AbortSignal'` and the node-fetch check passes.

Do NOT remove this option.  The crash is silent-looking (bot fails to start, server still up).
