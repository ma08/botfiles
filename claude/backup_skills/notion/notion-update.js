const { Client } = require('@notionhq/client');

const notion = new Client({ auth: process.env.NOTION_API_KEY });

async function appendContent() {
  const pageId = '2e2d73a0f0a3810c890ee3d4a9550a67';

  // Content to append - ZonEye work today
  const blocks = [
    {
      object: 'block',
      type: 'to_do',
      to_do: {
        rich_text: [{ type: 'text', text: { content: 'ZonEye: Config hot-reload via Redis pub/sub (GitHub Issue #2) - eliminates container restarts' } }],
        checked: true
      }
    },
    {
      object: 'block',
      type: 'to_do',
      to_do: {
        rich_text: [{ type: 'text', text: { content: 'ZonEye: Fix save_zones to trigger hot-reload while video is playing' } }],
        checked: true
      }
    },
    {
      object: 'block',
      type: 'to_do',
      to_do: {
        rich_text: [{ type: 'text', text: { content: 'ZonEye: Updated AGENTS.md for Codex with correct conda path (/anaconda/)' } }],
        checked: true
      }
    },
    {
      object: 'block',
      type: 'heading_3',
      heading_3: {
        rich_text: [{ type: 'text', text: { content: 'ZonEye Resolution Notes' } }]
      }
    },
    {
      object: 'block',
      type: 'bulleted_list_item',
      bulleted_list_item: {
        rich_text: [{ type: 'text', text: { content: 'Low-res videos (320x240) fail detection - 4x upscaling makes frames too blurry for PeopleNet' } }]
      }
    },
    {
      object: 'block',
      type: 'bulleted_list_item',
      bulleted_list_item: {
        rich_text: [{ type: 'text', text: { content: 'Videos 920x680+ work fine (~1.4x upscaling preserves enough detail)' } }]
      }
    },
    {
      object: 'block',
      type: 'bulleted_list_item',
      bulleted_list_item: {
        rich_text: [{ type: 'text', text: { content: 'Zone coordinates are in 1280x720 space (Savant processing resolution) - no scaling bug' } }]
      }
    }
  ];

  try {
    const response = await notion.blocks.children.append({
      block_id: pageId,
      children: blocks
    });
    console.log('Successfully appended ZonEye updates');
    console.log('Added', response.results.length, 'blocks');
  } catch (error) {
    console.error('Error:', error.message);
  }
}

appendContent();
