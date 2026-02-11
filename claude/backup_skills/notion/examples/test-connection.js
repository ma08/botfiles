/**
 * Test Notion API connection and configuration
 *
 * Usage: node examples/test-connection.js
 */
const { Client } = require('@notionhq/client');

const notion = new Client({ auth: process.env.NOTION_API_KEY });

async function testConnection() {
  console.log('Testing Notion API connection...\n');

  // Check API key is set
  if (process.env.NOTION_API_KEY === undefined) {
    console.log('ERROR: NOTION_API_KEY not set in environment');
    process.exit(1);
  }

  // Test basic API access
  try {
    const results = await notion.search({
      filter: { property: 'object', value: 'page' },
      sort: { direction: 'descending', timestamp: 'last_edited_time' },
      page_size: 5
    });

    console.log('API connection: OK');
    console.log('Found', results.results.length, 'recent pages:\n');

    for (const page of results.results) {
      let title = 'Untitled';
      for (const val of Object.values(page.properties || {})) {
        if (val.type === 'title' && val.title && val.title[0]) {
          title = val.title[0].plain_text;
          break;
        }
      }
      console.log('-', title);
    }
  } catch (error) {
    console.log('API connection: FAILED');
    console.log('Error:', error.message);
    if (error.code === 'unauthorized') {
      console.log('Your API key may be invalid. Check NOTION_API_KEY environment variable');
    }
    process.exit(1);
  }

  // Test database access if configured
  console.log('\n--- Database Access ---');
  const dbId = process.env.NOTION_DATABASE_ID || process.env.NOTION_UPDATES_DB_ID;

  if (dbId === undefined) {
    console.log('No database ID configured (NOTION_DATABASE_ID or NOTION_UPDATES_DB_ID)');
    console.log('Skipping database test');
    return;
  }

  try {
    const db = await notion.databases.retrieve({ database_id: dbId });
    let dbTitle = 'Untitled';
    if (db.title && db.title[0]) {
      dbTitle = db.title[0].plain_text;
    }
    console.log('Database access: OK');
    console.log('Database name:', dbTitle);
  } catch (error) {
    console.log('Database access: FAILED');
    console.log('Error:', error.code || error.message);
    if (error.code === 'object_not_found') {
      console.log('The database is not shared with your integration.');
      console.log('Go to Notion > Share > Invite your integration');
    }
  }

  console.log('\nAll tests passed.');
}

testConnection().catch(console.error);
