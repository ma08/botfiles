#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

const TOOL_DIR = process.env.ZONE_CHANNEL_LINKEDIN_TOOL_DIR || process.cwd();
const CHROME_PROFILE =
  process.env.ZONE_CHANNEL_LINKEDIN_CHROME_PROFILE ||
  path.join(process.env.HOME || ".", "pro/lab/zone-channel-ingest/stores/linkedin-sourya/chrome-profile");
const CHROME_BIN = process.env.ZONE_CHANNEL_LINKEDIN_CHROME_BIN || "/usr/bin/google-chrome";

function loadPlaywright() {
  const resolved = require.resolve("playwright", { paths: [TOOL_DIR] });
  return require(resolved);
}

function usage() {
  console.error(`Usage:
  zone-li-extract.cjs health [--quiet] [--headed]
  zone-li-extract.cjs recent [--limit 20] [--open-limit 10] [--max-messages 50] [--output FILE] [--quiet] [--headed]
  zone-li-extract.cjs thread --thread-url URL [--max-messages 50] [--output FILE] [--quiet] [--headed]
  zone-li-extract.cjs thread --profile-url URL [--max-messages 50] [--output FILE] [--quiet] [--headed]
  zone-li-extract.cjs thread --name NAME [--max-messages 50] [--output FILE] [--quiet] [--headed]
  zone-li-extract.cjs profile --thread-url URL [--experience-limit 3] [--output FILE] [--quiet] [--headed]
  zone-li-extract.cjs profile --profile-url URL [--experience-limit 3] [--output FILE] [--quiet] [--headed]
`);
}

function parseArgs(argv) {
  const opts = {
    command: argv[0],
    limit: 20,
    openLimit: 10,
    maxMessages: 50,
    timeoutMs: 30000,
    settleMs: 1500,
    experienceLimit: 3,
    headed: false,
    quiet: false,
    output: null,
    threadUrl: null,
    profileUrl: null,
    name: null,
  };

  for (let i = 1; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = () => {
      i += 1;
      if (i >= argv.length) {
        throw new Error(`Missing value after ${arg}`);
      }
      return argv[i];
    };

    switch (arg) {
      case "--limit":
        opts.limit = Number(next());
        break;
      case "--open-limit":
        opts.openLimit = Number(next());
        break;
      case "--max-messages":
        opts.maxMessages = Number(next());
        break;
      case "--timeout-ms":
        opts.timeoutMs = Number(next());
        break;
      case "--settle-ms":
        opts.settleMs = Number(next());
        break;
      case "--experience-limit":
        opts.experienceLimit = Number(next());
        break;
      case "--profile-url":
        opts.profileUrl = next();
        break;
      case "--thread-url":
        opts.threadUrl = next();
        break;
      case "--name":
        opts.name = next();
        break;
      case "--output":
        opts.output = next();
        break;
      case "--headed":
        opts.headed = true;
        break;
      case "--headless":
        opts.headed = false;
        break;
      case "--quiet":
        opts.quiet = true;
        break;
      case "--help":
      case "-h":
        usage();
        process.exit(0);
        break;
      default:
        throw new Error(`Unknown option: ${arg}`);
    }
  }

  if (!["health", "recent", "thread", "profile"].includes(opts.command)) {
    throw new Error(`Unknown command: ${opts.command || "(missing)"}`);
  }
  if (opts.command === "thread" && !opts.threadUrl && !opts.profileUrl && !opts.name) {
    throw new Error("thread requires --thread-url URL, --profile-url URL, or --name NAME");
  }
  if (opts.command === "profile" && !opts.threadUrl && !opts.profileUrl && !opts.name) {
    throw new Error("profile requires --thread-url URL, --profile-url URL, or --name NAME");
  }
  for (const key of ["limit", "openLimit", "maxMessages", "timeoutMs", "settleMs", "experienceLimit"]) {
    if (!Number.isFinite(opts[key]) || opts[key] < 0) {
      throw new Error(`${key} must be a non-negative number`);
    }
  }
  return opts;
}

function nowIso() {
  return new Date().toISOString();
}

function cleanText(value) {
  return String(value || "")
    .replace(/\u00a0/g, " ")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function compactLines(value, limit = 12) {
  return cleanText(value)
    .split(/\n+/)
    .map((line) => cleanText(line))
    .filter(Boolean)
    .slice(0, limit);
}

function slugify(value) {
  return cleanText(value)
    .toLowerCase()
    .replace(/https?:\/\//g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "linkedin-thread";
}

async function sleep(ms) {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

async function launchWithPage(opts, fn) {
  const { chromium } = loadPlaywright();
  const context = await chromium.launchPersistentContext(CHROME_PROFILE, {
    executablePath: CHROME_BIN,
    headless: !opts.headed,
    viewport: { width: 1365, height: 900 },
    locale: "en-US",
    args: [
      "--disable-dev-shm-usage",
      "--no-first-run",
      "--no-default-browser-check",
      "--disable-background-networking",
    ],
  });

  try {
    const page = context.pages()[0] || (await context.newPage());
    page.setDefaultTimeout(opts.timeoutMs);
    return await fn(page, context);
  } finally {
    await context.close();
  }
}

async function gotoAndSettle(page, url, opts) {
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: opts.timeoutMs });
  await sleep(opts.settleMs);
}

async function getLoginState(page) {
  const title = await page.title().catch(() => "");
  const url = page.url();
  const flags = await page
    .evaluate(() => {
      const hasLoginForm = Boolean(
        document.querySelector('input[name="session_key"], input#username, form[action*="login"]')
      );
      const hasMessagingUi = Boolean(
        document.querySelector(
          'li.msg-conversation-listitem, .msg-conversation-listitem, a[href*="/messaging/thread/"], main[aria-label*="Messaging"], .msg-s-message-list'
        )
      );
      const hasGlobalNav = Boolean(
        document.querySelector("nav.global-nav, .global-nav__me, a[href*='/in/']")
      );
      const hasCheckpointText = /checkpoint|security verification|verify/i.test(
        document.body ? document.body.innerText.slice(0, 2000) : ""
      );
      return { hasLoginForm, hasMessagingUi, hasGlobalNav, hasCheckpointText };
    })
    .catch(() => ({
      hasLoginForm: false,
      hasMessagingUi: false,
      hasGlobalNav: false,
      hasCheckpointText: false,
    }));

  const loginUrl = /\/login|checkpoint|authwall|signup/i.test(url);
  const loginRequired = loginUrl || flags.hasLoginForm || flags.hasCheckpointText;
  const loggedIn = !loginRequired && (flags.hasMessagingUi || flags.hasGlobalNav);
  return {
    loggedIn,
    loginRequired,
    url,
    title,
    hasMessagingUi: flags.hasMessagingUi,
    hasGlobalNav: flags.hasGlobalNav,
    hasCheckpointText: flags.hasCheckpointText,
  };
}

async function collectConversationCards(page, limit) {
  return await page.evaluate((maxItems) => {
    const clean = (value) =>
      String(value || "")
        .replace(/\u00a0/g, " ")
        .replace(/[ \t]+/g, " ")
        .replace(/\n{3,}/g, "\n\n")
        .trim();
    const lines = (value) =>
      clean(value)
        .split(/\n+/)
        .map((line) => clean(line))
        .filter(Boolean);
    const selector =
      'li.msg-conversation-listitem, div.msg-conversation-listitem, [data-control-name="conversation_card"], a[href*="/messaging/thread/"]';
    const rawNodes = Array.from(document.querySelectorAll(selector));
    const cards = [];
    const seen = new Set();

    for (const node of rawNodes) {
      const element = node.closest("li, .msg-conversation-listitem") || node;
      if (seen.has(element)) continue;
      seen.add(element);

      const link =
        (element.matches && element.matches("a") ? element : null) ||
        element.querySelector('a[href*="/messaging/"]');
      const href = link && link.href ? link.href : null;
      const textLines = lines(element.innerText).slice(0, 12);
      if (!href && textLines.length === 0) continue;

      const participant = textLines[0] || null;
      cards.push({
        index: cards.length,
        href,
        participant_names: participant ? [participant] : [],
        preview_lines: textLines,
      });
      if (cards.length >= maxItems) break;
    }
    return cards;
  }, limit);
}

async function extractThreadMessages(page, maxMessages) {
  return await page.evaluate((limit) => {
    const clean = (value) =>
      String(value || "")
        .replace(/\u00a0/g, " ")
        .replace(/[ \t]+/g, " ")
        .replace(/\n{3,}/g, "\n\n")
        .trim();
    const firstText = (root, selectors) => {
      for (const selector of selectors) {
        const found = root.querySelector(selector);
        const text = found ? clean(found.innerText || found.textContent) : "";
        if (text) return text;
      }
      return null;
    };
    const allText = (root, selectors) => {
      const parts = [];
      for (const selector of selectors) {
        for (const found of Array.from(root.querySelectorAll(selector))) {
          const text = clean(found.innerText || found.textContent);
          if (text && !parts.includes(text)) parts.push(text);
        }
      }
      return parts.join("\n");
    };

    const threadTitle = firstText(document, [
      ".msg-entity-lockup__entity-title",
      ".msg-thread__link-to-profile",
      "h2",
      "h1",
    ]);
    const profileUrls = Array.from(document.querySelectorAll('a[href*="/in/"]'))
      .map((anchor) => anchor.href)
      .filter(Boolean)
      .filter((href, index, arr) => arr.indexOf(href) === index)
      .slice(0, 5);

    const eventSelectors = [
      "li.msg-s-message-list__event",
      ".msg-s-message-list__event",
      ".msg-s-event-listitem",
      ".msg-s-message-group",
      "[data-event-urn*='message']",
    ];
    let nodes = Array.from(document.querySelectorAll(eventSelectors.join(",")));
    if (nodes.length === 0) {
      nodes = Array.from(
        document.querySelectorAll(".msg-s-event-listitem__body, .msg-s-message-list__event-message")
      ).map((node) => node.closest("li, .msg-s-event-listitem, .msg-s-message-group") || node);
    }

    const seenNodes = new Set();
    const messages = [];
    for (const node of nodes) {
      if (seenNodes.has(node)) continue;
      seenNodes.add(node);

      const sender = firstText(node, [
        ".msg-s-message-group__name",
        ".msg-s-message-group__profile-link",
        ".msg-s-message-list__name",
        "h3",
        "h4",
      ]);
      const timeNode = node.querySelector("time");
      const timestampText = timeNode
        ? clean(timeNode.getAttribute("datetime") || timeNode.innerText || timeNode.textContent)
        : firstText(node, [
            ".msg-s-message-group__timestamp",
            ".msg-s-message-list__time-heading",
            ".msg-s-event-listitem__time",
          ]);
      const body = allText(node, [
        ".msg-s-event-listitem__body",
        ".msg-s-message-list__event-message",
        ".msg-s-event__content",
        ".msg-s-message-group__message",
        "[class*='message-body']",
      ]);

      if (!body) continue;
      const key = `${sender || ""}|${timestampText || ""}|${body}`;
      if (messages.some((message) => message._key === key)) continue;
      messages.push({
        sender,
        timestamp_text: timestampText,
        body,
        _key: key,
      });
    }

    return {
      thread_title: threadTitle,
      profile_urls: profileUrls,
      messages: messages.slice(Math.max(0, messages.length - limit)).map(({ _key, ...message }) => message),
    };
  }, maxMessages);
}

async function scrollProfile(page, opts) {
  await page.evaluate(async () => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    for (const fraction of [0.25, 0.5, 0.75, 1]) {
      window.scrollTo(0, document.body.scrollHeight * fraction);
      await sleep(450);
    }
    window.scrollTo(0, 0);
  });
  await sleep(opts.settleMs);
}

function canonicalLinkedInUrl(rawUrl) {
  if (!rawUrl) return null;
  try {
    const url = new URL(rawUrl);
    url.search = "";
    url.hash = "";
    return url.toString();
  } catch (_error) {
    return rawUrl;
  }
}

async function extractProfileData(page, opts, source) {
  return await page.evaluate(
    ({ experienceLimit, source }) => {
      const clean = (value) =>
        String(value || "")
          .replace(/\u00a0/g, " ")
          .replace(/[ \t]+/g, " ")
          .replace(/\n{3,}/g, "\n\n")
          .trim();
      const lines = (value) =>
        clean(value)
          .split(/\n+/)
          .map((line) => clean(line))
          .filter(Boolean);
      const uniq = (values) => Array.from(new Set(values.filter(Boolean)));
      const visibleText = (selector) => {
        const node = document.querySelector(selector);
        return node ? clean(node.innerText || node.textContent) : null;
      };
      const allSections = Array.from(document.querySelectorAll("main section")).map((section, index) => ({
        index,
        text: clean(section.innerText || section.textContent),
        lines: lines(section.innerText || section.textContent),
      }));
      const findSection = (label) =>
        allSections.find((section) =>
          section.lines.some((line) => line.toLowerCase() === label.toLowerCase())
        );
      const sectionAfterLabel = (label, maxLines = 20) => {
        const section = findSection(label);
        if (!section) return [];
        const start = section.lines.findIndex((line) => line.toLowerCase() === label.toLowerCase());
        return section.lines
          .slice(start + 1)
          .filter((line) => !/^show all/i.test(line))
          .slice(0, maxLines);
      };

      const topSection = allSections[0] || { lines: [] };
      const name = visibleText("main h1") || topSection.lines[0] || null;
      const topLines = topSection.lines.slice(0, 30);
      const isTopCardNoise = (line) =>
        !line ||
        line === name ||
        line.includes("{:badgeType}") ||
        /^test$/i.test(line) ||
        /^(1st|2nd|3rd|\d+(st|nd|rd)\+?)$/i.test(line) ||
        /^(1st|2nd|3rd|\d+(st|nd|rd)\+?) degree connection$/i.test(line) ||
        /^contact info$/i.test(line) ||
        /^message$/i.test(line) ||
        /^follow$/i.test(line) ||
        /^connect$/i.test(line) ||
        /^more$/i.test(line) ||
        /^\d[\d,]*\+?\s+(followers|connections)$/i.test(line) ||
        /\bmutual connection/i.test(line);
      const headline =
        topLines.find(
          (line) =>
            !isTopCardNoise(line) &&
            !/\b(area|united states|india|canada|kingdom|france|germany|singapore|london|san francisco|new york|bengaluru|bangalore|delhi|mumbai|toronto|seattle|austin|boston|bay area)\b/i.test(
              line
            )
        ) || null;
      const rawLocation =
        topLines.find(
          (line) =>
            !isTopCardNoise(line) &&
            /\b(area|united states|india|canada|kingdom|france|germany|singapore|london|san francisco|new york|bengaluru|bangalore|delhi|mumbai|toronto|seattle|austin|boston|bay area)\b/i.test(
              line
            )
        ) || null;
      const location = rawLocation ? clean(rawLocation.replace(/\s+Contact info$/i, "")) : null;

      const aboutLines = sectionAfterLabel("About", 12);
      const experienceLines = sectionAfterLabel("Experience", 80);
      const companyUrls = uniq(
        Array.from(document.querySelectorAll('main a[href*="/company/"]'))
          .map((anchor) => anchor.href)
          .filter(Boolean)
      ).slice(0, 8);
      const profileUrls = uniq(
        Array.from(document.querySelectorAll('main a[href*="/in/"]'))
          .map((anchor) => anchor.href)
          .filter(Boolean)
      ).slice(0, 8);

      const currentCompanyCandidates = uniq(
        topLines
          .concat(experienceLines.slice(0, 12))
          .filter(
            (line) =>
              !isTopCardNoise(line) &&
              !line.includes("LinkedIn") &&
              !/^(Experience|About|Education)$/i.test(line)
          )
      ).slice(0, 12);

      const recentExperienceLines = experienceLines.slice(0, Math.max(1, experienceLimit) * 8);
      const parseCurrentExperience = (items) => {
        const normalized = items.filter((line) => !/^show all/i.test(line) && !/^…see more$/i.test(line));
        for (let index = 0; index < normalized.length - 1; index += 1) {
          const role = normalized[index];
          const companyLine = normalized[index + 1];
          const dateLine = normalized[index + 2] || null;
          if (!role || !companyLine) continue;
          if (/^(Experience|About|Education)$/i.test(role)) continue;
          if (/^(Present|Current)$/i.test(role)) continue;
          if (/^\d/.test(role)) continue;
          if (/^(Full-time|Contract|Part-time|Self-employed)$/i.test(role)) continue;
          if (dateLine && !/\b(Present|\d{4}|mos|yrs|Less than a year)\b/i.test(dateLine)) continue;
          return {
            role,
            company: clean(companyLine.replace(/\s+·.*$/, "")),
            date_range: dateLine,
          };
        }
        return null;
      };
      const currentExperience = parseCurrentExperience(experienceLines);

      return {
        source: "linkedin",
        extraction_source: source,
        profile_url: window.location.href,
        name,
        headline,
        location,
        current_role: currentExperience ? currentExperience.role : null,
        current_company: currentExperience ? currentExperience.company : null,
        current_date_range: currentExperience ? currentExperience.date_range : null,
        about: aboutLines.join("\n"),
        top_card_lines: topLines,
        current_company_candidates: currentCompanyCandidates,
        recent_experience_lines: recentExperienceLines,
        company_urls: companyUrls,
        profile_urls: profileUrls,
        extracted_section_labels: allSections
          .map((section) => section.lines[0])
          .filter(Boolean)
          .slice(0, 20),
      };
    },
    { experienceLimit: opts.experienceLimit, source }
  );
}

async function openConversationFromCard(page, card, index, opts) {
  if (card.href) {
    await gotoAndSettle(page, new URL(card.href, page.url()).toString(), opts);
    return;
  }
  const locator = page.locator(
    'li.msg-conversation-listitem, div.msg-conversation-listitem, [data-control-name="conversation_card"]'
  );
  await locator.nth(index).click({ timeout: opts.timeoutMs });
  await sleep(opts.settleMs);
}

async function runHealth(opts) {
  return await launchWithPage(opts, async (page) => {
    await gotoAndSettle(page, "https://www.linkedin.com/messaging/", opts);
    const login = await getLoginState(page);
    return {
      ok: true,
      command: "health",
      extracted_at: nowIso(),
      chrome_profile: CHROME_PROFILE,
      chrome_bin: CHROME_BIN,
      headless: !opts.headed,
      ...login,
      notes: login.loggedIn ? [] : ["login_required_or_not_verified"],
    };
  });
}

async function runRecent(opts) {
  return await launchWithPage(opts, async (page) => {
    const notes = [];
    await gotoAndSettle(page, "https://www.linkedin.com/messaging/", opts);
    const login = await getLoginState(page);
    if (!login.loggedIn) {
      return {
        ok: false,
        command: "recent",
        error: "login_required_or_not_verified",
        extracted_at: nowIso(),
        chrome_profile: CHROME_PROFILE,
        headless: !opts.headed,
        ...login,
        conversations: [],
        notes: ["Run zone-li-login from a VM GUI session, complete LinkedIn login, then retry."],
      };
    }

    const cards = await collectConversationCards(page, opts.limit);
    const conversations = [];
    const openCount = Math.min(cards.length, opts.openLimit);
    for (let i = 0; i < openCount; i += 1) {
      const card = cards[i];
      try {
        await openConversationFromCard(page, card, i, opts);
        const thread = await extractThreadMessages(page, opts.maxMessages);
        conversations.push({
          source: "linkedin",
          conversation_id: card.href || `recent-${i}`,
          profile_url: thread.profile_urls ? thread.profile_urls[0] || null : null,
          profile_urls: thread.profile_urls || [],
          participant_names: card.participant_names,
          last_activity_text: null,
          preview_lines: card.preview_lines,
          thread_title: thread.thread_title,
          profile_urls: thread.profile_urls,
          messages: thread.messages,
          extraction_notes: [],
        });
      } catch (error) {
        conversations.push({
          source: "linkedin",
          conversation_id: card.href || `recent-${i}`,
          profile_url: null,
          participant_names: card.participant_names,
          preview_lines: card.preview_lines,
          messages: [],
          extraction_notes: [`open_or_extract_failed: ${error.message}`],
        });
      }
    }

    if (cards.length > openCount) {
      notes.push(`conversation_cards_not_opened=${cards.length - openCount}`);
    }

    return {
      ok: true,
      command: "recent",
      extracted_at: nowIso(),
      chrome_profile: CHROME_PROFILE,
      headless: !opts.headed,
      ...login,
      requested_limit: opts.limit,
      open_limit: opts.openLimit,
      max_messages: opts.maxMessages,
      conversation_card_count: cards.length,
      conversations,
      unopened_cards: cards.slice(openCount),
      notes,
    };
  });
}

async function clickFirstVisible(locatorCandidates) {
  for (const locator of locatorCandidates) {
    try {
      if ((await locator.count()) > 0 && (await locator.first().isVisible())) {
        await locator.first().click();
        return true;
      }
    } catch (_error) {
      // Try the next locator.
    }
  }
  return false;
}

async function runThread(opts) {
  return await launchWithPage(opts, async (page) => {
    const notes = [];
    await gotoAndSettle(page, "https://www.linkedin.com/messaging/", opts);
    let login = await getLoginState(page);
    if (!login.loggedIn) {
      return {
        ok: false,
        command: "thread",
        error: "login_required_or_not_verified",
        extracted_at: nowIso(),
        chrome_profile: CHROME_PROFILE,
        headless: !opts.headed,
        ...login,
        conversations: [],
        notes: ["Run zone-li-login from a VM GUI session, complete LinkedIn login, then retry."],
      };
    }

    let targetLabel = opts.threadUrl || opts.profileUrl || opts.name;
    let profileName = null;
    let targetOpened = false;

    if (opts.threadUrl) {
      await gotoAndSettle(page, opts.threadUrl, opts);
      targetOpened = /\/messaging\/thread\//.test(page.url());
      if (!targetOpened) {
        notes.push("thread_url_did_not_open_messaging_thread");
      }
    } else if (opts.profileUrl) {
      await gotoAndSettle(page, opts.profileUrl, opts);
      profileName = await page.locator("h1").first().innerText({ timeout: 5000 }).catch(() => null);
      const clicked = await clickFirstVisible([
        page.getByRole("button", { name: /message/i }),
        page.getByRole("link", { name: /message/i }),
        page.locator('button[aria-label*="Message"], a[aria-label*="Message"]'),
        page.locator('a[href*="/messaging/thread/"]'),
      ]);
      targetOpened = clicked;
      if (!clicked) {
        notes.push("message_button_not_found");
      }
      await sleep(opts.settleMs + 1000);
    } else if (opts.name) {
      await gotoAndSettle(page, "https://www.linkedin.com/messaging/", opts);
      const cards = await collectConversationCards(page, 50);
      const wanted = opts.name.toLowerCase();
      const index = cards.findIndex((card) =>
        [...(card.participant_names || []), ...(card.preview_lines || [])]
          .join(" ")
          .toLowerCase()
          .includes(wanted)
      );
      if (index >= 0) {
        await openConversationFromCard(page, cards[index], index, opts);
        targetOpened = true;
        profileName = cards[index].participant_names ? cards[index].participant_names[0] : null;
      } else {
        notes.push("name_not_found_in_recent_conversation_list");
      }
    }

    login = await getLoginState(page);
    const thread = targetOpened
      ? await extractThreadMessages(page, opts.maxMessages)
      : { thread_title: null, messages: [] };

    return {
      ok: targetOpened,
      command: "thread",
      extracted_at: nowIso(),
      chrome_profile: CHROME_PROFILE,
      headless: !opts.headed,
      ...login,
      target: targetLabel,
      thread_url: opts.threadUrl,
      profile_url: opts.profileUrl,
      profile_name: cleanText(profileName),
      max_messages: opts.maxMessages,
      conversations: [
        {
          source: "linkedin",
          conversation_id: opts.threadUrl
            ? slugify(opts.threadUrl)
            : opts.profileUrl
              ? slugify(opts.profileUrl)
              : slugify(opts.name),
          thread_url: opts.threadUrl,
          profile_url: opts.profileUrl,
          participant_names: cleanText(profileName) ? [cleanText(profileName)] : [],
          thread_title: thread.thread_title,
          profile_urls: thread.profile_urls || [],
          messages: thread.messages,
          extraction_notes: notes,
        },
      ],
      notes,
    };
  });
}

async function resolveProfileTarget(page, opts, notes) {
  if (opts.profileUrl) {
    return { profileUrl: opts.profileUrl, profileName: null, source: "profile_url" };
  }

  if (opts.threadUrl) {
    await gotoAndSettle(page, opts.threadUrl, opts);
    if (!/\/messaging\/thread\//.test(page.url())) {
      notes.push("thread_url_did_not_open_messaging_thread");
      return { profileUrl: null, profileName: null, source: "thread_url" };
    }
    const thread = await extractThreadMessages(page, 1);
    const profileUrl = thread.profile_urls ? thread.profile_urls[0] || null : null;
    if (!profileUrl) {
      notes.push("profile_url_not_found_in_thread");
    }
    return {
      profileUrl,
      profileName: thread.thread_title || null,
      source: "thread_url",
      threadTitle: thread.thread_title,
      threadProfileUrls: thread.profile_urls || [],
    };
  }

  await gotoAndSettle(page, "https://www.linkedin.com/messaging/", opts);
  const cards = await collectConversationCards(page, 50);
  const wanted = opts.name.toLowerCase();
  const index = cards.findIndex((card) =>
    [...(card.participant_names || []), ...(card.preview_lines || [])].join(" ").toLowerCase().includes(wanted)
  );
  if (index < 0) {
    notes.push("name_not_found_in_recent_conversation_list");
    return { profileUrl: null, profileName: opts.name, source: "name" };
  }
  await openConversationFromCard(page, cards[index], index, opts);
  const thread = await extractThreadMessages(page, 1);
  const profileUrl = thread.profile_urls ? thread.profile_urls[0] || null : null;
  if (!profileUrl) {
    notes.push("profile_url_not_found_in_thread");
  }
  return {
    profileUrl,
    profileName: thread.thread_title || cards[index].participant_names[0] || opts.name,
    source: "name",
    threadTitle: thread.thread_title,
    threadProfileUrls: thread.profile_urls || [],
  };
}

async function runProfile(opts) {
  return await launchWithPage(opts, async (page) => {
    const notes = [];
    await gotoAndSettle(page, "https://www.linkedin.com/messaging/", opts);
    let login = await getLoginState(page);
    if (!login.loggedIn) {
      return {
        ok: false,
        command: "profile",
        error: "login_required_or_not_verified",
        extracted_at: nowIso(),
        chrome_profile: CHROME_PROFILE,
        headless: !opts.headed,
        ...login,
        profile: null,
        notes: ["Run zone-li-login from a VM GUI session, complete LinkedIn login, then retry."],
      };
    }

    const target = await resolveProfileTarget(page, opts, notes);
    if (!target.profileUrl) {
      return {
        ok: false,
        command: "profile",
        error: "profile_url_not_resolved",
        extracted_at: nowIso(),
        chrome_profile: CHROME_PROFILE,
        headless: !opts.headed,
        ...login,
        target: opts.threadUrl || opts.profileUrl || opts.name,
        profile: null,
        target_resolution: target,
        notes,
      };
    }

    const profileUrl = canonicalLinkedInUrl(target.profileUrl);
    await gotoAndSettle(page, profileUrl, opts);
    await scrollProfile(page, opts);
    login = await getLoginState(page);
    const profile = await extractProfileData(page, opts, target.source);
    profile.profile_url = canonicalLinkedInUrl(profile.profile_url || profileUrl);

    return {
      ok: true,
      command: "profile",
      extracted_at: nowIso(),
      chrome_profile: CHROME_PROFILE,
      headless: !opts.headed,
      ...login,
      target: opts.threadUrl || opts.profileUrl || opts.name,
      target_resolution: target,
      profile,
      notes,
    };
  });
}

function summarize(result, outputPath) {
  const conversations = Array.isArray(result.conversations) ? result.conversations : [];
  const messageCount = conversations.reduce(
    (sum, conversation) => sum + (Array.isArray(conversation.messages) ? conversation.messages.length : 0),
    0
  );
  const hasProfile = Boolean(result.profile);
  return {
    ok: result.ok,
    command: result.command,
    extracted_at: result.extracted_at,
    loggedIn: result.loggedIn,
    loginRequired: result.loginRequired,
    url: result.url,
    output: outputPath || null,
    conversation_count: conversations.length,
    message_count: messageCount,
    profile_extracted: hasProfile,
    profile_name: hasProfile ? result.profile.name || null : null,
    profile_url: hasProfile ? result.profile.profile_url || null : null,
    notes: result.notes || [],
    error: result.error || null,
  };
}

function emit(result, opts) {
  if (opts.output) {
    fs.mkdirSync(path.dirname(opts.output), { recursive: true });
    fs.writeFileSync(opts.output, `${JSON.stringify(result, null, 2)}\n`, { mode: 0o600 });
    fs.chmodSync(opts.output, 0o600);
  }
  const payload = opts.quiet ? summarize(result, opts.output) : result;
  process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`);
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  let result;
  if (opts.command === "health") {
    result = await runHealth(opts);
  } else if (opts.command === "recent") {
    result = await runRecent(opts);
  } else if (opts.command === "thread") {
    result = await runThread(opts);
  } else {
    result = await runProfile(opts);
  }
  emit(result, opts);

  if (result.ok === false && result.error === "login_required_or_not_verified") {
    process.exitCode = 3;
  } else if (result.ok === false) {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  process.stderr.write(
    `${JSON.stringify(
      {
        ok: false,
        command: process.argv[2] || null,
        extracted_at: nowIso(),
        error: error.message,
      },
      null,
      2
    )}\n`
  );
  process.exit(1);
});
