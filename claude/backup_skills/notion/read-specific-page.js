const { Client } = require('@notionhq/client');
const notion = new Client({ auth: process.env.NOTION_API_KEY });

const pageId = process.argv[2] || '2ead73a0f0a380f5a709d5e4f8cc8338';

function extractText(richText) {
  if (!richText) return '';
  return richText.map(t => t.plain_text).join('');
}

async function getAllContent(pageId) {
  // Get page metadata first
  const page = await notion.pages.retrieve({ page_id: pageId });
  const title = page.properties.title?.title?.[0]?.plain_text || 'Untitled';
  console.log('Page:', title);
  console.log('URL:', page.url);
  console.log('---\n');

  let allBlocks = [];
  let cursor;

  do {
    const response = await notion.blocks.children.list({
      block_id: pageId,
      start_cursor: cursor,
      page_size: 100
    });
    allBlocks = allBlocks.concat(response.results);
    cursor = response.has_more ? response.next_cursor : undefined;
  } while (cursor);

  for (const block of allBlocks) {
    const type = block.type;
    const content = block[type];
    let text = '';

    if (content && content.rich_text) {
      text = extractText(content.rich_text);
    }

    if (type.startsWith('heading')) {
      console.log('---');
      console.log(type.toUpperCase() + ':', text);
    } else if (type === 'paragraph') {
      if (text) console.log(text);
    } else if (type === 'bulleted_list_item' || type === 'numbered_list_item') {
      console.log('• ' + text);
    } else if (type === 'to_do') {
      const checked = content.checked ? '☑' : '☐';
      console.log(checked + ' ' + text);
    } else if (type === 'code') {
      console.log('```' + (content.language || ''));
      console.log(text);
      console.log('```');
    } else if (type === 'divider') {
      console.log('---');
    } else if (type === 'callout') {
      console.log('[CALLOUT] ' + text);
    } else if (type === 'toggle') {
      console.log('[TOGGLE] ' + text);
    }

    // Handle nested blocks
    if (block.has_children && type !== 'child_page') {
      const children = await notion.blocks.children.list({ block_id: block.id });
      for (const child of children.results) {
        const ctype = child.type;
        const ccontent = child[ctype];
        if (ccontent && ccontent.rich_text) {
          console.log('  - ' + extractText(ccontent.rich_text));
        }
      }
    }
  }
}

getAllContent(pageId);
