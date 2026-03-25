"use client";

import { useState, useEffect, useRef } from "react";
import { motion, useInView, AnimatePresence } from "framer-motion";
import {
  Zap,
  BarChart3,
  Shield,
  ArrowRight,
  Star,
  Check,
  Menu,
  X,
  Moon,
  Sun,
  Sparkles,
  Globe,
  Clock,
  Users,
  ChevronRight,
} from "lucide-react";

// --- Intersection Observer Fade-in ---
function FadeIn({ children, delay = 0, className = "" }: { children: React.ReactNode; delay?: number; className?: string }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-60px" });
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 24 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, delay, ease: "easeOut" }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// --- Nav ---
function Nav({ dark, setDark }: { dark: boolean; setDark: (v: boolean) => void }) {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handler, { passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, []);

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-white/80 dark:bg-gray-950/80 backdrop-blur-xl border-b border-gray-200 dark:border-gray-800"
          : "bg-transparent"
      }`}
      role="navigation"
      aria-label="メインナビゲーション"
    >
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <a href="#" className="flex items-center gap-2 text-xl font-bold">
          <Sparkles className="h-6 w-6 text-blue-500" />
          <span className="text-gray-900 dark:text-white">FlowSync</span>
        </a>

        {/* Desktop links */}
        <div className="hidden items-center gap-8 md:flex">
          {["機能", "料金", "導入事例", "FAQ"].map((item) => (
            <a
              key={item}
              href={`#${item}`}
              className="text-sm font-medium text-gray-600 transition-colors duration-150 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
            >
              {item}
            </a>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setDark(!dark)}
            className="flex h-9 w-9 items-center justify-center rounded-lg transition-colors duration-150 hover:bg-gray-100 dark:hover:bg-gray-800 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500"
            aria-label={dark ? "ライトモードに切替" : "ダークモードに切替"}
          >
            {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>

          <a
            href="#cta"
            className="hidden rounded-full bg-blue-500 px-5 py-2 text-sm font-semibold text-white transition-all duration-150 hover:bg-blue-600 active:scale-95 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 md:inline-flex"
          >
            無料で始める
          </a>

          {/* Mobile menu */}
          <button
            onClick={() => setOpen(!open)}
            className="flex h-9 w-9 items-center justify-center rounded-lg md:hidden hover:bg-gray-100 dark:hover:bg-gray-800 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500"
            aria-label="メニュー"
            aria-expanded={open}
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu panel */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="border-b border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-950 md:hidden"
          >
            <div className="flex flex-col gap-1 px-6 py-4">
              {["機能", "料金", "導入事例", "FAQ"].map((item) => (
                <a
                  key={item}
                  href={`#${item}`}
                  onClick={() => setOpen(false)}
                  className="rounded-lg px-3 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
                >
                  {item}
                </a>
              ))}
              <a
                href="#cta"
                className="mt-2 rounded-full bg-blue-500 px-5 py-2.5 text-center text-sm font-semibold text-white"
              >
                無料で始める
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}

// --- Hero ---
function Hero() {
  return (
    <section className="relative flex min-h-screen items-center justify-center overflow-hidden px-6 pt-16">
      {/* Background gradient */}
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-blue-50 via-white to-white dark:from-blue-950/20 dark:via-gray-950 dark:to-gray-950" />
      <div className="pointer-events-none absolute top-0 left-1/2 -translate-x-1/2 h-[600px] w-[800px] rounded-full bg-blue-400/10 blur-3xl dark:bg-blue-500/5" />

      <div className="relative z-10 mx-auto max-w-3xl text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-3.5 py-1 text-xs font-semibold text-blue-600 dark:bg-blue-500/10 dark:text-blue-400 mb-6">
            <Sparkles className="h-3.5 w-3.5" />
            新機能: AIアシスタント搭載
          </span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="mt-6 text-5xl font-extrabold leading-tight tracking-tight text-gray-900 dark:text-white sm:text-6xl lg:text-7xl"
        >
          チームの生産性が
          <span className="bg-gradient-to-r from-blue-500 to-violet-500 bg-clip-text text-transparent">
            3倍になる
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mt-6 text-lg leading-relaxed text-gray-600 dark:text-gray-400 sm:text-xl"
        >
          タスク管理・ドキュメント・コミュニケーションを
          <br className="hidden sm:block" />
          ひとつのワークスペースに統合。AIが最適な進め方を提案します。
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center"
        >
          <a
            href="#cta"
            className="group inline-flex items-center gap-2 rounded-full bg-blue-500 px-7 py-3.5 text-sm font-semibold text-white shadow-lg shadow-blue-500/25 transition-all duration-150 hover:bg-blue-600 hover:shadow-blue-500/40 active:scale-95 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500"
          >
            無料で試す
            <ArrowRight className="h-4 w-4 transition-transform duration-150 group-hover:translate-x-0.5" />
          </a>
          <a
            href="#機能"
            className="inline-flex items-center gap-2 rounded-full border border-gray-300 px-7 py-3.5 text-sm font-semibold text-gray-700 transition-all duration-150 hover:border-gray-400 hover:bg-gray-50 active:scale-95 dark:border-gray-700 dark:text-gray-300 dark:hover:border-gray-600 dark:hover:bg-gray-800/50 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500"
          >
            機能を見る
          </a>
        </motion.div>

        {/* Social proof */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="mt-14 flex flex-col items-center gap-3"
        >
          <div className="flex -space-x-2">
            {["bg-pink-400", "bg-amber-400", "bg-emerald-400", "bg-violet-400", "bg-sky-400"].map((c, i) => (
              <div key={i} className={`h-8 w-8 rounded-full ${c} border-2 border-white dark:border-gray-950 flex items-center justify-center text-xs font-bold text-white`}>
                {String.fromCharCode(65 + i)}
              </div>
            ))}
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-500">
            <span className="font-semibold text-gray-700 dark:text-gray-300">2,400+社</span>が導入済み
          </p>
        </motion.div>
      </div>
    </section>
  );
}

// --- Features ---
const features = [
  {
    icon: Zap,
    title: "リアルタイム同期",
    desc: "チーム全員の変更が即座に反映。コンフリクトのない共同作業を実現します。",
    color: "text-amber-500 bg-amber-50 dark:bg-amber-500/10",
  },
  {
    icon: BarChart3,
    title: "AIインサイト",
    desc: "プロジェクトの進捗をAIが分析。ボトルネックを自動で検出し改善策を提案します。",
    color: "text-blue-500 bg-blue-50 dark:bg-blue-500/10",
  },
  {
    icon: Shield,
    title: "エンタープライズセキュリティ",
    desc: "SOC2 Type II準拠。データは暗号化され、アクセス権限を細かく制御できます。",
    color: "text-emerald-500 bg-emerald-50 dark:bg-emerald-500/10",
  },
  {
    icon: Globe,
    title: "グローバル対応",
    desc: "12言語対応、世界中のチームと自然にコラボレーション。タイムゾーン管理も自動。",
    color: "text-violet-500 bg-violet-50 dark:bg-violet-500/10",
  },
  {
    icon: Clock,
    title: "自動ワークフロー",
    desc: "繰り返しタスクを自動化。トリガーとアクションを組み合わせて業務を効率化。",
    color: "text-rose-500 bg-rose-50 dark:bg-rose-500/10",
  },
  {
    icon: Users,
    title: "柔軟なチーム管理",
    desc: "部門・プロジェクト・ロール別にチームを構成。権限管理も直感的に設定可能。",
    color: "text-sky-500 bg-sky-50 dark:bg-sky-500/10",
  },
];

function Features() {
  return (
    <section id="機能" className="py-24 px-6">
      <div className="mx-auto max-w-6xl">
        <FadeIn className="text-center">
          <span className="text-sm font-semibold uppercase tracking-wider text-blue-500">Features</span>
          <h2 className="mt-3 text-3xl font-bold text-gray-900 dark:text-white sm:text-4xl">
            すべてが揃ったワークスペース
          </h2>
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            チームが最高のパフォーマンスを発揮するために必要な機能をすべて搭載
          </p>
        </FadeIn>

        <div className="mt-16 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => (
            <FadeIn key={f.title} delay={i * 0.08}>
              <div className="group rounded-2xl border border-gray-200 bg-white p-7 transition-all duration-200 hover:border-gray-300 hover:shadow-lg hover:shadow-gray-200/50 dark:border-gray-800 dark:bg-gray-900 dark:hover:border-gray-700 dark:hover:shadow-gray-900/50">
                <div className={`inline-flex h-11 w-11 items-center justify-center rounded-xl ${f.color}`}>
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="mt-5 text-lg font-semibold text-gray-900 dark:text-white">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-600 dark:text-gray-400">{f.desc}</p>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}

// --- Stats ---
function Stats() {
  return (
    <section className="border-y border-gray-200 bg-gray-50 py-16 px-6 dark:border-gray-800 dark:bg-gray-900/50">
      <div className="mx-auto grid max-w-5xl grid-cols-2 gap-8 sm:grid-cols-4">
        {[
          { value: "2,400+", label: "導入企業" },
          { value: "99.99%", label: "稼働率" },
          { value: "150万+", label: "月間タスク処理" },
          { value: "4.9/5", label: "顧客満足度" },
        ].map((s, i) => (
          <FadeIn key={s.label} delay={i * 0.1} className="text-center">
            <p className="text-3xl font-extrabold text-gray-900 dark:text-white sm:text-4xl">{s.value}</p>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{s.label}</p>
          </FadeIn>
        ))}
      </div>
    </section>
  );
}

// --- Testimonials ---
const testimonials = [
  {
    name: "山田 智子",
    role: "CTO / TechVenture Inc.",
    text: "FlowSyncを導入してからチームの生産性が劇的に向上しました。特にAIインサイト機能が素晴らしく、プロジェクトのボトルネックを事前に把握できるようになりました。",
    avatar: "T",
    color: "bg-pink-400",
  },
  {
    name: "佐々木 健太",
    role: "プロダクトマネージャー / StartupLab",
    text: "以前は5つのツールを使い分けていましたが、FlowSyncひとつで完結するようになりました。チームのオンボーディングも2日で完了するほど直感的です。",
    avatar: "K",
    color: "bg-blue-400",
  },
  {
    name: "李 美玲",
    role: "デザインリード / CreativeStudio",
    text: "リアルタイム同期のおかげで、リモートチームとの協業がスムーズになりました。デザインレビューのサイクルが50%短縮されています。",
    avatar: "M",
    color: "bg-emerald-400",
  },
];

function Testimonials() {
  return (
    <section id="導入事例" className="py-24 px-6">
      <div className="mx-auto max-w-6xl">
        <FadeIn className="text-center">
          <span className="text-sm font-semibold uppercase tracking-wider text-blue-500">Testimonials</span>
          <h2 className="mt-3 text-3xl font-bold text-gray-900 dark:text-white sm:text-4xl">
            お客様の声
          </h2>
        </FadeIn>

        <div className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-3">
          {testimonials.map((t, i) => (
            <FadeIn key={t.name} delay={i * 0.1}>
              <div className="flex h-full flex-col rounded-2xl border border-gray-200 bg-white p-7 dark:border-gray-800 dark:bg-gray-900">
                <div className="mb-4 flex gap-1">
                  {[...Array(5)].map((_, j) => (
                    <Star key={j} className="h-4 w-4 fill-amber-400 text-amber-400" />
                  ))}
                </div>
                <p className="flex-1 text-sm leading-relaxed text-gray-600 dark:text-gray-400">"{t.text}"</p>
                <div className="mt-6 flex items-center gap-3 border-t border-gray-100 pt-5 dark:border-gray-800">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-full ${t.color} text-sm font-bold text-white`}>
                    {t.avatar}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">{t.name}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{t.role}</p>
                  </div>
                </div>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}

// --- Pricing ---
const plans = [
  {
    name: "Starter",
    price: "¥0",
    period: "永久無料",
    desc: "小規模チームに最適",
    features: ["5名まで", "基本タスク管理", "1GBストレージ", "メールサポート"],
    cta: "無料で始める",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "¥1,980",
    period: "/ ユーザー / 月",
    desc: "成長するチームに",
    features: ["無制限メンバー", "AIインサイト", "100GBストレージ", "優先サポート", "自動ワークフロー", "API連携"],
    cta: "14日間無料で試す",
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: "お問い合わせ",
    period: "",
    desc: "大規模組織向け",
    features: ["全Pro機能", "SSO / SAML", "無制限ストレージ", "専任サポート", "SLA保証", "カスタム連携"],
    cta: "営業に相談する",
    highlighted: false,
  },
];

function Pricing() {
  return (
    <section id="料金" className="py-24 px-6 bg-gray-50 dark:bg-gray-900/50">
      <div className="mx-auto max-w-6xl">
        <FadeIn className="text-center">
          <span className="text-sm font-semibold uppercase tracking-wider text-blue-500">Pricing</span>
          <h2 className="mt-3 text-3xl font-bold text-gray-900 dark:text-white sm:text-4xl">
            シンプルな料金体系
          </h2>
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            14日間の無料トライアル。クレジットカード不要。
          </p>
        </FadeIn>

        <div className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-3">
          {plans.map((p, i) => (
            <FadeIn key={p.name} delay={i * 0.1}>
              <div
                className={`relative flex h-full flex-col rounded-2xl border p-8 ${
                  p.highlighted
                    ? "border-blue-500 bg-white shadow-xl shadow-blue-500/10 dark:bg-gray-900"
                    : "border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900"
                }`}
              >
                {p.highlighted && (
                  <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 rounded-full bg-blue-500 px-4 py-1 text-xs font-semibold text-white">
                    人気プラン
                  </span>
                )}
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{p.name}</h3>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{p.desc}</p>
                <div className="mt-6">
                  <span className="text-4xl font-extrabold text-gray-900 dark:text-white">{p.price}</span>
                  {p.period && <span className="ml-1 text-sm text-gray-500 dark:text-gray-400">{p.period}</span>}
                </div>
                <ul className="mt-8 flex-1 space-y-3">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-center gap-2.5 text-sm text-gray-600 dark:text-gray-400">
                      <Check className="h-4 w-4 flex-shrink-0 text-emerald-500" />
                      {f}
                    </li>
                  ))}
                </ul>
                <a
                  href="#cta"
                  className={`mt-8 block rounded-full py-3 text-center text-sm font-semibold transition-all duration-150 active:scale-95 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 ${
                    p.highlighted
                      ? "bg-blue-500 text-white shadow-lg shadow-blue-500/25 hover:bg-blue-600"
                      : "border border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
                  }`}
                >
                  {p.cta}
                </a>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}

// --- CTA ---
function CTA() {
  return (
    <section id="cta" className="py-24 px-6">
      <FadeIn>
        <div className="mx-auto max-w-3xl rounded-3xl bg-gradient-to-br from-blue-500 to-violet-600 p-12 text-center shadow-2xl shadow-blue-500/20 sm:p-16">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            今日からチームを変えよう
          </h2>
          <p className="mt-4 text-blue-100">
            14日間無料。いつでもキャンセル可能。セットアップは2分で完了。
          </p>
          <div className="mt-8 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <a
              href="#"
              className="group inline-flex items-center gap-2 rounded-full bg-white px-8 py-3.5 text-sm font-semibold text-blue-600 shadow-lg transition-all duration-150 hover:bg-blue-50 active:scale-95 focus:outline-2 focus:outline-offset-2 focus:outline-white"
            >
              無料で始める
              <ChevronRight className="h-4 w-4 transition-transform duration-150 group-hover:translate-x-0.5" />
            </a>
          </div>
        </div>
      </FadeIn>
    </section>
  );
}

// --- Footer ---
function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-white py-12 px-6 dark:border-gray-800 dark:bg-gray-950">
      <div className="mx-auto max-w-6xl">
        <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
          <div className="col-span-2 sm:col-span-1">
            <a href="#" className="flex items-center gap-2 text-lg font-bold text-gray-900 dark:text-white">
              <Sparkles className="h-5 w-5 text-blue-500" />
              FlowSync
            </a>
            <p className="mt-3 text-sm leading-relaxed text-gray-500 dark:text-gray-400">
              チームの働き方を進化させる、オールインワンワークスペース。
            </p>
          </div>
          {[
            { title: "プロダクト", links: ["機能一覧", "料金", "更新履歴", "ロードマップ"] },
            { title: "サポート", links: ["ヘルプセンター", "お問い合わせ", "ステータス", "API"] },
            { title: "会社概要", links: ["私たちについて", "ブログ", "採用情報", "プレス"] },
          ].map((col) => (
            <div key={col.title}>
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white">{col.title}</h4>
              <ul className="mt-3 space-y-2">
                {col.links.map((link) => (
                  <li key={link}>
                    <a href="#" className="text-sm text-gray-500 transition-colors duration-150 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-10 border-t border-gray-200 pt-6 text-center text-xs text-gray-400 dark:border-gray-800">
          &copy; 2026 FlowSync Inc. All rights reserved.
        </div>
      </div>
    </footer>
  );
}

// --- Main Page ---
export default function LandingPage() {
  const [dark, setDark] = useState(false);

  return (
    <div className={dark ? "dark" : ""}>
      <div className="min-h-screen bg-white text-gray-900 dark:bg-gray-950 dark:text-gray-100 transition-colors duration-200">
        <Nav dark={dark} setDark={setDark} />
        <Hero />
        <Features />
        <Stats />
        <Testimonials />
        <Pricing />
        <CTA />
        <Footer />
      </div>
    </div>
  );
}
