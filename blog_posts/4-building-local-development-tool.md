---
title: When Localhost Got Fancy: building a friendlier dev URL (and learning to love the chaos)
author: Sebastian Gomez
date: 2026-02-15
category: Python Development
tags: Python, Architecture, Local Development, Middleware, ASGI, WSGI
read_time: 5 min
image: /static/images/networking.jpg
excerpt: A human story about building a local development tool to map friendly subdomains to local ports, the engineering challenges, and lessons learned.
---

# When Localhost Got Fancy: building a friendlier dev URL (and learning to love the chaos)

*By Patoruzuy — messy code, clearer thinking.*

> I wanted to type `http://myapp.localhost` and feel like I was shipping a feature, not juggling ports. This is a short story about building that small dream, the headaches, and what I’d do differently next time.

---

## Hook: why I care (and why you might too)

Local development is supposed to be frictionless. But if you’ve ever tried to demo a feature to a teammate, or handed a QA engineer a long http://localhost:8000 URL, you know the difference between polish and chaos.

I set out to build a tiny tool so developers could use friendly subdomains (myapp.localhost) to reach services on different ports. The idea sounds trivial, but the engineering and UX trade-offs are instructive: permissions, packaging, platform quirks, and a ton of small surprises.

This piece is a human story — a short, honest account of what I built, the problems that chased me, and what I’d change. If you’re curious about local routing, middleware, or making tooling that doesn’t annoy people, keep reading.

---

## The idea, in plain language

The goal: map subdomains of a base domain (by default `localhost`) to local ports. Instead of `http://localhost:8000`, you get `http://myapp.localhost:8000` — and, optionally, remove the `:8000` by running a small gateway that forwards traffic from port 80.

There are three simple pieces to this idea:

- A way to register routes (name → port) from the command line. (“devhost add myapp 8000”).
- Middleware your app can use so it knows "I’m being accessed as `myapp.localhost`".
- An optional gateway that can proxy `myapp.localhost` (port 80) to the right port.

It sounds small. The engineering turned out to be delightfully messy.

---

## Short primer: tech and terms (no jargon, promise)

- Proxy / gateway: a lightweight program that receives HTTP requests and forwards them somewhere else. Think of it as a mail sorter for web traffic.
- Middleware (ASGI/WSGI): glue code your app can use to inspect the request and learn which subdomain was used. It’s how your Flask or FastAPI app can say “oh! you asked for `myapp`.”
- `localhost` and special-use names: modern browsers treat `*.localhost` specially so you can test things locally without exposing them on your network.

If you want to read more:
- FastAPI docs (ASGI): https://fastapi.tiangolo.com
- Flask docs (WSGI): https://flask.palletsprojects.com
- Why `localhost` is special: https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy#local_files_and_localhost
- Caddy (a common gateway): https://caddyserver.com

---

## What I built (short story)

I made a small CLI + middleware with an optional gateway mode. It can:

- register a name and a port (`devhost add myapp 8000`)
- let your app read which subdomain a request was made to (middleware)
- optionally generate a gateway configuration to proxy `myapp.localhost` on port 80 so you can omit the `:8000` in the URL

The clever bits: auto-detecting framework (Flask/FastAPI), an auto-run helper that picks a free port, and a couple of CLI UX niceties (list, remove, doctor). The rough trade-off: keep the default behavior simple (middleware + port), make the gateway optional.

---

## The real story: where things broke and what I fixed

This is the part I enjoy the most — because bugs are honest. Here are the main problems I ran into and how I resolved them.

1. **Two different modes, two different behaviors**

   Packaging vs source install created a split: when installed from source I started an internal router/gateway; when installed via PyPI the router wasn’t bundled, so the gateway behavior differed. Users were confused because the CLI behaved differently depending on how the package was installed.

   What I learned: packaging shapes UX. If a piece of functionality is critical, either include it in releases or make it clearly optional.

2. **Caddy (the gateway) is powerful — and fragile**

   Caddy solves TLS and port-80 forwarding nicely, but it introduced platform headaches (Windows admin rights, WSL holding port 80, Caddy loading stale configs). I changed the approach so generated gateway configs live in a predictable user location and made CLI error messages actionable (copy-paste commands to restart or free port 80).

   Link: Caddy docs — https://caddyserver.com/docs

3. **Windows is a different universe**

   On Windows, port ownership, services, and the hosts file behave differently. I added portable checks and helpful hints (e.g., if WSL has wsl-relay holding port 80, suggest `wsl --shutdown`) rather than silently failing.

4. **Tests and pesky teardown races**

   Continuous integration caught a teardown error: a temp directory wasn’t empty when `rmdir()` ran. The fix was to use a more robust cleanup approach that removes non-empty directories safely.

5. **Confusing docs and UX gaps**

   Because the tool had multiple modes, documentation and CLI messages occasionally left users unsure whether the router was required. I focused on clearer messaging and an explicit “you installed via pip, here’s what to expect” flow.

---

## A few concrete anecdotes (because humans enjoy stories)

- I once spent twenty minutes debugging why `devhost caddy start` said “already running” — only to find the running service was WSL’s tiny HTTP forwarder. Windows had politely stolen my port. A `wsl --shutdown` later, everything behaved.

- A teammate in France typed `http://tinder.localhost` during a demo — I had to explain we weren’t actually building a dating app, merely reusing the name for testing. We all had a laugh and I added a small validation note to the CLI.

- In CI, a teardown error turned into a lesson: don’t assume directories are empty. Tests are your friends when they fail for the right reasons.

---

## What I’d change if I did this again (lessons and recommendations)

1. Default to the simplest useful experience: middleware + explicit port. Most devs tolerate `:8000` and it avoids admin rights and system ports.
2. Make gateway/port-80 functionality opt-in. Provide a single command that launches a bundled gateway (or container) rather than touching system configs by default.
3. Ensure packaging parity: verify pip-installed CLI behaves the same way as source. Add CI jobs that install from the built package and run basic commands.
4. Keep diagnostics concise and action-oriented. People want a one-line fix. Give it to them.

---

## Visuals I plan to include

- Screenshot: the generated Caddyfile location (annotated)
- Infographic: two-mode architecture (middleware-only vs gateway)
- Graph: CI runs before/after fix (tests passing)—illustrate the CI health improvement
- GIF: one-line demo of `devhost add hello 8000` + visiting `http://hello.localhost:8000`

(Placeholders below in the repo to drop images when ready.)

---

## Notes and links for curious readers

- FastAPI (ASGI) — https://fastapi.tiangolo.com
- Flask (WSGI) — https://flask.palletsprojects.com
- Caddy — https://caddyserver.com
- MDN on localhost special-use names — https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy#local_files_and_localhost
- A practical guide to local HTTPS (if you insist) — https://localhost.run and other tunneling services

---

## Closing: why this small project matters

Developer experience is often measured in tiny things: the difference between `localhost:8000` and `myapp.localhost` is a handful of keystrokes and a lot of polish. What I built is small, opinionated, and full of lessons about packaging, platform quirks, and the difference between a feature and a friction.

If you’re building dev tooling, aim for predictable defaults, reversible changes, and clear messages. And when the machine confuses you, tell a story about it — it’s how we learn (and laugh) together.

— Gracias y slàinte. (I still pronounce URLs with a Scottish burr.)

---

<!-- Visual placeholders -->

- ![Caddyfile screenshot](/static/images/caddyfile-screenshot.svg)
- ![Architecture diagram](/static/images/architecture.png)
- ![CI test graph](/static/images/ci-graph.svg)

<!-- Demo GIF (Missing, using placeholder) -->
- ![Demo GIF](/static/images/placeholder.jpg)