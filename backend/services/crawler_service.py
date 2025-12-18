import os
from firecrawl import FirecrawlApp
from typing import Optional, Dict

class CrawlerService:
    def __init__(self):
        api_key = os.getenv("FIRECRAWL_API_KEY")
        self.app = FirecrawlApp(api_key=api_key)

    async def crawl_url(self, url: str) -> Optional[Dict]:
        """Crawls a single URL and returns LLM-ready markdown."""
        if not self.app:
            raise ValueError("Firecrawl API Key not configured.")

        print(f"🕷️ Crawling: {url}...")
        
        try:
            # Scrape specific URL (fast)
            scrape_result = self.app.scrape_url(url, params={
                'formats': ['markdown'],
                'onlyMainContent': True
            })
            
            return {
                "title": scrape_result.get('metadata', {}).get('title', 'Untitled'),
                "content": scrape_result.get('markdown', ''),
                "source_url": url
            }
        except Exception as e:
            print(f"❌ Crawl Failed for {url}: {e}")
            return None

    async def crawl_domain(self, domain_url: str, limit: int = 10) -> list[Dict]:
        """Crawls an entire domain (e.g., a documentation site)."""
        if not self.app: return []

        print(f"🕸️ Submitting Crawl Job: {domain_url}...")
        
        # 1. Submit Async Job
        crawl_job = self.app.async_crawl_url(domain_url, params={
            'limit': limit, 
            'scrapeOptions': {'formats': ['markdown']}
        })
        
        job_id = crawl_job['id']
        print(f" ↳ Job ID: {job_id}")

        # 2. Polling Loop
        max_retries = 20 # Wait up to ~100 seconds
        for _ in range(max_retries):
            status_response = self.app.check_crawl_status(job_id)
            status = status_response['status']
            
            print(f" ↳ Status: {status}...")
            
            if status == 'completed':
                print("   ✅ Crawl Finished.")
                return status_response['data'] # The list of pages
            
            elif status == 'failed':
                print("   ❌ Crawl Job Failed.")
                return []
            
            # Wait 5 seconds before checking again
            await asyncio.sleep(5)

        print(" ⚠️ Crawl Timed Out.")
        return []

# Singleton
crawler = CrawlerService()