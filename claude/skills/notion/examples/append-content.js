/**
 * Append content blocks to an existing Notion page
 *
 * Usage: node examples/append-content.js <page_id> "Content to add"
 * Example: node examples/append-content.js abc123 "New paragraph text"
 */
const { Client } = require('@notionhq/client');

const notion = new Client({ auth: process.env.NOTION_API_KEY });

async function appendContent(pageId, content) {
  if (pageId === undefined || pageId.length === 0) {
    console.log('Error: No page ID provided');
    console.log('Usage: node append-content.js <page_id> "Content to add"');
    process.exit(1);
  }

  if (content === undefined || content.length === 0) {
    console.log('Error: No content provided');
    console.log('Usage: node append-content.js <page_id> "Content to add"');
    process.exit(1);
  }

  await notion.blocks.children.append({
    block_id: pageId,
    children: [
      {
        object: 'block',
        type: 'paragraph',
        paragraph: {
          rich_text: [{ type: 'text', text: { content: content } }]
        }
      }
    ]
  });

  console.log('Content appended successfully to page:', pageId);
}

// Example: Append a to-do item instead
async function appendTodo(pageId, taskText, checked) {
  await notion.blocks.children.append({
    block_id: pageId,
    children: [
      {
        object: 'block',
        type: 'to_do',
        to_do: {
          rich_text: [{ type: 'text', text: { content: taskText } }],
          checked: checked || false
        }
      }
    ]
  });
  console.log('Todo added:', taskText);
}

// Example: Append a heading
async function appendHeading(pageId, headingText, level) {
  const headingType = 'heading_' + (level || 2);
  const block = {
    object: 'block',
    type: headingType
  };
  block[headingType] = {
    rich_text: [{ type: 'text', text: { content: headingText } }]
  };

  await notion.blocks.children.append({
    block_id: pageId,
    children: [block]
  });
  console.log('Heading added:', headingText);
}

const pageId = process.argv[2];
const content = process.argv[3];
appendContent(pageId, content).catch(console.error);

// Export functions for use as module
module.exports = { appendContent, appendTodo, appendHeading };
