# Notion Skill for Claude Code
I created this myself to have a skill-only Notion-Claude Code integration that avoids MCPs which were causing [context bloating](https://x.com/curious_queue/status/2008612572992315850?s=20).

> **Attribution**: This skill was adapted from [FastMCP Notion Skill](https://fastmcp.me/Skills/Details/334/notion) and customized for use with Claude Code.

A Claude Code skill for integrating with Notion workspaces - read/write pages, search databases, create tasks, and sync content.

## Prerequisites

Before using this skill, ensure you have the following set up:

### 1. Node.js Dependencies

```bash
npm install @notionhq/client
```

- `@notionhq/client` - Official Notion SDK (currently v5.6.0)

**Note**: This documentation is verified for SDK v5.6.0. API methods may differ in other versions.

### 2. Environment Variables

Set these in your shell environment (e.g., via `.bashrc`, `.zshrc`, `direnv`, or `source .env`):

```bash
export NOTION_API_KEY=ntn_xxxxxxxxxxxxxxxxxxxxx
export NOTION_DATABASE_ID=your_database_id_here  # Optional
```

### 3. Notion Integration Setup

1. Go to https://www.notion.so/my-integrations
2. Click "New integration"
3. Name it and select your workspace
4. Copy the "Internal Integration Token" (starts with `ntn_`)
5. **CRITICAL**: Share pages/databases with your integration:
   - Open the page in Notion
   - Click **Share** → **Invite**
   - Search for your integration name and invite it

Without sharing, you'll get `object_not_found` errors.

## Usage

### Writing Scripts

**Always write Notion scripts to files** rather than using inline `node -e "..."` evaluation. Inline evaluation has shell escaping issues with special characters like `!` in JavaScript code.

```javascript
// scripts/notion-task.js
const { Client } = require('@notionhq/client');

const notion = new Client({ auth: process.env.NOTION_API_KEY });

async function main() {
  // Your Notion code here
  const results = await notion.search({
    filter: { property: 'object', value: 'page' },
    page_size: 10
  });
  console.log(results);
}

main().catch(console.error);
```

Then run:
```bash
node scripts/notion-task.js
```

## ⚠️ Critical Gotchas (SDK v5.6.0)

### 1. `databases.query()` DOES NOT EXIST

This is the most common mistake. **The method simply doesn't exist** in SDK v5.6.0+:

```javascript
// ❌ WRONG - this will throw "is not a function":
await notion.databases.query({ database_id: '...' })

// ✅ CORRECT - use search instead:
const results = await notion.search({
  filter: { property: 'object', value: 'page' },
  page_size: 50
});
```

### 2. `databases.retrieve()` Returns Limited Data

The `properties` field is NOT included in the response:

```javascript
const db = await notion.databases.retrieve({ database_id: '...' });
console.log(db.title);      // ✅ Works
console.log(db.properties); // ❌ UNDEFINED - don't use!
```

### 3. Shell Escaping with Inline Evaluation

**Don't do this:**
```bash
# This will fail - ! gets interpreted by bash
node -e "if (!dbId) { ... }"
```

**Do this instead:**
```bash
# Write to a file and execute
node your-script.js
```

### 4. object_not_found Errors

The page/database isn't shared with your integration. Go to Notion → Share → Invite your integration.

## File Structure

```
.claude/skills/notion/
├── README.md      # This file - setup and usage guide
└── SKILL.md       # Claude Code skill definition with API reference
```

## Testing Your Setup

Use the provided test script:

```bash
node examples/test-connection.js
```

Or create your own:

```javascript
// scripts/test-notion.js
const { Client } = require('@notionhq/client');

const notion = new Client({ auth: process.env.NOTION_API_KEY });

async function test() {
  console.log('Testing Notion API connection...\n');

  try {
    const results = await notion.search({
      filter: { property: 'object', value: 'page' },
      sort: { direction: 'descending', timestamp: 'last_edited_time' },
      page_size: 5
    });

    console.log('API connection successful!');
    console.log('Found', results.results.length, 'pages');
  } catch (error) {
    console.error('Error:', error.message);
    if (error.code === 'unauthorized') {
      console.log('Check your NOTION_API_KEY environment variable');
    }
  }
}

test();
```

## Resources

- [Notion API Documentation](https://developers.notion.com)
- [Notion JS SDK](https://github.com/makenotion/notion-sdk-js)
- [Notion Python SDK](https://github.com/ramnes/notion-sdk-py)
- [Original FastMCP Skill](https://fastmcp.me/Skills/Details/334/notion)

## License

MIT
