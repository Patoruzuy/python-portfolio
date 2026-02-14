**Tweet / Social Post (short)**

I built a tiny tool so my apps feel less like plumbing: `myapp.localhost` instead of `localhost:8000`.

It worked—mostly. Packaging, Windows ports and a meddlesome gateway taught me more than I expected. Short story & lessons in my latest blog:

🔗 Read: [Devhost — When Localhost Got Fancy](./blog_post.md)

— a Uruguayan in Scotland, with a fondness for tidy URLs and bad weather.

---

**Thread / LinkedIn thread summary**

1) I wanted friendly local URLs: `myapp.localhost`. Small UX win, right? Nope—turns out it’s an entire engineering problem.

2) Built: CLI for routes, middleware for apps, optional gateway to proxy port 80. Auto-detects Flask/FastAPI and picks free ports.

3) Problems I hit: packaging differences (pip vs source), Caddy quirks on Windows (WSL steals port 80), stale config files, and a flaky CI teardown.

4) Fixes: standardized Caddyfile to a user path, improved CLI messaging, robust PID handling, and safer test cleanup.

5) Lessons: prefer simple defaults, make heavy features opt-in, test packaging parity, and give copy-paste fixes in your CLI.

6) If you build dev tools: aim for predictability over magic. The fewer hidden side-effects, the happier your users.

7) Read the full (human) writeup: `./blog_post.md` — I promise it’s short, honest, and slightly Scottish.

---

If you want, I can generate a tweet image or split this into platform-specific sizes.