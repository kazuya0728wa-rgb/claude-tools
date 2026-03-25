"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BarChart3,
  Users,
  DollarSign,
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight,
  Home,
  ShoppingCart,
  Settings,
  Bell,
  Search,
  Moon,
  Sun,
  ChevronLeft,
  ChevronRight,
  MoreHorizontal,
  ChevronDown,
  Database,
} from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

// --- Mock Data ---
const trendData = [
  { month: "1月", 売上: 4200, 訪問者: 2400 },
  { month: "2月", 売上: 3800, 訪問者: 1398 },
  { month: "3月", 売上: 5100, 訪問者: 3800 },
  { month: "4月", 売上: 4700, 訪問者: 3908 },
  { month: "5月", 売上: 5300, 訪問者: 4800 },
  { month: "6月", 売上: 6200, 訪問者: 3800 },
  { month: "7月", 売上: 5900, 訪問者: 4300 },
];

const comparisonData = [
  { category: "製品A", 今月: 4000, 先月: 2400 },
  { category: "製品B", 今月: 3000, 先月: 1398 },
  { category: "製品C", 今月: 2000, 先月: 3800 },
  { category: "製品D", 今月: 2780, 先月: 3908 },
  { category: "製品E", 今月: 1890, 先月: 4800 },
];

const tableData = [
  { id: "ORD-001", customer: "田中太郎", amount: "¥12,400", status: "完了", date: "2026-03-23" },
  { id: "ORD-002", customer: "佐藤花子", amount: "¥8,200", status: "処理中", date: "2026-03-22" },
  { id: "ORD-003", customer: "鈴木一郎", amount: "¥23,100", status: "完了", date: "2026-03-22" },
  { id: "ORD-004", customer: "高橋美咲", amount: "¥5,600", status: "キャンセル", date: "2026-03-21" },
  { id: "ORD-005", customer: "渡辺健", amount: "¥15,800", status: "完了", date: "2026-03-21" },
  { id: "ORD-006", customer: "伊藤恵", amount: "¥9,300", status: "処理中", date: "2026-03-20" },
];

const sidebarItems = [
  { icon: Home, label: "ダッシュボード", active: true },
  { icon: ShoppingCart, label: "注文管理", active: false },
  { icon: Users, label: "顧客管理", active: false },
  { icon: BarChart3, label: "分析", active: false },
  { icon: Settings, label: "設定", active: false },
];

// --- KPI Card Component ---
function KpiCard({
  title,
  value,
  change,
  trend,
  icon: Icon,
  loading,
}: {
  title: string;
  value: string;
  change: string;
  trend: "up" | "down";
  icon: React.ElementType;
  loading?: boolean;
}) {
  if (loading) {
    return (
      <div className="rounded-xl border border-[hsl(var(--color-border))] bg-[hsl(var(--color-surface))] p-6 animate-pulse">
        <div className="flex items-center justify-between mb-4">
          <div className="h-4 w-20 rounded bg-[hsl(var(--color-border))]" />
          <div className="h-10 w-10 rounded-lg bg-[hsl(var(--color-border))]" />
        </div>
        <div className="h-8 w-28 rounded bg-[hsl(var(--color-border))] mb-2" />
        <div className="h-4 w-16 rounded bg-[hsl(var(--color-border))]" />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-[hsl(var(--color-border))] bg-[hsl(var(--color-surface))] p-6 transition-colors duration-150 hover:border-[hsl(var(--color-accent))]"
    >
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-[hsl(var(--color-muted))]">{title}</span>
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[hsl(var(--color-accent)/0.1)]">
          <Icon className="h-5 w-5 text-[hsl(var(--color-accent))]" />
        </div>
      </div>
      <p className="text-2xl font-bold text-[hsl(var(--color-foreground))]">{value}</p>
      <div className="mt-2 flex items-center gap-1">
        {trend === "up" ? (
          <ArrowUpRight className="h-4 w-4 text-[hsl(var(--color-success))]" />
        ) : (
          <ArrowDownRight className="h-4 w-4 text-[hsl(var(--color-error))]" />
        )}
        <span
          className={`text-sm font-medium ${
            trend === "up" ? "text-[hsl(var(--color-success))]" : "text-[hsl(var(--color-error))]"
          }`}
        >
          {change}
        </span>
        <span className="text-sm text-[hsl(var(--color-muted))]">前月比</span>
      </div>
    </motion.div>
  );
}

// --- Status Badge ---
function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    完了: "bg-[hsl(var(--color-success)/0.1)] text-[hsl(var(--color-success))]",
    処理中: "bg-[hsl(var(--color-accent)/0.1)] text-[hsl(var(--color-accent))]",
    キャンセル: "bg-[hsl(var(--color-error)/0.1)] text-[hsl(var(--color-error))]",
  };

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${styles[status] || ""}`}>
      {status}
    </span>
  );
}

// --- Empty State ---
function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <Database className="h-12 w-12 text-[hsl(var(--color-muted))] mb-4" />
      <h3 className="text-lg font-semibold text-[hsl(var(--color-foreground))]">
        まだデータがありません
      </h3>
      <p className="mt-1 text-sm text-[hsl(var(--color-muted))]">
        最初のデータが登録されると、ここに表示されます
      </p>
    </div>
  );
}

// --- Custom Tooltip for Charts ---
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-[hsl(var(--color-border))] bg-[hsl(var(--color-surface))] p-3 shadow-lg">
      <p className="text-sm font-medium text-[hsl(var(--color-foreground))] mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} className="text-sm" style={{ color: entry.color }}>
          {entry.name}: {entry.value.toLocaleString()}
        </p>
      ))}
    </div>
  );
}

// --- Main Dashboard ---
export default function DashboardPage() {
  const [darkMode, setDarkMode] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;

  const toggleDarkMode = () => setDarkMode(!darkMode);
  const toggleSidebar = () => setSidebarCollapsed(!sidebarCollapsed);

  // Sort logic
  const sortedTableData = [...tableData].sort((a, b) => {
    if (!sortColumn) return 0;
    const aVal = a[sortColumn as keyof typeof a];
    const bVal = b[sortColumn as keyof typeof b];
    if (aVal < bVal) return sortDirection === "asc" ? -1 : 1;
    if (aVal > bVal) return sortDirection === "asc" ? 1 : -1;
    return 0;
  });

  const paginatedData = sortedTableData.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );
  const totalPages = Math.ceil(sortedTableData.length / itemsPerPage);

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortColumn(column);
      setSortDirection("asc");
    }
  };

  return (
    <div className={darkMode ? "dark" : ""}>
      <div className="flex h-screen bg-[hsl(var(--color-background))] text-[hsl(var(--color-foreground))] transition-colors duration-200">
        {/* Sidebar */}
        <aside
          className={`flex flex-col border-r border-[hsl(var(--color-border))] bg-[hsl(var(--color-surface))] transition-all duration-200 ${
            sidebarCollapsed ? "w-16" : "w-60"
          }`}
          role="navigation"
          aria-label="サイドバーナビゲーション"
        >
          {/* Logo */}
          <div className="flex h-16 items-center justify-between border-b border-[hsl(var(--color-border))] px-4">
            {!sidebarCollapsed && (
              <span className="text-lg font-bold text-[hsl(var(--color-accent))]">Dashboard</span>
            )}
            <button
              onClick={toggleSidebar}
              className="flex h-8 w-8 items-center justify-center rounded-md transition-colors duration-150 hover:bg-[hsl(var(--color-border))] focus:outline-2 focus:outline-offset-2 focus:outline-current"
              aria-label={sidebarCollapsed ? "サイドバーを展開" : "サイドバーを折りたたむ"}
            >
              {sidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
            </button>
          </div>

          {/* Nav Items */}
          <nav className="flex-1 py-4">
            <ul className="space-y-1 px-2">
              {sidebarItems.map((item) => (
                <li key={item.label}>
                  <button
                    className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors duration-150 focus:outline-2 focus:outline-offset-2 focus:outline-current ${
                      item.active
                        ? "bg-[hsl(var(--color-accent)/0.1)] text-[hsl(var(--color-accent))]"
                        : "text-[hsl(var(--color-muted))] hover:bg-[hsl(var(--color-border))] hover:text-[hsl(var(--color-foreground))]"
                    }`}
                    aria-current={item.active ? "page" : undefined}
                  >
                    <item.icon className="h-5 w-5 flex-shrink-0" />
                    {!sidebarCollapsed && <span>{item.label}</span>}
                  </button>
                </li>
              ))}
            </ul>
          </nav>
        </aside>

        {/* Main Content */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {/* Header */}
          <header className="flex h-16 items-center justify-between border-b border-[hsl(var(--color-border))] bg-[hsl(var(--color-surface))] px-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[hsl(var(--color-muted))]" />
              <input
                type="search"
                placeholder="検索..."
                className="h-9 w-64 rounded-lg border border-[hsl(var(--color-border))] bg-[hsl(var(--color-background))] pl-9 pr-3 text-sm transition-colors duration-150 placeholder:text-[hsl(var(--color-muted))] focus:border-[hsl(var(--color-accent))] focus:outline-2 focus:outline-offset-2 focus:outline-current"
                aria-label="ダッシュボードを検索"
              />
            </div>

            <div className="flex items-center gap-3">
              {/* Dark mode toggle */}
              <button
                onClick={toggleDarkMode}
                className="flex h-9 w-9 items-center justify-center rounded-lg transition-colors duration-150 hover:bg-[hsl(var(--color-border))] focus:outline-2 focus:outline-offset-2 focus:outline-current"
                aria-label={darkMode ? "ライトモードに切替" : "ダークモードに切替"}
              >
                {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </button>

              {/* Notifications */}
              <button
                className="relative flex h-9 w-9 items-center justify-center rounded-lg transition-colors duration-150 hover:bg-[hsl(var(--color-border))] focus:outline-2 focus:outline-offset-2 focus:outline-current"
                aria-label="通知"
              >
                <Bell className="h-5 w-5" />
                <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-[hsl(var(--color-error))]" />
              </button>

              {/* User avatar */}
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[hsl(var(--color-accent))] text-sm font-bold text-white">
                K
              </div>
            </div>
          </header>

          {/* Dashboard Content */}
          <main className="flex-1 overflow-y-auto p-6" role="main">
            <div className="mx-auto max-w-7xl space-y-6">
              {/* Page Title */}
              <div>
                <h1 className="text-2xl font-bold">ダッシュボード</h1>
                <p className="text-sm text-[hsl(var(--color-muted))]">ビジネスの概要を確認できます</p>
              </div>

              {/* KPI Cards */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <KpiCard
                  title="総売上"
                  value="¥1,234,567"
                  change="+12.5%"
                  trend="up"
                  icon={DollarSign}
                  loading={loading}
                />
                <KpiCard
                  title="新規ユーザー"
                  value="2,345"
                  change="+8.2%"
                  trend="up"
                  icon={Users}
                  loading={loading}
                />
                <KpiCard
                  title="コンバージョン率"
                  value="3.24%"
                  change="-0.4%"
                  trend="down"
                  icon={TrendingUp}
                  loading={loading}
                />
                <KpiCard
                  title="注文数"
                  value="1,892"
                  change="+15.3%"
                  trend="up"
                  icon={ShoppingCart}
                  loading={loading}
                />
              </div>

              {/* Charts Row */}
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                {/* Line Chart - Trend */}
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="rounded-xl border border-[hsl(var(--color-border))] bg-[hsl(var(--color-surface))] p-6"
                >
                  <h2 className="mb-4 text-lg font-semibold">売上トレンド</h2>
                  <ResponsiveContainer width="100%" height={280}>
                    <LineChart data={trendData}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                      <XAxis
                        dataKey="month"
                        tick={{ fontSize: 12 }}
                        stroke="hsl(var(--color-muted))"
                      />
                      <YAxis
                        tick={{ fontSize: 12 }}
                        stroke="hsl(var(--color-muted))"
                        tickFormatter={(v) => `${v / 1000}k`}
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend verticalAlign="top" height={36} />
                      <Line
                        type="monotone"
                        dataKey="売上"
                        stroke="#3B82F6"
                        strokeWidth={2}
                        dot={{ r: 4 }}
                        activeDot={{ r: 6 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="訪問者"
                        stroke="#F97316"
                        strokeWidth={2}
                        dot={{ r: 4 }}
                        activeDot={{ r: 6 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </motion.div>

                {/* Bar Chart - Comparison */}
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="rounded-xl border border-[hsl(var(--color-border))] bg-[hsl(var(--color-surface))] p-6"
                >
                  <h2 className="mb-4 text-lg font-semibold">製品別売上比較</h2>
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={comparisonData}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                      <XAxis
                        dataKey="category"
                        tick={{ fontSize: 12 }}
                        stroke="hsl(var(--color-muted))"
                      />
                      <YAxis
                        tick={{ fontSize: 12 }}
                        stroke="hsl(var(--color-muted))"
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend verticalAlign="top" height={36} />
                      <Bar dataKey="今月" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="先月" fill="#F97316" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </motion.div>
              </div>

              {/* Data Table */}
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="rounded-xl border border-[hsl(var(--color-border))] bg-[hsl(var(--color-surface))]"
              >
                <div className="flex items-center justify-between border-b border-[hsl(var(--color-border))] px-6 py-4">
                  <h2 className="text-lg font-semibold">最近の注文</h2>
                  <button
                    className="flex h-8 items-center gap-1 rounded-lg border border-[hsl(var(--color-border))] px-3 text-sm transition-colors duration-150 hover:bg-[hsl(var(--color-border))] focus:outline-2 focus:outline-offset-2 focus:outline-current"
                    aria-label="フィルター"
                  >
                    フィルター
                    <ChevronDown className="h-4 w-4" />
                  </button>
                </div>

                {paginatedData.length === 0 ? (
                  <EmptyState />
                ) : (
                  <>
                    <div className="overflow-x-auto">
                      <table className="w-full" role="table">
                        <thead>
                          <tr className="border-b border-[hsl(var(--color-border))]">
                            {[
                              { key: "id", label: "注文ID" },
                              { key: "customer", label: "顧客" },
                              { key: "amount", label: "金額" },
                              { key: "status", label: "ステータス" },
                              { key: "date", label: "日付" },
                            ].map((col) => (
                              <th
                                key={col.key}
                                className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-[hsl(var(--color-muted))] cursor-pointer select-none transition-colors duration-150 hover:text-[hsl(var(--color-foreground))]"
                                onClick={() => handleSort(col.key)}
                                aria-sort={
                                  sortColumn === col.key
                                    ? sortDirection === "asc"
                                      ? "ascending"
                                      : "descending"
                                    : "none"
                                }
                              >
                                <span className="flex items-center gap-1">
                                  {col.label}
                                  {sortColumn === col.key && (
                                    <span className="text-[hsl(var(--color-accent))]">
                                      {sortDirection === "asc" ? "↑" : "↓"}
                                    </span>
                                  )}
                                </span>
                              </th>
                            ))}
                            <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-[hsl(var(--color-muted))]">
                              操作
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[hsl(var(--color-border))]">
                          {paginatedData.map((row) => (
                            <tr
                              key={row.id}
                              className="transition-colors duration-150 hover:bg-[hsl(var(--color-background))]"
                            >
                              <td className="whitespace-nowrap px-6 py-4 text-sm font-medium">
                                {row.id}
                              </td>
                              <td className="whitespace-nowrap px-6 py-4 text-sm">{row.customer}</td>
                              <td className="whitespace-nowrap px-6 py-4 text-sm font-medium">
                                {row.amount}
                              </td>
                              <td className="whitespace-nowrap px-6 py-4 text-sm">
                                <StatusBadge status={row.status} />
                              </td>
                              <td className="whitespace-nowrap px-6 py-4 text-sm text-[hsl(var(--color-muted))]">
                                {row.date}
                              </td>
                              <td className="whitespace-nowrap px-6 py-4 text-right">
                                <button
                                  className="flex h-8 w-8 items-center justify-center rounded-md transition-colors duration-150 hover:bg-[hsl(var(--color-border))] focus:outline-2 focus:outline-offset-2 focus:outline-current ml-auto"
                                  aria-label={`${row.id}の操作メニュー`}
                                >
                                  <MoreHorizontal className="h-4 w-4" />
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Pagination */}
                    <div className="flex items-center justify-between border-t border-[hsl(var(--color-border))] px-6 py-3">
                      <p className="text-sm text-[hsl(var(--color-muted))]">
                        全{sortedTableData.length}件中 {(currentPage - 1) * itemsPerPage + 1}〜
                        {Math.min(currentPage * itemsPerPage, sortedTableData.length)}件を表示
                      </p>
                      <div className="flex gap-1">
                        <button
                          onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                          disabled={currentPage === 1}
                          className="flex h-8 w-8 items-center justify-center rounded-md border border-[hsl(var(--color-border))] transition-colors duration-150 hover:bg-[hsl(var(--color-border))] disabled:opacity-40 disabled:cursor-not-allowed focus:outline-2 focus:outline-offset-2 focus:outline-current"
                          aria-label="前のページ"
                        >
                          <ChevronLeft className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                          disabled={currentPage === totalPages}
                          className="flex h-8 w-8 items-center justify-center rounded-md border border-[hsl(var(--color-border))] transition-colors duration-150 hover:bg-[hsl(var(--color-border))] disabled:opacity-40 disabled:cursor-not-allowed focus:outline-2 focus:outline-offset-2 focus:outline-current"
                          aria-label="次のページ"
                        >
                          <ChevronRight className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </motion.div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
