import sys
import json
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

def scrape_and_analyze(url):
    print(f"Scraping {url}...")
    try:
        # Standardize URL
        if not url.startswith("http"):
            url = "https://" + url
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Scrape basic metadata
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        
        meta_desc = ""
        meta_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_tag:
            meta_desc = meta_tag.get('content', '').strip()
            
        h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all('h1')]
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True)) > 20][:10]
        images = soup.find_all('img')
        images_missing_alt = [img for img in images if not img.get('alt')]
        
        # Tech signals extraction
        scripts = [script.get('src', '') for script in soup.find_all('script') if script.get('src')]
        tech_signals = []
        if any('_next' in src for src in scripts): tech_signals.append("Next.js")
        if any('wp-content' in src for src in scripts): tech_signals.append("WordPress")
        if any('shopify' in src for src in scripts): tech_signals.append("Shopify")
        if any('webflow' in src for src in scripts): tech_signals.append("Webflow")
        if not tech_signals: tech_signals = ["Custom Web Architecture"]

        # Try to use LLMs if available
        api_key_openai = os.environ.get("OPENAI_API_KEY")
        api_key_gemini = os.environ.get("GEMINI_API_KEY")
        
        context = f"Website URL: {url}\nTitle: {title}\nDescription: {meta_desc}\nHeaders: {h1_tags}\nText: {' '.join(paragraphs)}\nMissing Alt Text Images: {len(images_missing_alt)}/{len(images)}"
        
        product_prompt = f"Based on the following scraped website data, generate a structured JSON for 'Product Intelligence'. Provide ONLY the valid JSON, nothing else.\n\nData:\n{context}\n\nRequired JSON format:\n{{\n  \"Product Overview\": {{\"Product Name\": \"\", \"Website\": \"\", \"One-liner\": \"\"}},\n  \"What It Does\": \"\",\n  \"Product Category & Type\": {{\"Categories\": \"\", \"Product Type\": \"\"}},\n  \"Target Customers\": \"\",\n  \"Business Model & Pricing\": {{\"Model\": \"\", \"Pricing\": \"\"}},\n  \"Key Features\": [\"\", \"\"],\n  \"Primary CTA\": \"\",\n  \"Tech Signals\": [\"{', '.join(tech_signals)}\"]\n}}"
        strategy_prompt = f"Based on the following scraped website data, generate a structured JSON for 'Market Strategy'. Provide ONLY the valid JSON, nothing else.\n\nData:\n{context}\n\nRequired JSON format:\n{{\n  \"1. Ideal Customer Profile (ICP)\": {{\"Primary Target\": \"\", \"Industries\": \"\", \"Role\": \"\", \"Pain points\": \"\"}},\n  \"2. Positioning Statement\": \"\",\n  \"3. Messaging Framework\": {{\"Core Value Proposition\": \"\", \"Pillars\": \"\", \"Tone\": \"\"}},\n  \"4. Channel Prioritization Report\": [\"\", \"\"],\n  \"5. 30-Day Roadmap\": {{\"Week 1\": \"\", \"Week 2\": \"\", \"Week 3\": \"\", \"Week 4\": \"\"}},\n  \"Primary KPIs to Track\": [\"\", \"\"]\n}}"
        actions_prompt = f"Based on the scraped data, generate an array of 3-4 actionable technical SEO fixes for this specific website. Provide ONLY the valid JSON array.\n\nData:\n{context}\n\nJSON Schema: [{{\"id\": \"A1\", \"title\": \"\", \"status\": \"PENDING\", \"overview\": \"\", \"steps\": [\"\", \"\"], \"target_file\": \"src/app/layout.tsx (or relevant file)\", \"before_code\": \"\", \"after_code\": \"\", \"impact\": \"\"}}]"
        social_prompt = f"Generate 3 highly engaging social media post drafts for this website: one for X (Twitter), one for LinkedIn, and one for Reddit. Focus on SEO value and brand authority. Provide ONLY a JSON object with keys 'X', 'LinkedIn', 'Reddit'.\n\nData:\n{context}"

        ai_success = False
        
        if api_key_openai and "your-actual-api-key" not in api_key_openai:
            try:
                import openai
                print("Using OpenAI GPT-4o-mini...")
                client = openai.OpenAI(api_key=api_key_openai)
                
                product_res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": product_prompt}], response_format={"type": "json_object"})
                product_info = json.loads(product_res.choices[0].message.content)
                
                strategy_res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": strategy_prompt}], response_format={"type": "json_object"})
                strategy = json.loads(strategy_res.choices[0].message.content)
                
                actions_res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": actions_prompt}], response_format={"type": "json_object"})
                actions_data = json.loads(actions_res.choices[0].message.content)
                
                social_res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": social_prompt}], response_format={"type": "json_object"})
                social_drafts = json.loads(social_res.choices[0].message.content)

                if isinstance(actions_data, dict) and "actions" in actions_data: actions = actions_data["actions"]
                elif isinstance(actions_data, list): actions = actions_data
                else: actions = list(actions_data.values())[0] if isinstance(list(actions_data.values())[0], list) else []
                ai_success = True
            except Exception as e:
                err_str = str(e)
                if "insufficient_quota" in err_str:
                    print("⚠️ OpenAI quota exceeded! Your OpenAI account has run out of credits.")
                else:
                    print(f"⚠️ Failed to use OpenAI: {err_str}")
        
        if not ai_success and api_key_gemini:
            try:
                import google.generativeai as genai
                print("Using Google Gemini API...")
                genai.configure(api_key=api_key_gemini)
                model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
                
                product_info = json.loads(model.generate_content(product_prompt).text)
                strategy = json.loads(model.generate_content(strategy_prompt).text)
                social_drafts = json.loads(model.generate_content(social_prompt).text)

                actions_data = json.loads(model.generate_content(actions_prompt).text)
                if isinstance(actions_data, dict) and "actions" in actions_data: actions = actions_data["actions"]
                elif isinstance(actions_data, list): actions = actions_data
                else: actions = list(actions_data.values())[0] if isinstance(list(actions_data.values())[0], list) else []
                ai_success = True
            except Exception as e:
                print(f"⚠️ Failed to use Gemini: {e}")
        if not ai_success:
            print("No valid AI API Key found or API failed. Generating dynamic heuristic strategy and SEO actions based on scraped data...")
            product_info, strategy, actions, social_drafts = generate_fallback(url, title, meta_desc, h1_tags, paragraphs, tech_signals, len(images), len(images_missing_alt))

        # Save Raw Scraped Data for Dashboard Metrics
        scraped_raw = {
            "url": url,
            "title": title,
            "meta_description": meta_desc,
            "h1_headings": h1_tags,
            "images": {
                "total": len(images),
                "missing_alt": len(images_missing_alt)
            }
        }
        
        os.makedirs("data", exist_ok=True)
        with open("data/scraped_raw.json", "w", encoding='utf-8') as f:
            json.dump(scraped_raw, f, indent=4, ensure_ascii=False)

        # Save the generated JSONs
        os.makedirs("data", exist_ok=True)
        os.makedirs("runtime/outputs", exist_ok=True)
        
        with open("data/product_info.json", "w", encoding='utf-8') as f:
            json.dump(product_info, f, indent=4, ensure_ascii=False)
            
        with open("data/strategy.json", "w", encoding='utf-8') as f:
            json.dump(strategy, f, indent=4, ensure_ascii=False)
            
        with open("data/social_drafts.json", "w", encoding='utf-8') as f:
            json.dump(social_drafts, f, indent=4, ensure_ascii=False)

        with open("runtime/outputs/actions.json", "w", encoding='utf-8') as f:
            json.dump(actions, f, indent=4, ensure_ascii=False)
            
        print(f"Successfully generated custom intelligence and SEO audit for {url}")
        
    except Exception as e:
        print(f"Critical error analyzing site: {e}")
        sys.exit(1)

def generate_fallback(url, title, meta_desc, h1_tags, paragraphs, tech_signals, total_images, missing_alt):
    """Fallback generator if no LLM API is available."""
    domain = urlparse(url).netloc.replace('www.', '')
    company_name = title.split('|')[0].strip() if '|' in title else title.split('-')[0].strip()
    if not company_name:
        company_name = domain

    # Dynamic Product Info
    product_info = {
        "Product Overview": {
            "Product Name": company_name,
            "Website": url,
            "One-liner": meta_desc if meta_desc else (paragraphs[0] if paragraphs else f"Digital solutions by {company_name}")
        },
        "What It Does": " ".join(paragraphs[:2]) if paragraphs else f"{company_name} is a platform providing targeted solutions for its audience.",
        "Product Category & Type": {
            "Categories": "Software / Service Platform",
            "Product Type": "B2B / B2C Solution"
        },
        "Target Customers": "Users and businesses searching for solutions related to: " + (h1_tags[0] if h1_tags else company_name),
        "Business Model & Pricing": {
            "Model": "Standard SaaS / Agency Model",
            "Pricing": "Available upon request or via website pricing page"
        },
        "Key Features": h1_tags if len(h1_tags) > 1 else ["Core Product Functionality", "Customer Support & Success", "Scalable Infrastructure"],
        "Primary CTA": "Get Started / Contact Us",
        "Tech Signals": tech_signals
    }
    
    # Dynamic Strategy
    strategy = {
        "1. Ideal Customer Profile (ICP)": {
            "Primary Target": f"Companies looking for {company_name} services",
            "Industries": "Technology, E-commerce, SaaS, Professional Services",
            "Role": "Decision Makers, Executives, Managers",
            "Pain points": "Inefficient processes, need for automation and expert help",
            "Trigger events": "Company growth, digital transformation initiatives"
        },
        "2. Positioning Statement": f"For businesses looking to scale, {company_name} provides robust, tailored solutions that deliver immediate ROI without the heavy overhead of traditional alternatives.",
        "3. Messaging Framework": {
            "Core Value Proposition": meta_desc if meta_desc else f"Unlock your potential with {company_name}.",
            "Pillar 1 — Efficiency": "Streamline your workflows and save time.",
            "Pillar 2 — Expertise": "Built by industry professionals for maximum impact.",
            "Tone": "Professional, authoritative, and direct."
        },
        "4. Channel Prioritization Report": [
            "1. SEO / Content Marketing: Target high-intent queries.",
            "2. LinkedIn/B2B Outreach: Direct contact with decision makers.",
            "3. Paid Search: Capture intent at the bottom of the funnel."
        ],
        "5. 30-Day Roadmap": {
            "Week 1 — Foundation": f"Audit {domain} messaging, define 3 core ICPs, and launch initial outreach.",
            "Week 2 — Content": "Publish cornerstone content piece related to primary offering.",
            "Week 3 — Activation": "Launch targeted email sequence to 50 curated prospects.",
            "Week 4 — Optimization": "Review engagement metrics, A/B test CTAs, and refine targeting."
        },
        "Primary KPIs to Track": [
            "Qualified Leads Generated",
            "Organic Traffic Growth (MoM)",
            "Conversion Rate on primary CTA"
        ]
    }
    
    # Dynamic SEO Actions (The Audit)
    actions = []
    
    # Check 1: Title Length
    if not title:
        actions.append({
            "id": "A1",
            "title": "Add Missing Title Tag",
            "status": "PENDING",
            "overview": "The homepage is entirely missing a <title> tag, which is the most critical on-page SEO element.",
            "steps": ["Identify primary keywords for the brand.", "Write a title tag under 60 characters.", "Insert it into the <head> of the document."],
            "target_file": "src/app/layout.tsx",
            "before_code": "<head>\n  <meta charSet=\"utf-8\" />\n</head>",
            "after_code": f"<head>\n  <meta charSet=\"utf-8\" />\n  <title>{domain} | Premium Services</title>\n</head>",
            "impact": "Massive improvement in organic search visibility and indexability."
        })
    elif len(title) > 60:
        actions.append({
            "id": "A1",
            "title": f"Optimize Truncated Title Tag ({len(title)} chars)",
            "status": "PENDING",
            "overview": f"Google truncates title tags beyond 60 characters. Your current title is {len(title)} characters.",
            "steps": ["Review current title.", "Identify primary keyword.", "Rewrite to under 60 characters."],
            "target_file": "src/app/layout.tsx",
            "before_code": f"<title>{title}</title>",
            "after_code": f"<title>{company_name} | Top Solutions</title>",
            "impact": "Can improve click-through rates by 5-15%."
        })
    else:
         actions.append({
            "id": "A1",
            "title": "Expand Short Title Tag",
            "status": "PENDING",
            "overview": "Your title tag is under-optimized and leaves room for secondary keywords.",
            "steps": ["Research relevant secondary keywords.", "Expand title tag closer to the 60 character limit."],
            "target_file": "src/app/layout.tsx",
            "before_code": f"<title>{title}</title>",
            "after_code": f"<title>{title} | Expert Solutions & Services</title>",
            "impact": "Captures long-tail search traffic."
        })

    # Check 2: Missing H1
    if not h1_tags:
        actions.append({
            "id": "A2",
            "title": "Add Missing H1 Heading",
            "status": "PENDING",
            "overview": "The page is missing an H1 tag. Search engines use the H1 to understand the primary topic of the page.",
            "steps": ["Write a compelling H1 containing the target keyword.", "Wrap the main hero text in an <h1> tag."],
            "target_file": "src/app/page.tsx",
            "before_code": "<div className=\"hero\">\n  <span>Welcome to our site</span>\n</div>",
            "after_code": f"<div className=\"hero\">\n  <h1>{company_name}: The Ultimate Solution for Your Business</h1>\n</div>",
            "impact": "Directly impacts core topic relevance signals."
        })
    
    # Check 3: Alt Text
    if missing_alt > 0:
         actions.append({
            "id": "A3",
            "title": f"Fix Missing Alt Text on {missing_alt} Images",
            "status": "PENDING",
            "overview": f"Missing alt text on images is an accessibility violation and a direct SEO signal loss. Found {missing_alt} out of {total_images} images missing alt text.",
            "steps": ["Audit all images.", "Write descriptive, keyword-relevant alt text.", "Update in the CMS or code."],
            "target_file": "src/components/Hero.tsx",
            "before_code": "<img src=\"/hero-banner.jpg\" alt=\"\" />",
            "after_code": f"<img src=\"/hero-banner.jpg\" alt=\"{company_name} digital solutions overview\" />",
            "impact": "Improves image search traffic and accessibility."
        })
    elif total_images == 0:
         actions.append({
            "id": "A3",
            "title": "Add Media Richness",
            "status": "PENDING",
            "overview": "The page contains no images, reducing engagement and media-search visibility.",
            "steps": ["Design custom graphics or product screenshots.", "Add them to the page with descriptive alt text."],
            "target_file": "src/app/page.tsx",
            "before_code": "<section id=\"about\">\n  <p>About us...</p>\n</section>",
            "after_code": "<section id=\"about\">\n  <p>About us...</p>\n  <img src=\"/product-demo.png\" alt=\"Product Demonstration\" />\n</section>",
            "impact": "Increases time on page and unlocks image search channels."
        })

    # Check 4: Meta Description
    if not meta_desc:
        actions.append({
            "id": "A4",
            "title": "Add Missing Meta Description",
            "status": "PENDING",
            "overview": "A meta description is missing. Google will auto-generated one from random page text, which hurts click-through rate.",
            "steps": ["Draft a compelling 150-160 character description.", "Include a clear call to action."],
            "target_file": "src/app/layout.tsx",
            "before_code": "export const metadata = {\n  title: 'Home',\n}",
            "after_code": f"export const metadata = {{\n  title: 'Home',\n  description: 'Discover how {company_name} provides industry-leading solutions to help you scale faster. Contact us today!',\n}}",
            "impact": "Directly improves organic CTR."
        })

    # Dynamic Social Drafts
    social_drafts = {
        "X": f"🚀 Exciting things happening at {company_name}! Check out how we're transforming IT solutions: {url} #IT #Innovation #Tech",
        "LinkedIn": f"We are proud to share our latest advancements in digital transformation at {company_name}. Visit our website to learn more about our services and how we can help your business grow: {url}",
        "Reddit": f"If you're looking for leading IT solutions, you should definitely check out {company_name}. They have a great track record and an impressive suite of services: {url}"
    }

    return product_info, strategy, actions, social_drafts

if __name__ == "__main__":
    if len(sys.argv) > 1:
        scrape_and_analyze(sys.argv[1])
    else:
        print("Please provide a URL")
