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
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


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

    def generate_hreflang_tags(self, page_path: str = "/") -> str:
        """hreflang 태그 생성 (다국어 SEO 최적화)"""
        base_url = self.seo_data["site"]["url"]

        # 언어별 locale 매핑
        locale_map = {
            "ko": "ko-KR",
            "en": "en-US",
            "ja": "ja-JP"
        }

        tags = []

        # 각 언어별 hreflang 태그
        for lang, locale_code in locale_map.items():
            url = f"{base_url}{page_path}?lang={lang}"
            tags.append(f'<link rel="alternate" hreflang="{lang}" href="{url}">')
            # 지역별 태그도 추가
            tags.append(f'<link rel="alternate" hreflang="{locale_code}" href="{url}">')

        # x-default (기본 언어)
        tags.append(f'<link rel="alternate" hreflang="x-default" href="{base_url}{page_path}">')

        return "\n    ".join(tags)

    def generate_opengraph_tags(self, page: str = "home", image_url: Optional[str] = None) -> str:
        """OpenGraph meta tags 생성 (소셜 미디어 공유 최적화)"""
        meta = self.get_page_metadata(page)
        image = image_url or meta["image"]

        # 다국어 locale 매핑
        locale_alternates = {
            "ko": "ko_KR",
            "en": "en_US",
            "ja": "ja_JP"
        }

        tags = [
            f'<meta property="og:type" content="{meta["og_type"]}">',
            f'<meta property="og:title" content="{meta["title"]}">',
            f'<meta property="og:description" content="{meta["description"]}">',
            f'<meta property="og:url" content="{meta["url"]}">',
            f'<meta property="og:site_name" content="{meta["site_name"]}">',
            f'<meta property="og:locale" content="{meta["locale"]}">',
        ]

        # og:locale:alternate 추가 (다국어 대체)
        current_locale = meta["locale"]
        for lang, locale_code in locale_alternates.items():
            if locale_code != current_locale:
                tags.append(f'<meta property="og:locale:alternate" content="{locale_code}">')

        tags.extend([
            f'<meta property="og:image" content="{image}">',
            '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="630">',
            f'<meta property="og:image:alt" content="{meta["title"]}">',
            '<meta property="og:image:type" content="image/jpeg">',
        ])

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
            logger.debug(f"No FAQ items found for locale '{self.locale}', skipping FAQ schema generation")
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

    def generate_video_object_schema(self) -> str:
        """VideoObject structured data (JSON-LD) 생성 - 크리에이터 플랫폼용"""
        site = self.seo_data.get("site", {})

        schema = {
            "@context": "https://schema.org",
            "@type": "VideoObject",
            "name": self.seo_data.get("video", {}).get("name", "Creator Control Center Platform Tour"),
            "description": self.seo_data.get("video", {}).get("description", site.get("description", "")),
            "thumbnailUrl": self.seo_data.get("video", {}).get("thumbnail", "/static/images/video-thumbnail.jpg"),
            "uploadDate": self.seo_data.get("video", {}).get("uploadDate", "2024-01-01"),
            "contentUrl": self.seo_data.get("video", {}).get("contentUrl", ""),
            "embedUrl": self.seo_data.get("video", {}).get("embedUrl", ""),
            "duration": "PT2M30S",
            "publisher": {
                "@type": "Organization",
                "name": "Creator Control Center",
                "logo": {
                    "@type": "ImageObject",
                    "url": self.seo_data.get("organization", {}).get("logo", "/static/images/logo.png")
                }
            }
        }

        # contentUrl이 없으면 스키마 생성 안 함
        if not self.seo_data.get("video", {}).get("contentUrl"):
            logger.debug(f"No video contentUrl configured for locale '{self.locale}', skipping VideoObject schema generation")
            return ""

        return self._json_ld_script(schema)

    def generate_article_schema(self, page: str = "home") -> str:
        """Article/BlogPosting structured data (JSON-LD) 생성 - E-E-A-T 강화"""
        meta = self.get_page_metadata(page)
        site = self.seo_data.get("site", {})

        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": meta["title"],
            "description": meta["description"],
            "image": meta["image"],
            "datePublished": "2024-01-01T00:00:00+00:00",
            "dateModified": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "author": {
                "@type": "Organization",
                "name": "Creator Control Center",
                "url": site.get("url", "")
            },
            "publisher": {
                "@type": "Organization",
                "name": "Creator Control Center",
                "logo": {
                    "@type": "ImageObject",
                    "url": self.seo_data.get("organization", {}).get("logo", "/static/images/logo.png")
                }
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": meta["url"]
            },
            "inLanguage": self.locale
        }

        return self._json_ld_script(schema)

    def generate_howto_schema(self) -> str:
        """HowTo structured data (JSON-LD) 생성 - AEO 최적화"""
        howto_data = self.seo_data.get("howto", {})

        if not howto_data:
            logger.debug(f"No HowTo data configured for locale '{self.locale}', skipping HowTo schema generation")
            return ""

        schema = {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": howto_data.get("name", ""),
            "description": howto_data.get("description", ""),
            "image": howto_data.get("image", "/static/images/howto.jpg"),
            "totalTime": howto_data.get("totalTime", "PT10M"),
            "supply": [
                {
                    "@type": "HowToSupply",
                    "name": item
                }
                for item in howto_data.get("supplies", [])
            ],
            "tool": [
                {
                    "@type": "HowToTool",
                    "name": item
                }
                for item in howto_data.get("tools", [])
            ],
            "step": [
                {
                    "@type": "HowToStep",
                    "position": idx + 1,
                    "name": step.get("name", ""),
                    "text": step.get("text", ""),
                    "image": step.get("image", "")
                }
                for idx, step in enumerate(howto_data.get("steps", []))
            ]
        }

        return self._json_ld_script(schema)

    def generate_complete_seo_head(
        self,
        page: str = "home",
        page_path: str = "/",
        include_faq: bool = False,
        custom_image: Optional[str] = None
    ) -> str:
        """완전한 SEO head 섹션 생성 (meta tags + hreflang + structured data)"""
        components = [
            self.generate_hreflang_tags(page_path),
            self.generate_meta_tags(page),
            self.generate_opengraph_tags(page, custom_image),
            self.generate_twitter_cards(page, custom_image),
            self.generate_all_schemas(page, include_faq),
        ]

        return "\n    ".join(components)


    def generate_speakable_schema(self, page: str = "home") -> str:
        """
        Speakable structured data (JSON-LD) 생성 - 음성 검색 최적화 (AEO)

        Google Assistant, Alexa 등 음성 비서가 읽을 수 있는 콘텐츠 마크업
        """
        meta = self.get_page_metadata(page)
        site = self.seo_data.get("site", {})

        schema = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": meta["title"],
            "speakable": {
                "@type": "SpeakableSpecification",
                "cssSelector": [
                    ".hero-title",
                    ".hero-subtitle",
                    ".feature-title",
                    ".section-header h2",
                    ".faq-answer"
                ]
            },
            "url": meta["url"]
        }

        return self._json_ld_script(schema)

    def generate_itemlist_schema(self, items: List[Dict[str, Any]], list_type: str = "ItemList") -> str:
        """
        ItemList structured data (JSON-LD) 생성 - 목록 콘텐츠 최적화 (GEO)

        AI 검색 엔진이 목록 형태의 콘텐츠를 더 잘 이해하도록 마크업
        """
        schema = {
            "@context": "https://schema.org",
            "@type": list_type,
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": idx + 1,
                    "name": item.get("name", ""),
                    "description": item.get("description", ""),
                    "url": item.get("url", "")
                }
                for idx, item in enumerate(items)
            ]
        }

        return self._json_ld_script(schema)

    def generate_service_schema(self) -> str:
        """
        Service structured data (JSON-LD) 생성 - 서비스 정보 최적화 (GEO)

        AI가 서비스 정보를 정확하게 이해하고 인용할 수 있도록 마크업
        """
        site = self.seo_data.get("site", {})
        org = self.seo_data.get("organization", {})

        schema = {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": "Creator Control Center",
            "description": site.get("description", ""),
            "provider": {
                "@type": "Organization",
                "name": org.get("name", "Creator Control Center"),
                "url": site.get("url", "")
            },
            "serviceType": "SaaS Analytics Platform",
            "areaServed": {
                "@type": "Country",
                "name": "Worldwide"
            },
            "hasOfferCatalog": {
                "@type": "OfferCatalog",
                "name": "Creator Control Center Plans",
                "itemListElement": [
                    {
                        "@type": "Offer",
                        "name": "Free Plan",
                        "description": "1 channel, basic analytics",
                        "price": "0",
                        "priceCurrency": "USD"
                    },
                    {
                        "@type": "Offer",
                        "name": "Personal Plus",
                        "description": "5 channels, AI features, advanced analytics",
                        "price": "29.90",
                        "priceCurrency": "USD"
                    },
                    {
                        "@type": "Offer",
                        "name": "Enterprise",
                        "description": "Unlimited channels, team management, API access",
                        "price": "119.00",
                        "priceCurrency": "USD"
                    }
                ]
            }
        }

        return self._json_ld_script(schema)

    def generate_definedterm_schema(self, terms: List[Dict[str, str]]) -> str:
        """
        DefinedTerm structured data (JSON-LD) 생성 - 용어 정의 최적화 (AEO)

        AI가 전문 용어와 그 정의를 명확하게 이해하도록 마크업
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "DefinedTermSet",
            "name": "Creator Control Center Glossary",
            "hasDefinedTerm": [
                {
                    "@type": "DefinedTerm",
                    "name": term.get("term", ""),
                    "description": term.get("definition", "")
                }
                for term in terms
            ]
        }

        return self._json_ld_script(schema)

    def generate_claim_review_schema(self, claims: List[Dict[str, Any]]) -> str:
        """
        ClaimReview structured data (JSON-LD) 생성 - 신뢰성 강화 (GEO/E-E-A-T)

        AI가 정보의 신뢰성을 평가할 수 있도록 마크업
        """
        site = self.seo_data.get("site", {})

        schema_list = []
        for claim in claims:
            schema = {
                "@context": "https://schema.org",
                "@type": "ClaimReview",
                "claimReviewed": claim.get("claim", ""),
                "reviewRating": {
                    "@type": "Rating",
                    "ratingValue": claim.get("rating", 5),
                    "bestRating": 5,
                    "worstRating": 1,
                    "alternateName": claim.get("verdict", "True")
                },
                "author": {
                    "@type": "Organization",
                    "name": "Creator Control Center"
                },
                "url": claim.get("url", site.get("url", ""))
            }
            schema_list.append(self._json_ld_script(schema))

        return "\n    ".join(schema_list)

    def generate_aeo_optimized_content(self, page: str = "home") -> str:
        """
        AEO (Answer Engine Optimization) 최적화된 모든 스키마 생성

        AI 답변 엔진(ChatGPT, Perplexity, Google AI Overview 등)에 최적화
        """
        schemas = [
            self.generate_speakable_schema(page),
            self.generate_faq_schema(),
            self.generate_howto_schema(),
        ]

        # Filter out empty schemas
        schemas = [s for s in schemas if s]

        return "\n    ".join(schemas)

    def generate_geo_optimized_content(self, page: str = "home") -> str:
        """
        GEO (Generative Engine Optimization) 최적화된 모든 스키마 생성

        생성형 AI 검색 엔진에 최적화된 구조화된 데이터
        """
        schemas = [
            self.generate_service_schema(),
            self.generate_article_schema(page),
        ]

        # Add defined terms for educational content
        terms = [
            {"term": "Creator Economy", "definition": "The economic ecosystem built around independent content creators who monetize their content and audience."},
            {"term": "Multi-Channel Network (MCN)", "definition": "Organizations that work with video platforms to offer content creators assistance with programming, funding, promotion, and audience development."},
            {"term": "Social Media Analytics", "definition": "The practice of gathering data from social media platforms and analyzing it to make business decisions."},
            {"term": "AI Performance Director", "definition": "An AI-powered tool that analyzes all channel data in real-time and provides actionable weekly recommendations."},
        ]
        schemas.append(self.generate_definedterm_schema(terms))

        # Filter out empty schemas
        schemas = [s for s in schemas if s]

        return "\n    ".join(schemas)

    def generate_complete_optimization(
        self,
        page: str = "home",
        page_path: str = "/",
        include_aeo: bool = True,
        include_geo: bool = True,
        custom_image: Optional[str] = None
    ) -> str:
        """
        SEO + AEO + GEO 완전한 최적화 head 섹션 생성

        모든 검색 엔진과 AI 시스템에 최적화된 메타데이터
        """
        components = [
            self.generate_hreflang_tags(page_path),
            self.generate_meta_tags(page),
            self.generate_opengraph_tags(page, custom_image),
            self.generate_twitter_cards(page, custom_image),
            self.generate_all_schemas(page, include_faq=(page == "support")),
        ]

        if include_aeo:
            aeo_content = self.generate_aeo_optimized_content(page)
            if aeo_content:
                components.append(aeo_content)

        if include_geo:
            geo_content = self.generate_geo_optimized_content(page)
            if geo_content:
                components.append(geo_content)

        return "\n    ".join(components)


def get_seo_service(locale: str = "ko") -> SEOService:
    """SEO 서비스 인스턴스 반환"""
    return SEOService(locale=locale)
