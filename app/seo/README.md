# SEO & AEO Optimization

Creator Control Center의 검색 엔진 최적화 (SEO) 및 Answer Engine 최적화 (AEO) 모듈입니다.

## 2025 최신 SEO/AEO 모범 사례 적용

이 모듈은 Google AI Overviews, ChatGPT, Bing Copilot 등 최신 AI 검색 엔진에 최적화되어 있습니다.

### 주요 기능

1. **Structured Data (JSON-LD)**
   - Organization Schema
   - WebSite Schema
   - WebPage Schema
   - FAQPage Schema (AEO 최적화)
   - SoftwareApplication Schema
   - BreadcrumbList Schema

2. **Meta Tags**
   - Title, Description, Keywords
   - Robots, Googlebot, Bingbot 메타 태그
   - Canonical URL

3. **Social Media Optimization**
   - OpenGraph (Facebook, LinkedIn 등)
   - Twitter Cards

4. **다국어 지원**
   - 한국어 (ko)
   - 영어 (en)
   - 일본어 (ja)

5. **Sitemap & Robots.txt**
   - 동적 sitemap.xml 생성
   - 다국어 hreflang 지원
   - robots.txt 제공

## 폴더 구조

```
app/seo/
├── __init__.py              # 패키지 초기화
├── seo_service.py           # SEO 서비스 메인 로직
├── sitemap_generator.py     # Sitemap & Robots.txt 생성
├── locales/                 # 언어별 SEO 메타데이터
│   ├── ko.json             # 한국어
│   ├── en.json             # 영어
│   └── ja.json             # 일본어
└── README.md               # 이 파일
```

## 사용 방법

### 1. 기본 사용법

```python
from app.seo import get_seo_service

# SEO 서비스 인스턴스 생성
seo = get_seo_service(locale="ko")

# 페이지별 메타데이터 조회
meta = seo.get_page_metadata("home")

# 완전한 SEO head 섹션 생성
seo_head = seo.generate_complete_seo_head(
    page="home",
    include_faq=True,
    custom_image="/path/to/image.jpg"
)
```

### 2. FastAPI 라우터에서 사용

```python
@app.get("/")
async def landing(request: Request):
    locale = getattr(request.state, "locale", "ko")
    seo_service = get_seo_service(locale)

    return app.state.templates.TemplateResponse(
        "landing.html",
        {
            "request": request,
            "seo": seo_service,
            "page": "home",
        },
    )
```

### 3. Jinja2 템플릿에서 사용

```html
<head>
    {% if seo is defined and page is defined %}
    {# SEO Meta Tags #}
    <title>{{ seo.get_page_metadata(page)['title'] }}</title>
    {{ seo.generate_meta_tags(page)|safe }}

    {# OpenGraph Tags #}
    {{ seo.generate_opengraph_tags(page)|safe }}

    {# Twitter Cards #}
    {{ seo.generate_twitter_cards(page)|safe }}

    {# Structured Data #}
    {{ seo.generate_all_schemas(page, include_faq=True)|safe }}
    {% endif %}
</head>
```

## 지원 페이지

다음 페이지들에 대한 SEO 메타데이터가 정의되어 있습니다:

- `home` - 홈/랜딩 페이지
- `services` - 서비스 소개
- `personal` - 개인 크리에이터 솔루션
- `business` - 기업/에이전시 솔루션
- `support` - 고객 지원 (FAQ 포함)
- `dashboard` - 대시보드

## SEO 메타데이터 추가/수정

새로운 페이지의 SEO 메타데이터를 추가하거나 기존 메타데이터를 수정하려면:

1. `app/seo/locales/` 폴더의 언어별 JSON 파일 편집
2. `pages` 섹션에 새 페이지 추가

예시:
```json
{
  "pages": {
    "new_page": {
      "title": "새 페이지 제목 - Creator Control Center",
      "description": "새 페이지에 대한 설명입니다.",
      "keywords": "키워드1, 키워드2, 키워드3",
      "og_type": "website"
    }
  }
}
```

## Answer Engine Optimization (AEO)

AEO는 AI 기반 검색 엔진 (ChatGPT, Google SGE, Bing Copilot)에서 답변으로 노출되도록 최적화하는 기법입니다.

### AEO 최적화 요소

1. **FAQPage Schema**: support 페이지에 FAQ 구조화 데이터 자동 포함
2. **명확한 답변 구조**: 질문-답변 형식의 명확한 콘텐츠
3. **Structured Data**: 기계가 읽을 수 있는 JSON-LD 형식
4. **권위성**: Organization schema로 브랜드 신뢰도 구축

### FAQ 관리

`locales/*.json` 파일의 `faq` 섹션에서 FAQ를 관리할 수 있습니다:

```json
{
  "faq": [
    {
      "question": "질문",
      "answer": "답변"
    }
  ]
}
```

## Sitemap & Robots.txt

### Sitemap 접근

- URL: `/sitemap.xml`
- 동적 생성
- 다국어 hreflang 지원
- 모든 공개 페이지 포함

### Robots.txt 접근

- URL: `/robots.txt`
- 크롤링 허용/차단 규칙
- Sitemap 위치 명시
- 주요 검색 엔진별 설정

## 성능 최적화

- JSON 파일은 앱 시작 시 한 번만 로드
- 캐싱 고려 (프로덕션 환경)
- Lazy loading 지원

## 검증 도구

SEO 구현을 검증하려면 다음 도구를 사용하세요:

1. **Google Rich Results Test**: https://search.google.com/test/rich-results
2. **Schema.org Validator**: https://validator.schema.org/
3. **Google Search Console**: https://search.google.com/search-console
4. **Facebook Sharing Debugger**: https://developers.facebook.com/tools/debug/
5. **Twitter Card Validator**: https://cards-dev.twitter.com/validator

## 참고 자료

- [Google Search Central - Structured Data](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data)
- [Schema.org Documentation](https://schema.org/)
- [Answer Engine Optimization Guide 2025](https://cxl.com/blog/answer-engine-optimization-aeo-the-comprehensive-guide-for-2025/)
- [JSON-LD Best Practices](https://w3c.github.io/json-ld-bp/)
