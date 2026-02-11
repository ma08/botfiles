/**
 * Read a daily update page with full details
 */
const { Client } = require('@notionhq/client');

const notion = new Client({ auth: process.env.NOTION_API_KEY });

async function readPage(pageId) {
  // Get page metadata
  const page = await notion.pages.retrieve({ page_id: pageId });

  console.log('=== Page Properties ===');
  for (const [key, val] of Object.entries(page.properties || {})) {
    if (val.type === 'title' && val.title?.[0]) {
      console.log(`${key}: ${val.title[0].plain_text}`);
    } else if (val.type === 'date' && val.date) {
      console.log(`${key}: ${val.date.start}`);
    } else if (val.type === 'rich_text' && val.rich_text?.[0]) {
      console.log(`${key}: ${val.rich_text[0].plain_text}`);
    } else if (val.type === 'select' && val.select) {
      console.log(`${key}: ${val.select.name}`);
    }
  }

  console.log('\nURL:', page.url);
  console.log('\n=== Page Content ===\n');

  // Get page content
  const blocks = await notion.blocks.children.list({ block_id: pageId });
  printBlocks(blocks.results);
}

function printBlocks(blocks, indent = 0) {
  const prefix = '  '.repeat(indent);
  for (const block of blocks) {
    const type = block.type;
    const content = block[type];

    if (type === 'heading_1' || type === 'heading_2' || type === 'heading_3') {
      const text = content?.rich_text?.map(t => t.plain_text).join('') || '';
      const level = type === 'heading_1' ? '#' : type === 'heading_2' ? '##' : '###';
      console.log(`${prefix}${level} ${text}`);
    } else if (type === 'paragraph') {
      const text = content?.rich_text?.map(t => t.plain_text).join('') || '';
      if (text) console.log(`${prefix}${text}`);
      else console.log('');
    } else if (type === 'bulleted_list_item' || type === 'numbered_list_item') {
      const text = content?.rich_text?.map(t => t.plain_text).join('') || '';
      console.log(`${prefix}- ${text}`);
    } else if (type === 'to_do') {
      const text = content?.rich_text?.map(t => t.plain_text).join('') || '';
      const checked = content?.checked ? '[x]' : '[ ]';
      console.log(`${prefix}${checked} ${text}`);
    } else if (type === 'divider') {
      console.log(`${prefix}---`);
    } else if (type === 'toggle') {
      const text = content?.rich_text?.map(t => t.plain_text).join('') || '';
      console.log(`${prefix}▸ ${text}`);
    }
  }
}

const pageId = process.argv[2];
if (!pageId) {
  console.error('Usage: node read-daily-update.js PAGE_ID');
  process.exit(1);
}
readPage(pageId).catch(console.error);
