"""
SEO 및 AEO 최적화 서비스

2025년 구글 AI 검색 및 Answer Engine 최적화를 위한 종합 SEO 서비스
- Structured Data (JSON-LD)
- Meta Tags
- OpenGraph
- Twitter Cards
- Multilingual Support (ko, en, ja)
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class SEOService:
    """SEO 및 AEO 최적화를 위한 서비스"""

    def __init__(self, locale: str = "ko"):
        """
        Args:
            locale: 언어 코드 (ko, en, ja)
        """
        self.locale = locale
        self.seo_data = self._load_seo_data(locale)

    def _load_seo_data(self, locale: str) -> Dict[str, Any]:
        """언어별 SEO 메타데이터 로드"""
        seo_dir = Path(__file__).parent / "locales"
        file_path = seo_dir / f"{locale}.json"

        if not file_path.exists():
            # Fallback to Korean
            file_path = seo_dir / "ko.json"

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_page_metadata(self, page: str = "home") -> Dict[str, str]:
        """페이지별 메타데이터 반환"""
        page_data = self.seo_data.get("pages", {}).get(page, self.seo_data["pages"]["home"])
        site_data = self.seo_data.get("site", {})

        return {
            "title": page_data.get("title", site_data.get("name", "")),
            "description": page_data.get("description", site_data.get("description", "")),
            "keywords": page_data.get("keywords", ""),
            "og_type": page_data.get("og_type", "website"),
            "locale": site_data.get("locale", "ko_KR"),
            "site_name": site_data.get("name", ""),
            "url": site_data.get("url", ""),
            "image": site_data.get("image", ""),
        }

    def generate_meta_tags(self, page: str = "home") -> str:
        """HTML meta tags 생성"""
        meta = self.get_page_metadata(page)

        tags = [
            f'<meta name="description" content="{meta["description"]}">',
            f'<meta name="keywords" content="{meta["keywords"]}">',
            '<meta name="author" content="Creator Control Center">',
            '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">',
            '<meta name="googlebot" content="index, follow">',
            '<meta name="bingbot" content="index, follow">',
            '<link rel="canonical" href="' + meta["url"] + '">',
        ]

        return "\n    ".join(tags)

    def generate_opengraph_tags(self, page: str = "home", image_url: Optional[str] = None) -> str:
        """OpenGraph meta tags 생성 (소셜 미디어 공유 최적화)"""
        meta = self.get_page_metadata(page)
        image = image_url or meta["image"]

        tags = [
            f'<meta property="og:type" content="{meta["og_type"]}">',
            f'<meta property="og:title" content="{meta["title"]}">',
            f'<meta property="og:description" content="{meta["description"]}">',
            f'<meta property="og:url" content="{meta["url"]}">',
            f'<meta property="og:site_name" content="{meta["site_name"]}">',
            f'<meta property="og:locale" content="{meta["locale"]}">',
            f'<meta property="og:image" content="{image}">',
            '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="630">',
            f'<meta property="og:image:alt" content="{meta["title"]}">',
        ]

        return "\n    ".join(tags)

    def generate_twitter_cards(self, page: str = "home", image_url: Optional[str] = None) -> str:
        """Twitter Card meta tags 생성"""
        meta = self.get_page_metadata(page)
        image = image_url or meta["image"]

        tags = [
            '<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{meta["title"]}">',
            f'<meta name="twitter:description" content="{meta["description"]}">',
            f'<meta name="twitter:image" content="{image}">',
            f'<meta name="twitter:image:alt" content="{meta["title"]}">',
        ]

        return "\n    ".join(tags)

    def generate_organization_schema(self) -> str:
        """Organization structured data (JSON-LD) 생성"""
        org = self.seo_data.get("organization", {})

        schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": org.get("name", "Creator Control Center"),
            "description": org.get("description", ""),
            "url": self.seo_data["site"]["url"],
            "logo": {
                "@type": "ImageObject",
                "url": org.get("logo", "/static/images/logo.png")
            },
            "foundingDate": org.get("foundingDate", "2024"),
            "contactPoint": {
                "@type": "ContactPoint",
                "email": org.get("contactEmail", "hello@creatorcontrol.center"),
                "contactType": "customer support"
            },
            "sameAs": org.get("sameAs", [])
        }

        return self._json_ld_script(schema)

    def generate_website_schema(self) -> str:
        """WebSite structured data (JSON-LD) 생성"""
        site = self.seo_data.get("site", {})

        schema = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": site.get("name", "Creator Control Center"),
            "url": site.get("url", ""),
            "description": site.get("description", ""),
            "inLanguage": self.locale,
            "potentialAction": {
                "@type": "SearchAction",
                "target": {
                    "@type": "EntryPoint",
                    "urlTemplate": site.get("url", "") + "/search?q={search_term_string}"
                },
                "query-input": "required name=search_term_string"
            }
        }

        return self._json_ld_script(schema)

    def generate_webpage_schema(self, page: str = "home") -> str:
        """WebPage structured data (JSON-LD) 생성"""
        meta = self.get_page_metadata(page)

        schema = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": meta["title"],
            "description": meta["description"],
            "url": meta["url"],
            "inLanguage": self.locale,
            "isPartOf": {
                "@type": "WebSite",
                "name": self.seo_data["site"]["name"],
                "url": self.seo_data["site"]["url"]
            }
        }

        return self._json_ld_script(schema)

    def generate_faq_schema(self) -> str:
        """FAQPage structured data (JSON-LD) 생성 - AEO 최적화"""
        faq_items = self.seo_data.get("faq", [])

        if not faq_items:
            return ""

        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["question"],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": item["answer"]
                    }
                }
                for item in faq_items
            ]
        }

        return self._json_ld_script(schema)

    def generate_software_application_schema(self) -> str:
        """SoftwareApplication structured data (JSON-LD) 생성"""
        site = self.seo_data.get("site", {})

        schema = {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": site.get("name", "Creator Control Center"),
            "description": site.get("description", ""),
            "url": site.get("url", ""),
            "applicationCategory": "BusinessApplication",
            "operatingSystem": "Web",
            "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD"
            },
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": "4.8",
                "ratingCount": "127"
            }
        }

        return self._json_ld_script(schema)

    def generate_breadcrumb_schema(self, breadcrumbs: List[Dict[str, str]]) -> str:
        """
        BreadcrumbList structured data (JSON-LD) 생성

        Args:
            breadcrumbs: [{"name": "Home", "url": "/"}, {"name": "Services", "url": "/services"}]
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": idx + 1,
                    "name": item["name"],
                    "item": self.seo_data["site"]["url"] + item["url"]
                }
                for idx, item in enumerate(breadcrumbs)
            ]
        }

        return self._json_ld_script(schema)

    def _json_ld_script(self, schema: Dict[str, Any]) -> str:
        """JSON-LD script tag 생성"""
        json_str = json.dumps(schema, ensure_ascii=False, indent=2)
        return f'<script type="application/ld+json">\n{json_str}\n</script>'

    def generate_all_schemas(self, page: str = "home", include_faq: bool = False) -> str:
        """모든 structured data 생성"""
        schemas = [
            self.generate_organization_schema(),
            self.generate_website_schema(),
            self.generate_webpage_schema(page),
        ]

        if page == "home":
            schemas.append(self.generate_software_application_schema())

        if include_faq:
            faq_schema = self.generate_faq_schema()
            if faq_schema:
                schemas.append(faq_schema)

        return "\n    ".join(schemas)

    def generate_complete_seo_head(
        self,
        page: str = "home",
        include_faq: bool = False,
        custom_image: Optional[str] = None
    ) -> str:
        """완전한 SEO head 섹션 생성 (meta tags + structured data)"""
        components = [
            self.generate_meta_tags(page),
            self.generate_opengraph_tags(page, custom_image),
            self.generate_twitter_cards(page, custom_image),
            self.generate_all_schemas(page, include_faq),
        ]

        return "\n    ".join(components)


def get_seo_service(locale: str = "ko") -> SEOService:
    """SEO 서비스 인스턴스 반환"""
    return SEOService(locale=locale)
