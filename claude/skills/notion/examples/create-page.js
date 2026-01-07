/**
 * Create a new page in a Notion database
 *
 * Usage: node examples/create-page.js <database_id> "Page Title"
 * Example: node examples/create-page.js abc123 "My New Page"
 *
 * Uses NOTION_DATABASE_ID from environment if no database_id provided
 */
const { Client } = require('@notionhq/client');

const notion = new Client({ auth: process.env.NOTION_API_KEY });

async function createPage(databaseId, title) {
  const dbId = databaseId || process.env.NOTION_DATABASE_ID;

  if (dbId === undefined || dbId.length === 0) {
    console.log('Error: No database ID provided');
    console.log('Usage: node create-page.js <database_id> "Page Title"');
    console.log('Or set NOTION_DATABASE_ID environment variable');
    process.exit(1);
  }

  if (title === undefined || title.length === 0) {
    console.log('Error: No title provided');
    console.log('Usage: node create-page.js <database_id> "Page Title"');
    process.exit(1);
  }

  const newPage = await notion.pages.create({
    parent: { database_id: dbId },
    properties: {
      Name: {
        title: [{ text: { content: title } }]
      }
    },
    children: [
      {
        object: 'block',
        type: 'heading_2',
        heading_2: {
          rich_text: [{ type: 'text', text: { content: 'Overview' } }]
        }
      },
      {
        object: 'block',
        type: 'paragraph',
        paragraph: {
          rich_text: [{ type: 'text', text: { content: 'Add content here...' } }]
        }
      }
    ]
  });

  console.log('Page created successfully');
  console.log('ID:', newPage.id);
  console.log('URL:', newPage.url);
}

const databaseId = process.argv[2];
const title = process.argv[3];
createPage(databaseId, title).catch(console.error);
