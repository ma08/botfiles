const { Client } = require('@notionhq/client');

const notion = new Client({ auth: process.env.NOTION_API_KEY });

const pageId = '2e1d73a0-f0a3-8162-b517-cc9830eb3d77';

async function updateDaily() {
  // First, get all existing blocks
  const existingBlocks = await notion.blocks.children.list({ block_id: pageId });

  // Delete all existing blocks
  for (const block of existingBlocks.results) {
    await notion.blocks.delete({ block_id: block.id });
  }

  // Add new content
  const newContent = [
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
        rich_text: [{ type: 'text', text: { content: 'Source version Personal OS' } }],
        checked: true
      }
    },
    {
      object: 'block',
      type: 'to_do',
      to_do: {
        rich_text: [{ type: 'text', text: { content: 'Get notion-skill only use in personal OS working (done via botfiles repo)' } }],
        checked: true
      }
    },
    {
      object: 'block',
      type: 'to_do',
      to_do: {
        rich_text: [{ type: 'text', text: { content: 'Codify ralph in personal OS' } }],
        checked: true
      }
    },
    {
      object: 'block',
      type: 'to_do',
      to_do: {
        rich_text: [{ type: 'text', text: { content: 'Implemented visual zone alerts in zoneye demo (using codified ralph)' } }],
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
    },
    {
      object: 'block',
      type: 'bulleted_list_item',
      bulleted_list_item: {
        rich_text: [{ type: 'text', text: { content: 'Finish reach out in AI Operations - Contacts list' } }]
      }
    },
    {
      object: 'block',
      type: 'bulleted_list_item',
      bulleted_list_item: {
        rich_text: [{ type: 'text', text: { content: 'Polish good demo for video - alerts for restaurant usecase' } }]
      }
    },
    {
      object: 'block',
      type: 'bulleted_list_item',
      bulleted_list_item: {
        rich_text: [{ type: 'text', text: { content: 'Zone Android App + iOS Bugfixes' } }]
      }
    },
    {
      object: 'block',
      type: 'bulleted_list_item',
      bulleted_list_item: {
        rich_text: [{ type: 'text', text: { content: 'Post on LinkedIn + Schedule finallayer when I can' } }]
      }
    },
    {
      object: 'block',
      type: 'bulleted_list_item',
      bulleted_list_item: {
        rich_text: [{ type: 'text', text: { content: 'Publish work we have done (like takeaways from ladduu whatsapp etc.)' } }]
      }
    }
  ];

  await notion.blocks.children.append({
    block_id: pageId,
    children: newContent
  });

  console.log('Daily update updated successfully!');
}

updateDaily().catch(console.error);
