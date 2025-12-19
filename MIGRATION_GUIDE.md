# 프론트엔드 선택 및 마이그레이션 가이드

## 🎯 목적
이 가이드는 FastAPI+Jinja와 Next.js 중 하나를 선택하고, 선택한 스택으로 완전히 전환하는 방법을 설명합니다.

---

## 📊 현재 상태

### FastAPI + Jinja (완성도: 95%)
✅ 구현된 페이지:
- `/` - 랜딩 페이지
- `/login` - 로그인
- `/signup` - 회원가입
- `/services` - 서비스 소개
- `/personal` - 개인 요금제
- `/business` - 기업 요금제
- `/support` - 고객 지원
- `/dashboard` - 사용자 대시보드
- `/channels/manage` - 채널 관리
- `/profile` - 프로필 설정
- `/manager/dashboard` - 기업 관리자 대시보드

### Next.js (완성도: 10%)
✅ 구현된 페이지:
- `/` - 랜딩 페이지만

❌ 미구현 페이지:
- `/login`, `/signup`, `/services`, `/personal`, `/business`, `/support`, `/dashboard` 등 7개+

---

## 🚀 Option A: FastAPI + Jinja로 진행 (권장)

### 장점
- ✅ 즉시 배포 가능
- ✅ 모든 기능 완성
- ✅ 서버 사이드 렌더링 (SEO 우수)
- ✅ 간단한 아키텍처

### 단점
- ⚠️ 전통적인 풀 페이지 리로드
- ⚠️ 제한적인 클라이언트 사이드 인터랙션

### 마이그레이션 단계

#### Step 1: Next.js 디렉토리 정리 (5분)

**Option 1a: 완전 제거**
```bash
# Next.js 관련 파일 삭제
rm -rf app/ components/ lib/translations.ts
rm package.json package-lock.json tsconfig.json next.config.js tailwind.config.ts

# 또는 백업
mkdir _archived_nextjs
mv app/ components/ lib/ package.json _archived_nextjs/
```

**Option 1b: 보관만 (나중에 사용 가능)**
```bash
# .gitignore에 추가하여 무시
echo "app/" >> .gitignore
echo "components/" >> .gitignore
```

#### Step 2: Jinja 템플릿 개선 (선택, 1-2일)

더 나은 UX를 원한다면 Alpine.js나 HTMX 추가:

```bash
pip install htmx
```

`ui/templates/base.html`에 추가:
```html
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
<script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

예시 - 동적 폼 검증:
```html
<form hx-post="/api/validate" hx-trigger="change">
    <input type="email" name="email" required>
    <div hx-target="this" hx-swap="innerHTML"></div>
</form>
```

#### Step 3: 배포 (30분)

**Google Cloud Run (권장):**
```bash
# Dockerfile 생성
cat > Dockerfile <<EOF
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
EOF

# 배포
gcloud run deploy creator-control-center \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

**Heroku:**
```bash
# Procfile 생성
echo "web: uvicorn app.main:app --host 0.0.0.0 --port \$PORT" > Procfile

# 배포
git push heroku main
```

---

## 🎨 Option B: Next.js로 완전 전환 (3-5일 작업)

### 장점
- ✅ 모던 React 기반
- ✅ 빠른 클라이언트 사이드 네비게이션
- ✅ 풍부한 UI 컴포넌트 생태계
- ✅ Vercel 배포 쉬움

### 단점
- ⚠️ 7개+ 페이지 개발 필요
- ⚠️ API 클라이언트 레이어 구축 필요
- ⚠️ 인증 상태 관리 복잡

### 마이그레이션 단계

#### Step 1: 필요한 페이지 생성 (2-3일)

```bash
# 디렉토리 구조
app/
├── page.tsx              # ✅ 이미 존재
├── login/
│   └── page.tsx          # ❌ 생성 필요
├── signup/
│   └── page.tsx          # ❌ 생성 필요
├── services/
│   └── page.tsx          # ❌ 생성 필요
├── personal/
│   └── page.tsx          # ❌ 생성 필요
├── business/
│   └── page.tsx          # ❌ 생성 필요
├── support/
│   └── page.tsx          # ❌ 생성 필요
├── dashboard/
│   └── page.tsx          # ❌ 생성 필요
└── channels/
    └── manage/
        └── page.tsx      # ❌ 생성 필요
```

**예시: app/login/page.tsx**
```tsx
"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    const res = await fetch("http://localhost:8000/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username: email, password }),
      credentials: "include"
    })

    if (res.ok) {
      router.push("/dashboard")
    } else {
      alert("로그인 실패")
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <form onSubmit={handleSubmit} className="w-full max-w-md space-y-4">
        <h1 className="text-2xl font-bold">로그인</h1>
        <Input
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="이메일"
          required
        />
        <Input
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          placeholder="비밀번호"
          required
        />
        <Button type="submit" className="w-full">로그인</Button>
      </form>
    </div>
  )
}
```

#### Step 2: API 클라이언트 레이어 생성 (1일)

```bash
mkdir lib/api
```

**lib/api/client.ts:**
```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  })

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`)
  }

  return res.json()
}

export const api = {
  auth: {
    login: (email: string, password: string) =>
      apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),

    signup: (data: { email: string; password: string; name: string }) =>
      apiRequest("/auth/signup", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },

  channels: {
    list: () => apiRequest("/channels"),
    create: (data: any) => apiRequest("/channels", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  },
}
```

#### Step 3: 인증 상태 관리 (1일)

**lib/auth-context.tsx:**
```tsx
"use client"

import { createContext, useContext, useState, useEffect } from "react"
import { api } from "./api/client"

interface User {
  id: number
  email: string
  name: string
}

interface AuthContext {
  user: User | null
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  isLoading: boolean
}

const AuthContext = createContext<AuthContext | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // 페이지 로드 시 사용자 정보 가져오기
    fetch("/api/me", { credentials: "include" })
      .then(res => res.ok ? res.json() : null)
      .then(setUser)
      .finally(() => setIsLoading(false))
  }, [])

  async function login(email: string, password: string) {
    const userData = await api.auth.login(email, password)
    setUser(userData)
  }

  async function logout() {
    await fetch("/auth/logout", { method: "POST", credentials: "include" })
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error("useAuth must be used within AuthProvider")
  return context
}
```

#### Step 4: Jinja 템플릿 제거 (30분)

```bash
# 백업
mkdir _archived_jinja
mv ui/ _archived_jinja/

# 또는 완전 삭제
rm -rf ui/
```

#### Step 5: 배포 (30분)

**Vercel (가장 쉬움):**
```bash
npm install -g vercel
vercel

# 환경 변수 설정
vercel env add NEXT_PUBLIC_API_URL production
# 값 입력: https://your-api.com
```

**환경 변수 설정:**
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000  # 개발
# NEXT_PUBLIC_API_URL=https://api.your-domain.com  # 프로덕션
```

---

## 🔄 Option C: 하이브리드 (비권장)

### 구조
- **마케팅 페이지** (/, /services, /pricing): Next.js
- **인증 페이지** (/login, /signup, /dashboard): FastAPI + Jinja

### 설정

**next.config.js:**
```javascript
module.exports = {
  async rewrites() {
    return [
      {
        source: '/login',
        destination: 'http://localhost:8000/login',
      },
      {
        source: '/signup',
        destination: 'http://localhost:8000/signup',
      },
      {
        source: '/dashboard/:path*',
        destination: 'http://localhost:8000/dashboard/:path*',
      },
    ]
  },
}
```

### 단점
- ⚠️ 복잡한 라우팅
- ⚠️ 일관성 없는 UX
- ⚠️ 유지보수 어려움
- ⚠️ 두 개의 배포 파이프라인

---

## 📊 의사결정 매트릭스

| 기준 | FastAPI+Jinja | Next.js | 하이브리드 |
|------|---------------|---------|-----------|
| 즉시 배포 가능성 | ⭐⭐⭐⭐⭐ | ⭐☆☆☆☆ | ⭐⭐☆☆☆ |
| 개발 속도 | ⭐⭐⭐⭐⭐ | ⭐⭐☆☆☆ | ⭐⭐☆☆☆ |
| 모던한 UX | ⭐⭐☆☆☆ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐☆☆ |
| SEO | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐☆ | ⭐⭐⭐⭐☆ |
| 유지보수 | ⭐⭐⭐⭐☆ | ⭐⭐⭐⭐☆ | ⭐⭐☆☆☆ |
| 학습 곡선 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐☆☆ | ⭐⭐☆☆☆ |

---

## 🎯 권장 사항

### 다음 경우 FastAPI + Jinja 선택:
- ✅ 1-2주 내 런칭 필요
- ✅ 팀에 React 개발자 없음
- ✅ B2B SaaS (복잡한 UI 불필요)
- ✅ 서버 리소스가 충분함

### 다음 경우 Next.js 선택:
- ✅ 2-4주 개발 기간 확보
- ✅ 팀에 React 개발자 있음
- ✅ B2C 제품 (인터랙티브 UI 중요)
- ✅ 장기적 투자 가능

### 하이브리드는 선택하지 마세요:
- ❌ 복잡도만 증가
- ❌ 유지보수 어려움
- ❌ 성능 이점 없음

---

## 📞 추가 리소스

- **FastAPI 문서:** https://fastapi.tiangolo.com/
- **Jinja2 문서:** https://jinja.palletsprojects.com/
- **Next.js 문서:** https://nextjs.org/docs
- **HTMX (Jinja 개선):** https://htmx.org/
- **Alpine.js (Jinja 개선):** https://alpinejs.dev/

---

**최종 결정을 내렸다면:**
- FastAPI 선택 → 이 파일의 "Option A" 섹션 따라하기
- Next.js 선택 → 이 파일의 "Option B" 섹션 따라하기

**예상 완료 시간:**
- FastAPI 전환: 1일
- Next.js 전환: 3-5일
