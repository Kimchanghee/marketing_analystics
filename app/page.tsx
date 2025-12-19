"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Globe, ChevronRight, BarChart3, Users, Shield, FileText, CreditCard } from "lucide-react"
import { translations } from "@/lib/translations"

type Language = "en" | "ja" | "ko"

// Cookie utility functions
function setCookie(name: string, value: string, days: number = 365) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString()
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`
}

function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) {
    const part = parts.pop()
    if (part) {
      return decodeURIComponent(part.split(";").shift() || "")
    }
  }
  return null
}

export default function LandingPage() {
  const [lang, setLang] = useState<Language>("en")

  // Initialize language from cookie or browser preference
  useEffect(() => {
    const savedLang = getCookie("lang") as Language | null
    if (savedLang && ["en", "ja", "ko"].includes(savedLang)) {
      setLang(savedLang)
    } else {
      // Check browser language preference
      const browserLang = navigator.language.slice(0, 2)
      if (browserLang === "ja") setLang("ja")
      else if (browserLang === "ko") setLang("ko")
    }
  }, [])

  // Update cookie when language changes
  const handleLanguageChange = (newLang: Language) => {
    setLang(newLang)
    setCookie("lang", newLang)
  }
  const t = translations[lang]

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                <BarChart3 className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="text-lg font-semibold">{t.app.title}</span>
            </div>

            <div className="flex items-center gap-6">
              <a
                href="#features"
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                {t.nav.services}
              </a>
              <a
                href="#pricing"
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                {t.nav.personal}
              </a>
              <a
                href="#testimonials"
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                {t.nav.business}
              </a>

              {/* Language Switcher */}
              <div className="flex items-center gap-1 border border-border rounded-lg p-1">
                <button
                  onClick={() => handleLanguageChange("en")}
                  className={`px-2 py-1 text-xs font-medium rounded transition-colors ${
                    lang === "en" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  EN
                </button>
                <button
                  onClick={() => handleLanguageChange("ja")}
                  className={`px-2 py-1 text-xs font-medium rounded transition-colors ${
                    lang === "ja" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  日本語
                </button>
                <button
                  onClick={() => handleLanguageChange("ko")}
                  className={`px-2 py-1 text-xs font-medium rounded transition-colors ${
                    lang === "ko" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  한국어
                </button>
              </div>

              <Link href="/login">
                <Button variant="outline" size="sm">
                  {t.auth.login_button}
                </Button>
              </Link>
              <Link href="/signup">
                <Button size="sm">{t.landing.cta_creator}</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <Badge variant="secondary" className="w-fit">
                <Globe className="h-3 w-3 mr-2" />
                {t.landing.platforms.youtube} · {t.landing.platforms.instagram} · {t.landing.platforms.tiktok}
              </Badge>

              <h1 className="text-5xl md:text-6xl font-bold leading-tight text-balance">{t.landing.headline}</h1>

              <p className="text-xl text-muted-foreground leading-relaxed text-pretty">{t.landing.subheadline}</p>

              <div className="space-y-3">
                {t.landing.hero_highlights.map((highlight, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                      <ChevronRight className="h-4 w-4 text-primary" />
                    </div>
                    <p className="text-muted-foreground leading-relaxed">{highlight}</p>
                  </div>
                ))}
              </div>

              <div className="flex flex-wrap gap-4">
                <Link href="/signup">
                  <Button size="lg" className="gap-2">
                    {t.landing.cta_creator}
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </Link>
                <Link href="/business">
                  <Button size="lg" variant="outline">
                    {t.landing.cta_manager}
                  </Button>
                </Link>
              </div>
            </div>

            {/* Dashboard Preview */}
            <div className="relative">
              <Card className="p-6 bg-card border-border shadow-xl">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold">{t.landing.preview_title}</h3>
                    <Badge variant="secondary" className="text-xs">
                      {t.landing.mock_metric}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    {t.landing.metrics.map((metric, index) => (
                      <Card key={index} className="p-4 bg-muted/50">
                        <div className="space-y-2">
                          <p className="text-xs text-muted-foreground">{metric.label}</p>
                          <p className="text-2xl font-bold">{metric.value}</p>
                          <p className="text-xs text-muted-foreground leading-relaxed">{metric.description}</p>
                        </div>
                      </Card>
                    ))}
                  </div>

                  <div className="flex flex-wrap gap-2 pt-2">
                    {Object.values(t.landing.platforms)
                      .slice(0, 5)
                      .map((platform, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {platform}
                        </Badge>
                      ))}
                  </div>
                </div>
              </Card>

              {/* Decorative gradient */}
              <div className="absolute -z-10 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary/5 rounded-full blur-3xl" />
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-muted/30 py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16 space-y-4">
            <h2 className="text-4xl font-bold text-balance">{t.landing.feature_section.title}</h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto text-balance">
              {t.landing.feature_section.description}
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {t.landing.feature_section.items.map((item, index) => {
              const icons = [BarChart3, Shield, Users, FileText]
              const Icon = icons[index]

              return (
                <Card key={index} className="p-6 hover:shadow-lg transition-shadow">
                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <Icon className="h-5 w-5 text-primary" />
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {item.tag}
                      </Badge>
                    </div>
                    <h3 className="text-lg font-semibold">{item.title}</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">{item.description}</p>
                  </div>
                </Card>
              )
            })}
          </div>
        </div>
      </section>

      {/* Journey Section */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16 space-y-4">
            <h2 className="text-4xl font-bold text-balance">{t.landing.journey.title}</h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed text-pretty">
              {t.landing.journey.description}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {t.landing.journey.steps.map((step, index) => (
              <Card key={index} className="p-6 relative">
                <div className="space-y-4">
                  <div className="inline-flex items-center justify-center h-12 w-12 rounded-full bg-primary text-primary-foreground font-bold text-lg">
                    {index + 1}
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {step.label}
                  </Badge>
                  <h3 className="text-xl font-semibold">{step.title}</h3>
                  <p className="text-muted-foreground leading-relaxed">{step.description}</p>
                </div>
                {index < 2 && <div className="hidden md:block absolute top-1/2 -right-4 w-8 h-0.5 bg-border" />}
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="bg-muted/30 py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">{t.landing.testimonials_label}</h2>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {t.landing.testimonials.slice(0, 6).map((testimonial, index) => (
              <Card key={index} className="p-6 hover:shadow-lg transition-shadow">
                <div className="space-y-4">
                  <p className="text-muted-foreground leading-relaxed italic">&ldquo;{testimonial.quote}&rdquo;</p>
                  <div className="border-t border-border pt-4">
                    <p className="font-semibold">{testimonial.name}</p>
                    <p className="text-sm text-muted-foreground">{testimonial.title}</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16 space-y-4">
            <h2 className="text-4xl font-bold text-balance">{t.landing.pricing?.title || "Choose Your Plan"}</h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto text-balance">
              {t.landing.pricing?.description || "Start free and scale as you grow. No hidden fees."}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Free Plan */}
            <Card className="p-6 hover:shadow-lg transition-shadow">
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center">
                    <Users className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <Badge variant="secondary" className="text-xs">FREE</Badge>
                </div>
                <h3 className="text-2xl font-bold">{t.landing.pricing?.free?.name || "Starter"}</h3>
                <p className="text-4xl font-bold">$0<span className="text-sm font-normal text-muted-foreground">/mo</span></p>
                <p className="text-sm text-muted-foreground">{t.landing.pricing?.free?.description || "Perfect for getting started"}</p>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-center gap-2">
                    <ChevronRight className="h-4 w-4 text-primary" />
                    {t.landing.pricing?.free?.features?.[0] || "1 channel connection"}
                  </li>
                  <li className="flex items-center gap-2">
                    <ChevronRight className="h-4 w-4 text-primary" />
                    {t.landing.pricing?.free?.features?.[1] || "Basic analytics"}
                  </li>
                  <li className="flex items-center gap-2">
                    <ChevronRight className="h-4 w-4 text-primary" />
                    {t.landing.pricing?.free?.features?.[2] || "7-day data retention"}
                  </li>
                </ul>
                <Link href="/signup" className="block">
                  <Button variant="outline" className="w-full">{t.landing.pricing?.free?.cta || "Get Started"}</Button>
                </Link>
              </div>
            </Card>

            {/* Pro Plan */}
            <Card className="p-6 hover:shadow-lg transition-shadow border-primary relative">
              <Badge className="absolute -top-3 left-1/2 -translate-x-1/2">{t.landing.pricing?.popular || "Most Popular"}</Badge>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <BarChart3 className="h-5 w-5 text-primary" />
                  </div>
                  <Badge variant="default" className="text-xs">PRO</Badge>
                </div>
                <h3 className="text-2xl font-bold">{t.landing.pricing?.pro?.name || "Professional"}</h3>
                <p className="text-4xl font-bold">$29<span className="text-sm font-normal text-muted-foreground">/mo</span></p>
                <p className="text-sm text-muted-foreground">{t.landing.pricing?.pro?.description || "For growing creators"}</p>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-center gap-2">
                    <ChevronRight className="h-4 w-4 text-primary" />
                    {t.landing.pricing?.pro?.features?.[0] || "5 channel connections"}
                  </li>
                  <li className="flex items-center gap-2">
                    <ChevronRight className="h-4 w-4 text-primary" />
                    {t.landing.pricing?.pro?.features?.[1] || "Advanced analytics & AI insights"}
                  </li>
                  <li className="flex items-center gap-2">
                    <ChevronRight className="h-4 w-4 text-primary" />
                    {t.landing.pricing?.pro?.features?.[2] || "30-day data retention"}
                  </li>
                  <li className="flex items-center gap-2">
                    <ChevronRight className="h-4 w-4 text-primary" />
                    {t.landing.pricing?.pro?.features?.[3] || "AI PD Assistant"}
                  </li>
                </ul>
                <Link href="/personal" className="block">
                  <Button className="w-full">{t.landing.pricing?.pro?.cta || "Start Pro Trial"}</Button>
                </Link>
              </div>
            </Card>

            {/* Enterprise Plan */}
            <Card className="p-6 hover:shadow-lg transition-shadow">
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <CreditCard className="h-5 w-5 text-primary" />
                  </div>
                  <Badge variant="outline" className="text-xs">ENTERPRISE</Badge>
                </div>
                <h3 className="text-2xl font-bold">{t.landing.pricing?.enterprise?.name || "Enterprise"}</h3>
                <p className="text-4xl font-bold">{t.landing.pricing?.enterprise?.price || "Custom"}</p>
                <p className="text-sm text-muted-foreground">{t.landing.pricing?.enterprise?.description || "For agencies & teams"}</p>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-center gap-2">
                    <ChevronRight className="h-4 w-4 text-primary" />
                    {t.landing.pricing?.enterprise?.features?.[0] || "Unlimited channels"}
                  </li>
                  <li className="flex items-center gap-2">
                    <ChevronRight className="h-4 w-4 text-primary" />
                    {t.landing.pricing?.enterprise?.features?.[1] || "Team management"}
                  </li>
                  <li className="flex items-center gap-2">
                    <ChevronRight className="h-4 w-4 text-primary" />
                    {t.landing.pricing?.enterprise?.features?.[2] || "Custom integrations"}
                  </li>
                  <li className="flex items-center gap-2">
                    <ChevronRight className="h-4 w-4 text-primary" />
                    {t.landing.pricing?.enterprise?.features?.[3] || "Priority support"}
                  </li>
                </ul>
                <Link href="/business" className="block">
                  <Button variant="outline" className="w-full">{t.landing.pricing?.enterprise?.cta || "Contact Sales"}</Button>
                </Link>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <Card className="p-12 text-center bg-primary/5 border-primary/20">
            <div className="max-w-2xl mx-auto space-y-6">
              <h2 className="text-4xl font-bold text-balance">{t.landing.cta.title}</h2>
              <p className="text-xl text-muted-foreground text-balance">{t.landing.cta.description}</p>
              <div className="flex flex-wrap justify-center gap-4 pt-4">
                <Link href="/signup">
                  <Button size="lg" className="gap-2">
                    {t.landing.cta.primary}
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </Link>
                <Link href="/login">
                  <Button size="lg" variant="outline">
                    {t.landing.cta.secondary}
                  </Button>
                </Link>
              </div>
            </div>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid md:grid-cols-4 gap-8">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                  <BarChart3 className="h-5 w-5 text-primary-foreground" />
                </div>
                <span className="font-semibold">{t.app.title}</span>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">{t.footer.tagline}</p>
            </div>

            <div className="space-y-4">
              <h3 className="font-semibold">{t.footer.product}</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link href="/services" className="hover:text-foreground transition-colors">{t.nav.services}</Link></li>
                <li><Link href="/personal" className="hover:text-foreground transition-colors">{t.nav.personal}</Link></li>
                <li><Link href="/business" className="hover:text-foreground transition-colors">{t.nav.business}</Link></li>
              </ul>
            </div>

            <div className="space-y-4">
              <h3 className="font-semibold">{t.footer.support}</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link href="/support" className="hover:text-foreground transition-colors">{t.nav.support}</Link></li>
                <li><Link href="/dashboard" className="hover:text-foreground transition-colors">{t.nav.dashboard}</Link></li>
              </ul>
            </div>

            <div className="space-y-4">
              <h3 className="font-semibold">{t.footer.contact}</h3>
              <p className="text-sm text-muted-foreground">{t.footer.contact}</p>
            </div>
          </div>

          <div className="border-t border-border mt-12 pt-8 text-center text-sm text-muted-foreground">
            {t.footer.note}
          </div>
        </div>
      </footer>
    </div>
  )
}
