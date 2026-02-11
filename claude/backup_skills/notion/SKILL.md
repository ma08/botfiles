---
name: Notion
description: Notion workspace integration. Use when user wants to read/write Notion pages, search databases, create tasks, or sync content with Notion.
source: base
---

# Notion Skill

Integrate with Notion workspaces to read and write content.

## When to Use

- User wants to read or search Notion pages
- User wants to create or update pages
- User wants to query databases
- User wants to sync content to/from Notion
- User wants to create tasks or notes in Notion
- User asks about their Notion workspace

## Critical Gotchas (SDK v5.6.0)

1. The databases.query() method DOES NOT EXIST in this SDK version. Use notion.search() instead.

2. The databases.retrieve() method returns only basic metadata (title, url, timestamps). The properties field is undefined.

3. Always write scripts to files. Never use inline node -e evaluation because shell metacharacters cause errors.

4. Pages must be shared with your integration or you get object_not_found errors.

## Setup Requirements

Environment variables (assumed already available due to the start session hook):
- NOTION_API_KEY: Your integration token (starts with ntn_)
- NOTION_DATABASE_ID or NOTION_UPDATES_DB_ID: Optional database ID

Node packages required:
- @notionhq/client (official SDK)

Install with: npm install @notionhq/client

## Example Scripts

All examples are in the examples/ subdirectory. Run from the skill directory.

Search pages:
  node examples/search-pages.js
  node examples/search-pages.js "query text"

Read page content:
  node examples/read-page.js PAGE_ID

Create a page:
  node examples/create-page.js DATABASE_ID "Page Title"

Append content to page:
  node examples/append-content.js PAGE_ID "Content text"

Test connection:
  node examples/test-connection.js

## SDK Methods Available

Search (primary query method):
  notion.search(params) - Search pages and databases

Pages:
  notion.pages.retrieve(params) - Get page metadata
  notion.pages.create(params) - Create new page
  notion.pages.update(params) - Update page properties

Blocks:
  notion.blocks.children.list(params) - Read page content
  notion.blocks.children.append(params) - Add content to page
  notion.blocks.retrieve(params) - Get single block
  notion.blocks.update(params) - Update a block
  notion.blocks.delete(params) - Delete a block

Databases:
  notion.databases.retrieve(params) - Get database metadata (limited)
  notion.databases.create(params) - Create database
  notion.databases.update(params) - Update database

## Block Types

Headings: heading_1, heading_2, heading_3
Text: paragraph
Lists: bulleted_list_item, numbered_list_item
Tasks: to_do (with checked property)
Code: code (with language property)
Other: divider, quote, callout

## Property Types

title - Page title (required)
rich_text - Text content
number - Numeric value
select - Single option
multi_select - Multiple options
date - Date with optional end
checkbox - Boolean
url - URL string
email - Email address

## Troubleshooting

object_not_found error:
  Share the page/database with your integration in Notion settings

Empty search results:
  No pages are shared with your integration

unauthorized error:
  Check that NOTION_API_KEY is set in your shell environment

## Resources

Notion API Docs: https://developers.notion.com
JS SDK: https://github.com/makenotion/notion-sdk-js
Python SDK: https://github.com/ramnes/notion-sdk-py
