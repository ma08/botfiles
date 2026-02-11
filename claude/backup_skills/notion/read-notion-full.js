const { Client } = require('@notionhq/client');
const notion = new Client({ auth: process.env.NOTION_API_KEY });

function extractText(richText) {
  if (!richText) return '';
  return richText.map(t => t.plain_text).join('');
}

async function getAllContent(pageId) {
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

    // Show block ID if it's a heading (to find the right section)
    if (type.startsWith('heading')) {
      console.log('---');
      console.log('Block ID:', block.id);
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
    }
  }
}

getAllContent('2e8d73a0f0a381c39785d8e272d47339');
