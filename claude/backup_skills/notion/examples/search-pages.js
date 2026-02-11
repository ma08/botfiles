/**
 * Search for pages in Notion workspace
 *
 * Usage: node examples/search-pages.js [query]
 * Example: node examples/search-pages.js "Meeting Notes"
 */
const { Client } = require('@notionhq/client');

const notion = new Client({ auth: process.env.NOTION_API_KEY });

async function searchPages(query) {
  const params = {
    filter: { property: 'object', value: 'page' },
    sort: { direction: 'descending', timestamp: 'last_edited_time' },
    page_size: 20
  };

  if (query) {
    params.query = query;
  }

  const results = await notion.search(params);

  console.log('Found', results.results.length, 'pages:\n');

  for (const page of results.results) {
    let title = 'Untitled';
    for (const val of Object.values(page.properties || {})) {
      if (val.type === 'title' && val.title && val.title[0]) {
        title = val.title[0].plain_text;
        break;
      }
    }
    console.log('-', title);
    console.log('  ID:', page.id);
    console.log('  URL:', page.url);
    console.log();
  }
}

const query = process.argv[2];
searchPages(query).catch(console.error);
