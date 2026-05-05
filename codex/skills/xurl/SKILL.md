---
name: xurl
description: Use the xurl CLI for authenticated X/Twitter API work, including reading posts, searching, checking timelines and mentions, inspecting followers/following, posting, replying, quoting, sending DMs, uploading media, and using raw X API v2 endpoints. Use when the user asks to interact with X/Twitter through xurl or asks for agent-safe X API workflows.
---

# xurl

`xurl` is a curl-like CLI for the X API. It supports shortcut commands and raw curl-style access to X API v2 endpoints. Commands return JSON to stdout.

Source basis: `xdevplatform/xurl` `SKILL.md` on `main` at commit `1a17984e8205468f6ba95e7a3a1360fbef32c255`, with local botfiles safety notes from `ZON-153`.

## Mandatory Safety

- Never read, print, parse, summarize, upload, or send `~/.xurl` or copies of it to model context.
- Never ask the user to paste credentials, tokens, client IDs, client secrets, or app secrets into chat.
- Never run auth or app-registration commands with inline secret flags in an agent session.
- Never use `--verbose` / `-v`; it can expose sensitive headers or tokens.
- Never use these sensitive flags in agent commands: `--bearer-token`, `--consumer-key`, `--consumer-secret`, `--access-token`, `--token-secret`, `--client-id`, `--client-secret`.
- Default to read-only commands. Ask for explicit user approval before any write or social action: post, reply, quote, delete, like, unlike, repost, unrepost, bookmark, unbookmark, follow, unfollow, block, unblock, mute, unmute, DM, media upload, or webhook mutation.
- Prefer dry-run or preview text before write actions when xurl does not provide a native dry-run.

## Local Setup Notes

On `Azure-A100-GPU-VM`, `ZON-153` verified a working setup:

- `xurl version` reports `xurl 1.1.0`.
- `xurl auth status` is safe to run and should be the first check.
- `self-x-app` is the intended active app, with OAuth2 user `curious_queue`.
- The OAuth callback redirect URI is `http://localhost:8080/callback`.

If re-authentication is needed on an SSH VM, do not inline secrets. The prior working pattern was:

1. Confirm the user wants to run OAuth.
2. Check what owns local port `8080`.
3. Stop any conflicting service only with explicit approval.
4. Use a browser bridge or tunnel so the browser reaches the VM callback listener.
5. Have the user complete the browser approval manually.
6. Close tunnels and restore services afterward.

## Authentication Checks

Before using xurl:

```bash
xurl auth status
xurl whoami
```

For multiple preconfigured apps:

```bash
xurl auth default prod-app
xurl auth default prod-app alice
xurl --app dev-app /2/users/me
xurl auth apps redirect-uri get prod-app
xurl auth apps redirect-uri set prod-app http://localhost:8080/callback
```

App credential registration must be done manually by the user outside the agent session. After credentials are registered, OAuth can be started with:

```bash
xurl auth oauth2
```

Examples with inline secret flags are intentionally omitted. If OAuth1 or app-only auth is needed, the user must run secret-bearing commands manually outside the agent session.

## Quick Reference

| Action | Command |
|---|---|
| Post | `xurl post "Hello world!"` |
| Reply | `xurl reply POST_ID "Nice post!"` |
| Quote | `xurl quote POST_ID "My take"` |
| Delete a post | `xurl delete POST_ID` |
| Read a post | `xurl read POST_ID` |
| Search posts | `xurl search "QUERY" -n 10` |
| Who am I | `xurl whoami` |
| Look up a user | `xurl user @handle` |
| Home timeline | `xurl timeline -n 20` |
| Mentions | `xurl mentions -n 10` |
| Like | `xurl like POST_ID` |
| Unlike | `xurl unlike POST_ID` |
| Repost | `xurl repost POST_ID` |
| Undo repost | `xurl unrepost POST_ID` |
| Bookmark | `xurl bookmark POST_ID` |
| Remove bookmark | `xurl unbookmark POST_ID` |
| List bookmarks | `xurl bookmarks -n 10` |
| List likes | `xurl likes -n 10` |
| Follow | `xurl follow @handle` |
| Unfollow | `xurl unfollow @handle` |
| List following | `xurl following -n 20` |
| List followers | `xurl followers -n 20` |
| Block | `xurl block @handle` |
| Unblock | `xurl unblock @handle` |
| Mute | `xurl mute @handle` |
| Unmute | `xurl unmute @handle` |
| Send DM | `xurl dm @handle "message"` |
| List DMs | `xurl dms -n 10` |
| Upload media | `xurl media upload path/to/file.mp4` |
| Media status | `xurl media status MEDIA_ID` |
| List apps | `xurl auth apps list` |
| View app redirect URI | `xurl auth apps redirect-uri get [NAME]` |
| Set app redirect URI | `xurl auth apps redirect-uri set NAME URI` |
| Remove app | `xurl auth apps remove NAME` |
| Set default interactively | `xurl auth default` |
| Set default by command | `xurl auth default APP_NAME [USERNAME]` |
| Use app per request | `xurl --app NAME /2/users/me` |
| Auth status | `xurl auth status` |

Post IDs can also be full post URLs, such as `https://x.com/user/status/1234567890`; xurl extracts the ID. Leading `@` is optional for usernames.

## Reading

```bash
xurl read 1234567890
xurl read https://x.com/user/status/1234567890
xurl search "golang"
xurl search "from:elonmusk" -n 20
xurl search "#buildinpublic lang:en" -n 15
xurl whoami
xurl user elonmusk
xurl user @XDevelopers
xurl timeline -n 25
xurl mentions -n 20
```

## Social Graph

Use these read commands freely after the auth check:

```bash
xurl following -n 50
xurl followers -n 50
xurl following --of elonmusk -n 20
xurl followers --of elonmusk -n 20
```

Ask for explicit approval before these write actions:

```bash
xurl follow @XDevelopers
xurl unfollow @XDevelopers
xurl block @spammer
xurl unblock @spammer
xurl mute @annoying
xurl unmute @annoying
```

## Posting And Engagement

Ask for explicit approval before running any command in this section.

```bash
xurl post "Hello world!"
xurl reply 1234567890 "Great point!"
xurl reply https://x.com/user/status/1234567890 "Agreed!"
xurl quote 1234567890 "Adding my thoughts"
xurl delete 1234567890
xurl like 1234567890
xurl unlike 1234567890
xurl repost 1234567890
xurl unrepost 1234567890
xurl bookmark 1234567890
xurl unbookmark 1234567890
```

Read-only engagement lists:

```bash
xurl bookmarks -n 20
xurl likes -n 20
```

## Direct Messages

Reading recent DMs is sensitive; confirm intent before running. Sending DMs is a write action and requires explicit approval.

```bash
xurl dms -n 10
xurl dm @someuser "message"
```

## Media Upload

Media upload is a write-adjacent action and requires explicit approval.

```bash
xurl media upload photo.jpg
xurl media upload video.mp4
xurl media upload --media-type image/jpeg --category tweet_image photo.jpg
xurl media status MEDIA_ID
xurl media status --wait MEDIA_ID
xurl post "Check this out" --media-id MEDIA_ID
```

## Raw API Access

Use raw curl-style mode for X API v2 endpoints not covered by shortcuts:

```bash
xurl /2/users/me
xurl -X POST /2/tweets -d '{"text":"Hello world!"}'
xurl -X DELETE /2/tweets/1234567890
xurl -H "Content-Type: application/json" /2/some/endpoint
xurl -s /2/tweets/search/stream
xurl https://api.x.com/2/users/me
```

Apply the same read/write approval rules to raw API access. Any raw `POST`, `PUT`, `PATCH`, or `DELETE` requires explicit approval.

## Streaming

Streaming endpoints are auto-detected. Known streaming endpoints include:

- `/2/tweets/search/stream`
- `/2/tweets/sample/stream`
- `/2/tweets/sample10/stream`

Force streaming with:

```bash
xurl -s /2/some/endpoint
```

## Output

Responses are JSON. API errors are also JSON and non-zero exit codes indicate command errors:

```json
{
  "errors": [
    {
      "message": "Not authorized",
      "code": 403
    }
  ]
}
```

## Common Workflows

### Read And Reply

```bash
xurl read https://x.com/user/status/1234567890
```

Draft the reply in chat first. Run the reply command only after explicit approval:

```bash
xurl reply 1234567890 "Here are my thoughts..."
```

### Search And Review

```bash
xurl search "topic of interest" -n 10
```

Treat likes, replies, reposts, follows, and DMs as separate write actions that need approval.

### Multiple Apps

```bash
xurl auth default prod
xurl auth oauth2
xurl auth default staging
xurl auth oauth2
xurl auth default prod alice
xurl --app staging /2/users/me
```

Credentials must already be configured manually outside the agent session.

## Error Handling

- Auth errors suggest rerunning `xurl auth oauth2` or checking tokens, but do not inspect token files.
- If X returns `client-forbidden` or `client-not-enrolled` after successful auth, check the app's X developer-console package and environment.
- If a command requires your user ID, xurl will fetch it with `/2/users/me`. When that endpoint is unreliable, use `--username USERNAME` or authenticate with `xurl auth oauth2 USERNAME`.
- If rate limited with HTTP 429, wait and retry later. Write endpoints have stricter limits than read endpoints.

## Notes

- OAuth 2.0 tokens auto-refresh when expired.
- Each app has isolated credentials, tokens, and optional stored `redirect_uri`.
- `REDIRECT_URI` in the environment takes precedence over the app's stored redirect URI, which takes precedence over the built-in default.
- Use `xurl auth apps redirect-uri get [NAME]`, `xurl auth apps redirect-uri set NAME URI`, or `xurl auth apps update NAME --redirect-uri URI` to inspect and manage callback URIs.
- A successful OAuth callback does not guarantee `/2/*` reads will work. If `client-not-enrolled` appears, verify the X app package and environment.
- Multiple OAuth 2.0 accounts can exist per app. Use `--username` / `-u` or `xurl auth default APP USER` to select one.
- When no `-u` flag is given, xurl uses the default user for the active app. If no default user is set, it uses the first available token.
