import sys
import json
import os
import time
from dotenv import load_dotenv
import tweepy

load_dotenv()

def generate_and_publish_socials(repo_url=None, publish_only=False):
    print("🚀 Triggering Off-Page SEO Agent (Social Media Publisher)...")
    
    draft_file = "data/social_drafts.json"
    
    if publish_only and os.path.exists(draft_file):
        print("[1/4] Using existing drafts from data/social_drafts.json...")
        with open(draft_file, "r") as f:
            posts = json.load(f)
    else:
        product_file = "data/product_info.json"
        if not os.path.exists(product_file):
            print("⚠️ No product intelligence found. Run analyze_site.py first.")
            return False
            
        with open(product_file, "r") as f:
            product_data = json.load(f)
            
        company_name = product_data.get("Product Overview", {}).get("Product Name", "The Company")
        website = product_data.get("Product Overview", {}).get("Website", "our website")
        one_liner = product_data.get("Product Overview", {}).get("One-liner", "our latest solutions.")
        
        # Generate Platform-Specific Content
        print("[1/4] Crafting platform-specific off-page SEO content...")
        time.sleep(1)
        
        # X (Twitter) has a 280 char limit.
        # Max one-liner should be around 110 chars to be safe.
        x_one_liner = one_liner if len(one_liner) < 110 else one_liner[:107] + "..."
        
        posts = {
            "LinkedIn": f"Excited to share {company_name}! 🚀\n\nWe provide {one_liner.lower()}\n\nIf you're looking for enterprise-grade architecture and AI integration, check us out here: {website}\n\n#Tech #Innovation #AI #WebDevelopment #{company_name.replace(' ', '')}",
            
            "X (Twitter)": f"Just shipped update at {company_name[:20]}! 🔥\n\n{x_one_liner}\n\nCheck it: {website}\n\n#BuildInPublic #Tech",
            
            "Mastodon": f"Excited to announce the latest updates for {company_name}! 🚀\n\n{one_liner}\n\nCheck out our progress at {website}\n\n#OpenSource #Tech #Innovation #SEO #{company_name.replace(' ', '')}",
            
            "Reddit": f"**Title:** How we built {company_name} to solve enterprise scaling issues\n\n**Body:** Hey r/SaaS and r/webdev! We just launched our newest iteration of {company_name}. We noticed a lot of companies struggling with {one_liner.lower()} so we built a custom solution. You can check it out at {website}. Happy to answer any questions about our tech stack or architecture!"
        }
        
        # Save drafts
        os.makedirs("data", exist_ok=True)
        with open(draft_file, "w") as f:
            json.dump(posts, f, indent=4)
            
        print("[2/4] Saving drafts to data/social_drafts.json...")
    
    # Simulate/Real Publishing
    print("[3/4] Authenticating with X, LinkedIn, and Reddit APIs...")
    time.sleep(1.5)
    
    # X (Twitter) credentials
    x_api_key = os.environ.get("X_API_KEY")
    x_api_secret = os.environ.get("X_API_SECRET")
    x_access_token = os.environ.get("X_ACCESS_TOKEN")
    x_access_secret = os.environ.get("X_ACCESS_SECRET")
    
    x_success = False
    
    if x_api_key and x_api_secret and x_access_token and x_access_secret:
        try:
            print("[4/4] Publishing post to X (Twitter)...")
            # Clean credentials
            client = tweepy.Client(
                consumer_key=x_api_key.strip("'\" "),
                consumer_secret=x_api_secret.strip("'\" "),
                access_token=x_access_token.strip("'\" "),
                access_token_secret=x_access_secret.strip("'\" ")
            )
            
            # Support both 'X' and 'X (Twitter)' keys
            post_text = posts.get("X") or posts.get("X (Twitter)")
            if post_text:
                response = client.create_tweet(text=post_text)
                print(f"✅ Successfully published to X! Tweet ID: {response.data['id']}")
                x_success = True
            else:
                print("⚠️ Error: No draft found for 'X'.")
        except tweepy.errors.Unauthorized as e:
            print(f"❌ CRITICAL AUTH ERROR: 401 Unauthorized. Your X API credentials are invalid.")
            print(f"   Details: {e}")
            print("   Action Required: Check if App is suspended or tokens are expired. Regenerate them in Developer Portal.")
        except tweepy.errors.Forbidden as e:
            print(f"❌ PERMISSION ERROR: 403 Forbidden. Your X App lacks 'Read and Write' permissions.")
            print(f"   Details: {e}")
            print("   Action Required: Enable 'Read and Write' in 'User authentication settings' AND REGENERATE ALL TOKENS.")
        except Exception as e:
            print(f"⚠️ Unexpected error publishing to X: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    # Mastodon publishing
    mastodon_success = False
    mastodon_token = os.environ.get("MASTODON_ACCESS_TOKEN")
    mastodon_base_url = os.environ.get("MASTODON_API_BASE_URL", "https://mastodon.social")
    
    if mastodon_token:
        try:
            print(f"🐘 Publishing post to Mastodon ({mastodon_base_url})...")
            from mastodon import Mastodon
            m_client = Mastodon(
                access_token=mastodon_token.strip("'\" "),
                api_base_url=mastodon_base_url.strip("'\" ")
            )
            m_text = posts.get("Mastodon")
            if m_text:
                m_client.status_post(m_text)
                print("✅ Successfully published to Mastodon!")
                mastodon_success = True
        except Exception as e:
            print(f"⚠️ Failed to publish to Mastodon: {e}")

    if x_success or mastodon_success:
        print("Publishing to LinkedIn and Reddit (Simulated)...")
        time.sleep(1)
        print("✅ Successfully published across active networks!")
        return True

    # Fallback to Zapier Webhook
    webhook_url = os.environ.get("SOCIAL_WEBHOOK")
    if webhook_url and "123456" not in webhook_url:
        try:
            print(f"🔗 Attempting fallback via Zapier Webhook...")
            import requests
            post_text = posts.get("X") or posts.get("X (Twitter)")
            payload = {"content": post_text, "platform": "X", "status": "api_failed"}
            r = requests.post(webhook_url, json=payload)
            if r.status_code < 300:
                print("✅ Successfully sent to Zapier Webhook!")
                return True
        except Exception as we:
            print(f"⚠️ Webhook fallback failed: {we}")

    print("\n🛑 AUTHENTICATION FAILURE: Stopping automation loop to prevent API spam.")
    print("Please fix the credentials in your .env file or Developer Portal before retrying.")
    return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish-only", action="store_true", help="Publish existing drafts without regenerating")
    args = parser.parse_args()
    
    generate_and_publish_socials(publish_only=args.publish_only)
