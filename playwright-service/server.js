const express = require('express');
const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

const cheerio = require('cheerio');
const cors = require('cors');

const app = express();
const PORT = 3001;

app.use(cors());
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: 'playwright-service' });
});

// Search endpoint
app.post('/search', async (req, res) => {
    const { query, max_results = 5 } = req.body;

    if (!query) {
        return res.status(400).json({ error: 'Query is required' });
    }

    console.log(`🔍 Searching for: ${query}`);

    try {
        const browser = await chromium.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        });
        const context = await browser.newContext({
            viewport: { width: 1920, height: 1080 },
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        });
        const page = await context.newPage();

        // Navigate to DuckDuckGo
        const searchUrl = `https://duckduckgo.com/?q=${encodeURIComponent(query)}`;
        console.log(`📡 Navigating to: ${searchUrl}`);
        await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 20000 });
        await page.waitForTimeout(2000);

        const content = await page.content();
        await browser.close();

        // Parse with Cheerio
        const $ = cheerio.load(content);
        const results = [];

        // Try multiple selectors
        let resultElements = $('article[data-testid="result"]');
        if (resultElements.length === 0) {
            resultElements = $('div.result');
        }
        if (resultElements.length === 0) {
            resultElements = $('li[data-layout="organic"]');
        }

        console.log(`🔍 Found ${resultElements.length} result elements`);

        // Strategy 1: DDG Parsing
        resultElements.slice(0, max_results).each((i, elem) => {
            const $elem = $(elem);
            const titleElem = $elem.find('h2').first() || $elem.find('a').first();
            const title = titleElem.text().trim() || 'No title';
            const linkElem = $elem.find('a[href]').first();
            const href = linkElem.attr('href') || '';
            const snippetElem = $elem.find('.result__snippet, span').first();
            const body = snippetElem.text().trim().substring(0, 200);

            if (href && title !== 'No title' && !href.includes('duckduckgo.com/')) {
                results.push({ title, href, body });
            }
        });

        // Strategy 2: Bing Fallback for Web Search
        if (results.length === 0) {
            console.log("🔄 DuckDuckGo web search failed, trying Bing...");
            const bingUrl = `https://www.bing.com/search?q=${encodeURIComponent(query)}`;
            const bingPage = await context.newPage();
            try {
                await bingPage.goto(bingUrl, { waitUntil: 'domcontentloaded', timeout: 20000 });
                const bingContent = await bingPage.content();
                const $bing = cheerio.load(bingContent);
                $bing('li.b_algo').each((i, elem) => {
                    if (results.length >= max_results) return;
                    const $e = $(elem);
                    const title = $e.find('h2').text().trim();
                    const href = $e.find('a').attr('href');
                    const snippet = $e.find('.b_caption p, .b_snippet').text().trim();
                    if (title && href) {
                        results.push({ title, href, body: snippet });
                    }
                });
                await bingPage.close();
            } catch (e) {
                console.error("❌ Bing web fallback failed:", e.message);
                await bingPage.close();
            }
        }

        await browser.close();
        console.log(`✅ Returning ${results.length} results`);
        res.json(results.length > 0 ? results : [{ title: 'No results', href: '', body: 'No results found' }]);

    } catch (error) {
        console.error(`❌ Search error:`, error);
        res.status(500).json({ error: `Search failed: ${error.message}` });
    }
});

// Scrape endpoint
app.post('/scrape', async (req, res) => {
    const { url } = req.body;

    if (!url) {
        return res.status(400).json({ error: 'URL is required' });
    }

    console.log(`🌐 Scraping: ${url}`);

    try {
        const browser = await chromium.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        });
        const context = await browser.newContext({
            viewport: { width: 1920, height: 1080 },
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        });
        const page = await context.newPage();

        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);

        const content = await page.content();
        await browser.close();

        // Parse with Cheerio
        const $ = cheerio.load(content);

        // Remove unwanted elements
        $('script, style, nav, footer, iframe, svg, header').remove();

        // Get text
        const text = $('body').text().replace(/\s+/g, ' ').trim();
        const cleanText = text.substring(0, 8000);

        console.log(`✅ Scraped ${cleanText.length} characters`);
        res.json({ text: cleanText });

    } catch (error) {
        console.error(`❌ Scrape error:`, error);
        res.status(500).json({ error: `Scraping failed: ${error.message}` });
    }
});

// Image Search endpoint
app.post('/search-images', async (req, res) => {
    const { query, max_results = 10 } = req.body;

    if (!query) {
        return res.status(400).json({ error: 'Query is required' });
    }

    console.log(`🖼️ Searching images for: ${query}`);

    try {
        const browser = await chromium.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        });
        const context = await browser.newContext({
            viewport: { width: 1920, height: 1080 },
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        });
        const page = await context.newPage();

        // Navigate to DuckDuckGo Images
        const searchUrl = `https://duckduckgo.com/?q=${encodeURIComponent(query)}&iax=images&ia=images`;
        console.log(`📡 Navigating to: ${searchUrl}`);
        await page.goto(searchUrl, { waitUntil: 'load', timeout: 30000 }); // 'load' is safer than 'domcontentloaded' for images

        // Wait for ANY image to load, not just specific classes
        try {
            await page.waitForSelector('img', { timeout: 5000 });
        } catch (e) {
            console.log('⚠️ Warning: Timeout waiting for images');
        }

        // Scroll aggressively to trigger lazy loading
        await page.evaluate(async () => {
            for (let i = 0; i < 4; i++) {
                window.scrollBy(0, 800);
                await new Promise(r => setTimeout(r, 800));
            }
        });
        await page.waitForTimeout(1000);

        const content = await page.content();
        const pageTitle = await page.title();
        console.log(`📄 Page Title: ${pageTitle}`);



        const $ = cheerio.load(content);
        let results = [];

        // Check for bot detection
        const pageText = $('body').text().toLowerCase();
        if (pageText.includes('robot') || pageText.includes('captcha') || pageText.includes('security check')) {
            console.error("❌ Bot detection detected on DuckDuckGo!");
        } else {
            // Strategy 1: Specific DDG selectors (tile--img__img)
            $('.tile--img__img').each((i, elem) => {
                extractImageFromElem($, elem, query, results, max_results);
            });
        }

        // Strategy 2: Fallback to any generic image (if Strategy 1 failed)
        if (results.length === 0) {
            console.log("⚠️ Standard DDG selectors failed, trying generic images...");
            $('img').each((i, elem) => {
                const alt = $(elem).attr('alt');
                if (alt && alt.length > 5) { // More selective
                    extractImageFromElem($, elem, query, results, max_results);
                }
            });
        }

        // --- BING FALLBACK ---
        if (results.length === 0) {
            console.log("🔄 DuckDuckGo failed, falling back to Bing Images...");
            const bingUrl = `https://www.bing.com/images/search?q=${encodeURIComponent(query)}&first=1`;
            await page.goto(bingUrl, { waitUntil: 'load', timeout: 30000 });

            await page.waitForTimeout(2000);
            await page.evaluate(() => window.scrollBy(0, 1000));
            await page.waitForTimeout(1000);

            const bingContent = await page.content();
            const $bing = cheerio.load(bingContent);

            $bing('.mimg').each((i, elem) => {
                if (results.length >= max_results) return;
                const src = $bing(elem).attr('src') || $bing(elem).attr('data-src');
                if (src && src.length > 20) {
                    results.push({
                        title: $bing(elem).attr('alt') || query,
                        image_url: src,
                        source_url: bingUrl,
                        thumbnail_url: src
                    });
                }
            });
        }

        await browser.close();
        console.log(`✅ Final count: ${results.length} images`);
        res.json(results);

    } catch (error) {
        console.error(`❌ Image search error:`, error);
        res.status(500).json({ error: `Image search failed: ${error.message}` });
    }
});

app.post('/search-videos', async (req, res) => {
    const { query, max_results = 5 } = req.body;
    if (!query) return res.status(400).json({ error: 'Query is required' });

    console.log(`🎬 Searching videos for: ${query}`);
    let browser;
    try {
        browser = await chromium.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        }); // Videos are easier to scrape headless
        const page = await browser.newPage();

        // Strategy: Use Bing Videos for better scraping stability
        const bingVideoUrl = `https://www.bing.com/videos/search?q=${encodeURIComponent(query)}`;
        console.log(`📡 Navigating to Bing Videos: ${bingVideoUrl}`);

        await page.goto(bingVideoUrl, { waitUntil: 'load', timeout: 30000 });
        await page.waitForTimeout(2000); // Wait for results to settle

        const content = await page.content();
        const $ = cheerio.load(content);
        const results = [];

        // Bing Video Selector: .dg_u
        $('.dg_u').each((i, elem) => {
            if (results.length >= max_results) return;

            const $elem = $(elem);
            const title = $elem.find('.mc_vtvc_title').text() || $elem.find('a').attr('title');
            const videoUrl = $elem.find('a').attr('href');
            const thumbnailUrl = $elem.find('img').attr('src') || $elem.find('img').attr('data-src');
            const duration = $elem.find('.time').text();

            if (videoUrl && title) {
                results.push({
                    title: title.trim(),
                    url: videoUrl.startsWith('http') ? videoUrl : `https://www.bing.com${videoUrl}`,
                    thumbnail_url: thumbnailUrl,
                    duration: duration,
                    platform: videoUrl.includes('youtube.com') ? 'YouTube' : 'Video'
                });
            }
        });

        await browser.close();
        console.log(`✅ Found ${results.length} videos`);
        res.json(results);

    } catch (error) {
        console.error(`❌ Video search error:`, error);
        if (browser) await browser.close();
        res.status(500).json({ error: `Video search failed: ${error.message}` });
    }
});

function extractImageFromElem($, elem, query, results, max_results) {
    if (results.length >= max_results) return;

    const $elem = $(elem);
    const src = $elem.attr('src') || $elem.attr('data-src') || $elem.attr('data-srcset');
    const alt = $elem.attr('alt') || query;

    // Filter out obvious garbage or tiny icons
    if (!src || src.length < 10) return;
    if (src.includes('assets.duckduckgo.com')) return;
    if (src.includes('logo') || src.includes('favicon') || src.includes('icon')) return;

    // Filter by alt text - if it's just "DuckDuckGo" or similar, it's a logo
    const lowAlt = alt.toLowerCase();
    if (lowAlt.includes('duckduckgo') || lowAlt.includes('logo') || lowAlt === 'logo' || lowAlt === 'image') return;

    // If it's a data URI, it must be a significant image (at least 200 chars)
    // Small data URIs are almost always placeholders/skeleton loaders
    if (src.startsWith('data:')) {
        if (!src.startsWith('data:image')) return;
        if (src.length < 200) return;
    }

    // Find parent link
    const parentLink = $elem.closest('a').attr('href') || '';

    results.push({
        title: alt,
        image_url: src,
        source_url: parentLink.startsWith('http') ? parentLink : `https://duckduckgo.com${parentLink}`,
        thumbnail_url: src
    });
}

app.listen(PORT, '0.0.0.0', () => {
    console.log(`
╔════════════════════════════════════════╗
║   Playwright Service Running           ║
║   Host: 0.0.0.0 / Port: ${PORT}        ║
╚════════════════════════════════════════╝
    `);
});
