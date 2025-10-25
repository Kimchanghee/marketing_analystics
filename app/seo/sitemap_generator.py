"""
Sitemap 생성 서비스

동적으로 sitemap.xml을 생성하여 검색 엔진 크롤링 최적화
"""

from datetime import datetime
from typing import List, Dict
from xml.etree import ElementTree as ET


class SitemapGenerator:
    """Sitemap.xml 생성기"""

    def __init__(self, base_url: str = "https://creatorcontrol.center"):
        self.base_url = base_url.rstrip("/")
        self.xmlns = "http://www.sitemaps.org/schemas/sitemap/0.9"
        self.xmlns_xhtml = "http://www.w3.org/1999/xhtml"

    def generate_sitemap(self) -> str:
        """다국어 sitemap.xml 생성"""
        urlset = ET.Element("urlset")
        urlset.set("xmlns", self.xmlns)
        urlset.set("xmlns:xhtml", self.xmlns_xhtml)

        # 모든 페이지 정의
        pages = self._get_all_pages()

        for page in pages:
            url_elem = self._create_url_element(page)
            urlset.append(url_elem)

        # XML 생성
        tree = ET.ElementTree(urlset)
        ET.indent(tree, space="  ")

        # XML 문자열로 변환
        xml_str = ET.tostring(urlset, encoding="unicode", method="xml")
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str

    def _get_all_pages(self) -> List[Dict]:
        """모든 페이지 URL 정의"""
        today = datetime.now().strftime("%Y-%m-%d")

        pages = [
            {
                "path": "/",
                "priority": "1.0",
                "changefreq": "daily",
                "lastmod": today,
                "alternates": True,
            },
            {
                "path": "/services",
                "priority": "0.9",
                "changefreq": "weekly",
                "lastmod": today,
                "alternates": True,
            },
            {
                "path": "/personal",
                "priority": "0.9",
                "changefreq": "weekly",
                "lastmod": today,
                "alternates": True,
            },
            {
                "path": "/business",
                "priority": "0.9",
                "changefreq": "weekly",
                "lastmod": today,
                "alternates": True,
            },
            {
                "path": "/support",
                "priority": "0.8",
                "changefreq": "weekly",
                "lastmod": today,
                "alternates": True,
            },
            {
                "path": "/signup",
                "priority": "0.8",
                "changefreq": "monthly",
                "lastmod": today,
                "alternates": True,
            },
            {
                "path": "/login",
                "priority": "0.7",
                "changefreq": "monthly",
                "lastmod": today,
                "alternates": True,
            },
        ]

        return pages

    def _create_url_element(self, page: Dict) -> ET.Element:
        """개별 URL 요소 생성"""
        url_elem = ET.Element("url")

        # loc
        loc = ET.SubElement(url_elem, "loc")
        loc.text = self.base_url + page["path"]

        # lastmod
        if "lastmod" in page:
            lastmod = ET.SubElement(url_elem, "lastmod")
            lastmod.text = page["lastmod"]

        # changefreq
        if "changefreq" in page:
            changefreq = ET.SubElement(url_elem, "changefreq")
            changefreq.text = page["changefreq"]

        # priority
        if "priority" in page:
            priority = ET.SubElement(url_elem, "priority")
            priority.text = page["priority"]

        # 다국어 alternate links (hreflang)
        if page.get("alternates", False):
            for lang in ["ko", "en", "ja"]:
                xhtml_link = ET.SubElement(url_elem, "{http://www.w3.org/1999/xhtml}link")
                xhtml_link.set("rel", "alternate")
                xhtml_link.set("hreflang", lang)
                xhtml_link.set("href", f"{self.base_url}{page['path']}?lang={lang}")

            # x-default
            xhtml_link_default = ET.SubElement(url_elem, "{http://www.w3.org/1999/xhtml}link")
            xhtml_link_default.set("rel", "alternate")
            xhtml_link_default.set("hreflang", "x-default")
            xhtml_link_default.set("href", f"{self.base_url}{page['path']}")

        return url_elem


def generate_robots_txt(base_url: str = "https://creatorcontrol.center") -> str:
    """robots.txt 생성"""
    robots_txt = f"""# robots.txt for Creator Control Center
# https://www.robotstxt.org/

User-agent: *
Allow: /
Allow: /static/
Disallow: /dashboard
Disallow: /manager/
Disallow: /super-admin
Disallow: /api/

# Sitemap
Sitemap: {base_url}/sitemap.xml

# Crawl-delay
Crawl-delay: 1

# Specific bots
User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

User-agent: Slurp
Allow: /

User-agent: DuckDuckBot
Allow: /

User-agent: Baiduspider
Allow: /

User-agent: YandexBot
Allow: /
"""
    return robots_txt


def get_sitemap_generator(base_url: str = "https://creatorcontrol.center") -> SitemapGenerator:
    """Sitemap 생성기 인스턴스 반환"""
    return SitemapGenerator(base_url=base_url)
