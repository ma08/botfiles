const { Client } = require('@notionhq/client');

const notion = new Client({ auth: process.env.NOTION_API_KEY });

const databaseId = '2b4d73a0-f0a3-80b2-beb7-fd5646e75f32';

async function createDaily() {
  // Create the page
  const page = await notion.pages.create({
    parent: { database_id: databaseId },
    properties: {
      'Update Title': {
        title: [{ text: { content: 'Daily Update' } }]
      },
      'Date': {
        date: { start: '2026-01-08' }
      },
      'Type': {
        select: { name: 'Daily Update' }
      }
    },
    children: [
      {
        object: 'block',
        type: 'heading_1',
        heading_1: {
          rich_text: [{ type: 'text', text: { content: 'Plan for today' } }]
        }
      },
      {
        object: 'block',
        type: 'to_do',
        to_do: {
          rich_text: [{ type: 'text', text: { content: 'Polish good demo for video - alerts for restaurant usecase' } }],
          checked: false
        }
      },
      {
        object: 'block',
        type: 'to_do',
        to_do: {
          rich_text: [{ type: 'text', text: { content: 'Zone Android App + iOS Bugfixes' } }],
          checked: false
        }
      },
      {
        object: 'block',
        type: 'to_do',
        to_do: {
          rich_text: [{ type: 'text', text: { content: 'Post on LinkedIn + Schedule finallayer when I can' } }],
          checked: false
        }
      },
      {
        object: 'block',
        type: 'to_do',
        to_do: {
          rich_text: [{ type: 'text', text: { content: 'Publish work we have done (like takeaways from ladduu whatsapp etc.)' } }],
          checked: false
        }
      },
      {
        object: 'block',
        type: 'to_do',
        to_do: {
          rich_text: [{ type: 'text', text: { content: 'Push personal OS to a github repo' } }],
          checked: false
        }
      },
      {
        object: 'block',
        type: 'heading_1',
        heading_1: {
          rich_text: [{ type: 'text', text: { content: 'What did I do today' } }]
        }
      },
      {
        object: 'block',
        type: 'to_do',
        to_do: {
          rich_text: [{ type: 'text', text: { content: 'Finished reach out in AI Operations - Contacts list (11 contacts via email/LinkedIn)' } }],
          checked: true
        }
      },
      {
        object: 'block',
        type: 'to_do',
        to_do: {
          rich_text: [{ type: 'text', text: { content: 'Group outreach for pharma vertical (IIT KGP Bay Area, ODF, SNR Hackathon, Friends of Next Play)' } }],
          checked: true
        }
      },
      {
        object: 'block',
        type: 'heading_1',
        heading_1: {
          rich_text: [{ type: 'text', text: { content: 'Notes' } }]
        }
      },
      {
        object: 'block',
        type: 'heading_1',
        heading_1: {
          rich_text: [{ type: 'text', text: { content: 'Next Steps' } }]
        }
      }
    ]
  });

  console.log('Jan 8 daily update created!');
  console.log('URL:', page.url);
}

createDaily().catch(console.error);
