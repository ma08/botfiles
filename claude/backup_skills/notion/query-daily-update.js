/**
 * Query daily updates database for a specific date
 * Usage: node query-daily-update.js [YYYY-MM-DD]
 */
const { Client } = require('@notionhq/client');

const notion = new Client({ auth: process.env.NOTION_API_KEY });
const DATABASE_ID = '2b4d73a0f0a380b2beb7fd5646e75f32';

async function queryDailyUpdate(targetDate) {
  // Search for pages, then filter by database parent and date
  const results = await notion.search({
    filter: { property: 'object', value: 'page' },
    sort: { direction: 'descending', timestamp: 'last_edited_time' },
    page_size: 50
  });

  // Filter to pages from our database
  const dbPages = results.results.filter(page =>
    page.parent?.type === 'database_id' &&
    page.parent.database_id.replace(/-/g, '') === DATABASE_ID.replace(/-/g, '')
  );

  console.log(`Found ${dbPages.length} pages in daily updates database\n`);

  // Find pages matching the target date
  for (const page of dbPages) {
    // Get the Date property
    const dateProperty = page.properties?.Date;
    let pageDate = null;

    if (dateProperty?.type === 'date' && dateProperty.date?.start) {
      pageDate = dateProperty.date.start;
    }

    // Get title
    let title = 'Untitled';
    for (const val of Object.values(page.properties || {})) {
      if (val.type === 'title' && val.title && val.title[0]) {
        title = val.title[0].plain_text;
        break;
      }
    }

    // Check if this matches our target date
    if (pageDate === targetDate) {
      console.log('=== FOUND TODAY\'S ENTRY ===');
      console.log('Title:', title);
      console.log('Date:', pageDate);
      console.log('Page ID:', page.id);
      console.log('URL:', page.url);
      console.log('\n--- Page Content ---\n');

      // Fetch the page content
      const blocks = await notion.blocks.children.list({ block_id: page.id });
      printBlocks(blocks.results);
      return;
    }
  }

  // If no exact match, show recent entries
  console.log(`No entry found for ${targetDate}. Recent entries:`);
  for (const page of dbPages.slice(0, 5)) {
    const dateProperty = page.properties?.Date;
    let pageDate = dateProperty?.date?.start || 'No date';

    let title = 'Untitled';
    for (const val of Object.values(page.properties || {})) {
      if (val.type === 'title' && val.title && val.title[0]) {
        title = val.title[0].plain_text;
        break;
      }
    }
    console.log(`- ${title} (${pageDate})`);
    console.log(`  ID: ${page.id}`);
  }
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
    } else if (type === 'bulleted_list_item' || type === 'numbered_list_item') {
      const text = content?.rich_text?.map(t => t.plain_text).join('') || '';
      console.log(`${prefix}- ${text}`);
    } else if (type === 'to_do') {
      const text = content?.rich_text?.map(t => t.plain_text).join('') || '';
      const checked = content?.checked ? '[x]' : '[ ]';
      console.log(`${prefix}${checked} ${text}`);
    } else if (type === 'divider') {
      console.log(`${prefix}---`);
    }
  }
}

const targetDate = process.argv[2] || new Date().toISOString().split('T')[0];
queryDailyUpdate(targetDate).catch(console.error);
