/**
 * Read content (blocks) from a Notion page
 *
 * Usage: node examples/read-page.js <page_id>
 * Example: node examples/read-page.js abc123-def456
 */
const { Client } = require('@notionhq/client');

const notion = new Client({ auth: process.env.NOTION_API_KEY });

async function readPage(pageId) {
  if (pageId.length === 0) {
    console.log('Usage: node read-page.js <page_id>');
    process.exit(1);
  }

  // Get page metadata
  const page = await notion.pages.retrieve({ page_id: pageId });

  let title = 'Untitled';
  for (const val of Object.values(page.properties || {})) {
    if (val.type === 'title' && val.title && val.title[0]) {
      title = val.title[0].plain_text;
      break;
    }
  }

  console.log('Page:', title);
  console.log('URL:', page.url);
  console.log('Last edited:', page.last_edited_time);
  console.log('\n--- Content ---\n');

  // Get page blocks
  const blocks = await notion.blocks.children.list({
    block_id: pageId,
    page_size: 100
  });

  for (const block of blocks.results) {
    const type = block.type;
    const content = block[type];

    if (type === 'heading_1') {
      const text = extractText(content.rich_text);
      console.log('#', text);
    } else if (type === 'heading_2') {
      const text = extractText(content.rich_text);
      console.log('##', text);
    } else if (type === 'heading_3') {
      const text = extractText(content.rich_text);
      console.log('###', text);
    } else if (type === 'paragraph') {
      const text = extractText(content.rich_text);
      if (text) console.log(text);
    } else if (type === 'bulleted_list_item') {
      const text = extractText(content.rich_text);
      console.log('*', text);
    } else if (type === 'numbered_list_item') {
      const text = extractText(content.rich_text);
      console.log('1.', text);
    } else if (type === 'to_do') {
      const text = extractText(content.rich_text);
      const checkbox = content.checked ? '[x]' : '[ ]';
      console.log(checkbox, text);
    } else if (type === 'divider') {
      console.log('---');
    } else if (type === 'code') {
      const text = extractText(content.rich_text);
      console.log('```' + (content.language || ''));
      console.log(text);
      console.log('```');
    }
  }
}

function extractText(richText) {
  if (richText && Array.isArray(richText)) {
    return richText.map(t => t.plain_text).join('');
  }
  return '';
}

const pageId = process.argv[2] || '';
readPage(pageId).catch(console.error);
