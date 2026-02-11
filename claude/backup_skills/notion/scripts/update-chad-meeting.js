const { Client } = require("@notionhq/client");

const notion = new Client({ auth: process.env.NOTION_API_KEY });
const pageId = "2e2d73a0-f0a3-80c9-a7b4-ca3ec373a60e";

async function updatePage() {
  const blocks = [
    // Header
    {
      object: "block",
      type: "heading_1",
      heading_1: {
        rich_text: [{ type: "text", text: { content: "Meeting Prep: Chad Moutray" } }]
      }
    },
    {
      object: "block",
      type: "paragraph",
      paragraph: {
        rich_text: [
          { type: "text", text: { content: "Date: January 8, 2026 | Intro via: Radha (IMPLAN connection)" }, annotations: { italic: true } }
        ]
      }
    },
    {
      object: "block",
      type: "divider",
      divider: {}
    },
    // About Chad
    {
      object: "block",
      type: "heading_2",
      heading_2: {
        rich_text: [{ type: "text", text: { content: "About Chad Moutray" } }]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [
          { type: "text", text: { content: "Senior Economist" }, annotations: { bold: true } },
          { type: "text", text: { content: " at " } },
          { type: "text", text: { content: "National Restaurant Association" }, annotations: { bold: true } }
        ]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [{ type: "text", text: { content: "Certified Business Economist (NABE, 2015)" } }]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [{ type: "text", text: { content: "13K+ LinkedIn followers - influential voice in restaurant economics" } }]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [{ type: "text", text: { content: "Education: Southern Illinois University, Carbondale" } }]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [{ type: "text", text: { content: "~10 peer-reviewed publications via SBA Office of Advocacy" } }]
      }
    },
    // Expertise
    {
      object: "block",
      type: "heading_3",
      heading_3: {
        rich_text: [{ type: "text", text: { content: "His Expertise" } }]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [{ type: "text", text: { content: "Restaurant & hospitality labor market analysis (JOLTS data, job openings, turnover)" } }]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [{ type: "text", text: { content: "Small business economics & entrepreneurship" } }]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [{ type: "text", text: { content: "Franchise economics" } }]
      }
    },
    {
      object: "block",
      type: "divider",
      divider: {}
    },
    // Zone Pitch
    {
      object: "block",
      type: "heading_2",
      heading_2: {
        rich_text: [{ type: "text", text: { content: "Zone - What We're Building" } }]
      }
    },
    {
      object: "block",
      type: "callout",
      callout: {
        rich_text: [
          { type: "text", text: { content: "Vision AI for Restaurant Operations" }, annotations: { bold: true } },
          { type: "text", text: { content: " - Not just LLMs, but physical AI that sees and understands real-world operations in real-time." } }
        ],
        icon: { emoji: "🎯" }
      }
    },
    {
      object: "block",
      type: "heading_3",
      heading_3: {
        rich_text: [{ type: "text", text: { content: "Technical Differentiator (1-2 lines for Chad)" } }]
      }
    },
    {
      object: "block",
      type: "quote",
      quote: {
        rich_text: [{ type: "text", text: { content: "\"We're building computer vision + physical AI that understands restaurant operations spatially and temporally - tracking kitchen flow, staff efficiency, and compliance in real-time. This is beyond chatbots; it's AI that sees and acts in the physical world.\"" } }]
      }
    },
    {
      object: "block",
      type: "heading_3",
      heading_3: {
        rich_text: [{ type: "text", text: { content: "Current Traction" } }]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [
          { type: "text", text: { content: "Pilot customer: Simply South" }, annotations: { bold: true } },
          { type: "text", text: { content: " - South Indian restaurant chain (Owner: Vinoz)" } }
        ]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [{ type: "text", text: { content: "Use cases: Kitchen monitoring, customer flow, staff efficiency, health & safety compliance" } }]
      }
    },
    {
      object: "block",
      type: "divider",
      divider: {}
    },
    // Meeting Goals
    {
      object: "block",
      type: "heading_2",
      heading_2: {
        rich_text: [{ type: "text", text: { content: "Meeting Goals" } }]
      }
    },
    {
      object: "block",
      type: "numbered_list_item",
      numbered_list_item: {
        rich_text: [
          { type: "text", text: { content: "Learn: " }, annotations: { bold: true } },
          { type: "text", text: { content: "Biggest operational challenges in restaurant industry today" } }
        ]
      }
    },
    {
      object: "block",
      type: "numbered_list_item",
      numbered_list_item: {
        rich_text: [
          { type: "text", text: { content: "Learn: " }, annotations: { bold: true } },
          { type: "text", text: { content: "Where are restaurants trying to adopt technology? What's working/not working?" } }
        ]
      }
    },
    {
      object: "block",
      type: "numbered_list_item",
      numbered_list_item: {
        rich_text: [
          { type: "text", text: { content: "Ask: " }, annotations: { bold: true } },
          { type: "text", text: { content: "Introductions to restaurant chain owners (his network/friends in the industry)" } }
        ]
      }
    },
    {
      object: "block",
      type: "divider",
      divider: {}
    },
    // Questions to Ask
    {
      object: "block",
      type: "heading_2",
      heading_2: {
        rich_text: [{ type: "text", text: { content: "Questions to Ask Chad" } }]
      }
    },
    {
      object: "block",
      type: "heading_3",
      heading_3: {
        rich_text: [{ type: "text", text: { content: "Operations & Challenges" } }]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [{ type: "text", text: { content: "\"From your data, what are the biggest operational pain points for restaurant chains right now?\"" } }]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [{ type: "text", text: { content: "\"Labor turnover is huge - what's driving it beyond wages? Is it operational inefficiency?\"" } }]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [{ type: "text", text: { content: "\"What metrics do restaurant operators obsess over that outsiders might not know about?\"" } }]
      }
    },
    {
      object: "block",
      type: "heading_3",
      heading_3: {
        rich_text: [{ type: "text", text: { content: "Technology Adoption" } }]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [{ type: "text", text: { content: "\"Where are chains investing in technology right now? What's getting budget?\"" } }]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [{ type: "text", text: { content: "\"What tech solutions have you seen fail in restaurants? Why?\"" } }]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [{ type: "text", text: { content: "\"How receptive are franchise operators vs corporate-owned locations to new tech?\"" } }]
      }
    },
    {
      object: "block",
      type: "heading_3",
      heading_3: {
        rich_text: [{ type: "text", text: { content: "Network & Intros" } }]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [{ type: "text", text: { content: "\"We're looking to work with more restaurant chains - would you be open to connecting us with operators in your network who might benefit from vision AI?\"" } }]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [{ type: "text", text: { content: "\"Any upcoming NRA events where we could demo to restaurant operators?\"" } }]
      }
    },
    {
      object: "block",
      type: "divider",
      divider: {}
    },
    // Radha's Tips
    {
      object: "block",
      type: "heading_2",
      heading_2: {
        rich_text: [{ type: "text", text: { content: "Radha's Tips" } }]
      }
    },
    {
      object: "block",
      type: "callout",
      callout: {
        rich_text: [
          { type: "text", text: { content: "✓ He's a nice guy - be polite but energetic\n" } },
          { type: "text", text: { content: "✓ Show technical prowess - emphasize this is beyond LLMs (physical/vision AI)\n" } },
          { type: "text", text: { content: "✓ He's unofficially supporting us - already friendly" } }
        ],
        icon: { emoji: "💡" }
      }
    },
    {
      object: "block",
      type: "divider",
      divider: {}
    },
    // Context
    {
      object: "block",
      type: "heading_2",
      heading_2: {
        rich_text: [{ type: "text", text: { content: "Context to Know" } }]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [
          { type: "text", text: { content: "NRA Connection: " }, annotations: { bold: true } },
          { type: "text", text: { content: "National Restaurant Association represents 500K+ restaurant businesses" } }
        ]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [
          { type: "text", text: { content: "Recent data point: " }, annotations: { bold: true } },
          { type: "text", text: { content: "Restaurant job openings dropped from 985K to 837K (Oct→Nov) - labor market shifting" } }
        ]
      }
    },
    {
      object: "block",
      type: "bulleted_list_item",
      bulleted_list_item: {
        rich_text: [
          { type: "text", text: { content: "IMPLAN connection: " }, annotations: { bold: true } },
          { type: "text", text: { content: "Radha worked there, Chad is continuing her work - he knows her quality" } }
        ]
      }
    },
    {
      object: "block",
      type: "divider",
      divider: {}
    },
    // Follow-up
    {
      object: "block",
      type: "heading_2",
      heading_2: {
        rich_text: [{ type: "text", text: { content: "Follow-Up Actions (Post-Meeting)" } }]
      }
    },
    {
      object: "block",
      type: "to_do",
      to_do: {
        rich_text: [{ type: "text", text: { content: "Send thank you note + Zone deck" } }],
        checked: false
      }
    },
    {
      object: "block",
      type: "to_do",
      to_do: {
        rich_text: [{ type: "text", text: { content: "Follow up on any intro requests" } }],
        checked: false
      }
    },
    {
      object: "block",
      type: "to_do",
      to_do: {
        rich_text: [{ type: "text", text: { content: "Add meeting notes below" } }],
        checked: false
      }
    },
    {
      object: "block",
      type: "divider",
      divider: {}
    },
    {
      object: "block",
      type: "heading_2",
      heading_2: {
        rich_text: [{ type: "text", text: { content: "Meeting Notes" } }]
      }
    },
    {
      object: "block",
      type: "paragraph",
      paragraph: {
        rich_text: [{ type: "text", text: { content: "(Add notes during/after the call)" }, annotations: { italic: true, color: "gray" } }]
      }
    }
  ];

  try {
    const response = await notion.blocks.children.append({
      block_id: pageId,
      children: blocks
    });
    console.log("Successfully updated page with meeting prep one-pager!");
    console.log(`Added ${response.results.length} blocks`);
  } catch (error) {
    console.error("Error:", error.message);
    if (error.body) console.error(error.body);
  }
}

updatePage();
