"use client";

import Link from "next/link";
import { useState } from "react";

type WorkspaceMode = "home" | "dashboard" | "reviews" | "admin" | "users";

type IconName =
  | "dashboard"
  | "detail"
  | "price"
  | "extension"
  | "knowledge"
  | "users"
  | "hotel"
  | "settings";

type NavItem = {
  label: string;
  href?: string;
  badge?: string;
  disabled?: boolean;
  icon: IconName;
};

type SectionKey = "review" | "price" | "extension" | "knowledge" | "administration";

type NavSection = {
  key: SectionKey;
  label: string;
  href?: string;
  icon?: IconName;
  items?: NavItem[];
};

function NavIcon({
  name,
  active,
  disabled,
}: {
  name: IconName;
  active?: boolean;
  disabled?: boolean;
}) {
  const colorClass = active
    ? "text-blue-500"
    : disabled
      ? "text-slate-300"
      : "text-slate-400 group-hover:text-slate-500";

  const iconClassName = `h-5 w-5 shrink-0 ${colorClass} transition`;

  switch (name) {
    case "dashboard":
      return (
        <svg viewBox="0 0 20 20" fill="none" className={iconClassName} aria-hidden="true">
          <rect x="3" y="3" width="5" height="5" rx="1.5" stroke="currentColor" strokeWidth="1.7" />
          <rect x="12" y="3" width="5" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.7" />
          <rect x="3" y="12" width="5" height="5" rx="1.5" stroke="currentColor" strokeWidth="1.7" />
          <rect x="12" y="14" width="5" height="3" rx="1.5" stroke="currentColor" strokeWidth="1.7" />
        </svg>
      );
    case "detail":
      return (
        <svg viewBox="0 0 20 20" fill="none" className={iconClassName} aria-hidden="true">
          <path d="M5 5.5h10M5 10h10M5 14.5h6.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
          <circle cx="14.5" cy="14.5" r="2.5" stroke="currentColor" strokeWidth="1.7" />
        </svg>
      );
    case "price":
      return (
        <svg viewBox="0 0 20 20" fill="none" className={iconClassName} aria-hidden="true">
          <path d="M10 3.5v13M13.5 6.5c0-1.1-1.57-2-3.5-2s-3.5.9-3.5 2 1.57 2 3.5 2 3.5.9 3.5 2-1.57 2-3.5 2-3.5-.9-3.5-2" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "extension":
      return (
        <svg viewBox="0 0 20 20" fill="none" className={iconClassName} aria-hidden="true">
          <path d="M7 6V4.75A1.75 1.75 0 0 1 8.75 3h2.5A1.75 1.75 0 0 1 13 4.75V6M7 14v1.25A1.75 1.75 0 0 0 8.75 17h2.5A1.75 1.75 0 0 0 13 15.25V14M6 7H4.75A1.75 1.75 0 0 0 3 8.75v2.5A1.75 1.75 0 0 0 4.75 13H6m8 0h1.25A1.75 1.75 0 0 0 17 11.25v-2.5A1.75 1.75 0 0 0 15.25 7H14" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
          <rect x="6.5" y="6.5" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.7" />
        </svg>
      );
    case "knowledge":
      return (
        <svg viewBox="0 0 20 20" fill="none" className={iconClassName} aria-hidden="true">
          <path d="M6 4.5h7.25A2.75 2.75 0 0 1 16 7.25V14a1 1 0 0 1-1.53.85L11 12.75l-3.47 2.1A1 1 0 0 1 6 14V4.5Z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
          <path d="M6 5h-.25A1.75 1.75 0 0 0 4 6.75v8.5C4 16.22 4.78 17 5.75 17H13" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
        </svg>
      );
    case "users":
      return (
        <svg viewBox="0 0 20 20" fill="none" className={iconClassName} aria-hidden="true">
          <circle cx="8" cy="7" r="2.5" stroke="currentColor" strokeWidth="1.7" />
          <path d="M3.5 15c.9-2 2.58-3 4.5-3s3.6 1 4.5 3M13.75 8.25a2 2 0 1 0 0-4M13 12.25c1.44.2 2.62 1.02 3.5 2.45" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
        </svg>
      );
    case "hotel":
      return (
        <svg viewBox="0 0 20 20" fill="none" className={iconClassName} aria-hidden="true">
          <path d="M4 16V5.5A1.5 1.5 0 0 1 5.5 4H11v12M11 8h5v8M6.5 7.5h1M6.5 10.5h1M6.5 13.5h1" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "settings":
      return (
        <svg viewBox="0 0 20 20" fill="none" className={iconClassName} aria-hidden="true">
          <circle cx="10" cy="10" r="2.5" stroke="currentColor" strokeWidth="1.7" />
          <path d="M10 3.5v1.5M10 15v1.5M15 10h1.5M3.5 10H5M14.6 5.4l1 1M4.4 15.6l1-1M14.6 14.6l1 1M4.4 4.4l1 1" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
        </svg>
      );
  }
}

function SidebarLink({
  item,
  active,
}: {
  item: NavItem;
  active: boolean;
}) {
  const content = (
    <span
      className={`group flex w-full items-center justify-between gap-3 rounded-2xl border px-4 py-4 text-[15px] font-medium transition ${
        active
          ? "border-blue-200 bg-[var(--accent-soft)] text-[var(--accent)] shadow-sm"
          : item.disabled
            ? "cursor-not-allowed border-transparent bg-slate-50 text-slate-400"
            : "border-transparent bg-transparent text-slate-700 hover:border-slate-200 hover:bg-white hover:text-slate-900"
      }`}
    >
      <span className="flex min-w-0 items-center gap-3">
        <NavIcon name={item.icon} active={active} disabled={item.disabled} />
        <span className="min-w-0 leading-6">{item.label}</span>
      </span>
      {item.badge ? (
        <span className="shrink-0 whitespace-nowrap rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[13px] font-semibold leading-none text-slate-500">
          {item.badge}
        </span>
      ) : null}
    </span>
  );

  if (!item.href || item.disabled) {
    return <div>{content}</div>;
  }

  return <Link href={item.href}>{content}</Link>;
}

export function WorkspaceShell({
  mode,
  title,
  subtitle,
  statusLabel,
  showHeaderActions = true,
  children,
}: {
  mode: WorkspaceMode;
  title: string;
  subtitle: string;
  statusLabel: string;
  showHeaderActions?: boolean;
  children: React.ReactNode;
}) {
  const activeSection =
    mode === "dashboard" || mode === "reviews"
      ? "review"
      : mode === "admin" || mode === "users"
        ? "administration"
        : null;
  const [expandedSection, setExpandedSection] = useState<SectionKey | null>(activeSection);
  const [mobileNavVisible, setMobileNavVisible] = useState(false);

  const priceItems: NavItem[] = [
    { label: "Price panel", badge: "Coming soon", disabled: true, icon: "price" },
  ];

  const extensionItems: NavItem[] = [
    { label: "Extensions", badge: "Coming soon", disabled: true, icon: "extension" },
  ];

  const knowledgeItems: NavItem[] = [
    { label: "Knowledge hub", badge: "Coming soon", disabled: true, icon: "knowledge" },
  ];

  const administrationItems: NavItem[] = [
    { label: "Users & roles", href: "/admin/users", badge: "Live", icon: "users" },
    { label: "Hotel panel", href: "/admin", badge: "Live", icon: "hotel" },
    { label: "Settings", badge: "Coming soon", disabled: true, icon: "settings" },
  ];

  const activeHref =
    mode === "users" ? "/admin/users" : mode === "admin" ? "/admin" : mode === "dashboard" || mode === "reviews" ? "/" : "";

  const sections: NavSection[] = [
    { key: "review" as const, label: "Review", href: "/", icon: "dashboard" },
    { key: "price" as const, label: "Price", items: priceItems },
    { key: "extension" as const, label: "Extension", items: extensionItems },
    { key: "knowledge" as const, label: "Knowledge", items: knowledgeItems },
    {
      key: "administration" as const,
      label: "Administration",
      items: administrationItems,
    },
  ];

  return (
    <main className="min-h-screen text-slate-900">
      <div className="flex min-h-screen w-full gap-4 px-3 py-3 lg:gap-4 lg:px-4">
        <aside className="hidden w-[268px] shrink-0 rounded-[16px] border border-slate-200 bg-white p-4 shadow-sm lg:flex lg:flex-col">
          <Link href="/" className="rounded-[14px] border border-slate-200 bg-white px-5 py-5 transition hover:border-slate-300 hover:bg-slate-50">
            <div className="flex items-center gap-3">
              <div className="flex h-14 w-14 items-center justify-center rounded-[14px] bg-slate-900 text-[22px] font-bold text-white">
                J
              </div>
              <div>
                <p className="text-[13px] font-semibold text-[#667085]">JoyON hospitality</p>
                <h1 className="mt-1 font-display text-[28px] font-semibold leading-[0.98] text-[#111827]">
                  JoyON Workspace
                </h1>
              </div>
            </div>
          </Link>

          <div className="mt-4 flex-1 space-y-6 px-2 py-2">
            {sections.map((section) => {
              const isExpanded = expandedSection === section.key;
              const hasActiveChild =
                section.key === "review" && (mode === "dashboard" || mode === "reviews");

              if (!section.items?.length) {
                return (
                  <div key={section.key}>
                    <Link href={section.href || "#"}>
                      <span
                        className={`group flex w-full items-center justify-between gap-3 rounded-[14px] px-4 py-3.5 text-left text-[15px] font-bold transition ${
                          hasActiveChild
                            ? "bg-slate-100 text-[#111827]"
                            : "text-[#46556D] hover:bg-slate-50"
                        }`}
                      >
                        <span className="flex min-w-0 items-center gap-3">
                          {section.icon ? <NavIcon name={section.icon} active={hasActiveChild} /> : null}
                          <span>{section.label}</span>
                        </span>
                      </span>
                    </Link>
                  </div>
                );
              }

              return (
                <div key={section.key}>
                  <button
                    type="button"
                    onClick={() =>
                      setExpandedSection((current) =>
                        current === section.key ? null : section.key,
                      )
                    }
                    className={`flex w-full items-center justify-between rounded-[14px] px-4 py-3.5 text-left text-[15px] font-bold transition ${
                      isExpanded || hasActiveChild
                        ? "bg-slate-100 text-[#111827]"
                        : "text-[#46556D] hover:bg-slate-50"
                    }`}
                  >
                    <span>{section.label}</span>
                    <span className={`text-[14px] text-slate-400 transition ${isExpanded ? "rotate-180" : ""}`}>
                      ▾
                    </span>
                  </button>

                  {isExpanded ? (
                    <div className="mt-2 space-y-1">
                      {section.items.map((item) => (
                        <SidebarLink
                          key={item.label}
                          item={item}
                          active={item.href === activeHref}
                        />
                      ))}
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        </aside>

        <div className="min-w-0 flex-1 rounded-[16px] border border-slate-200 bg-white shadow-sm">
          <header className="sticky top-0 z-10 rounded-t-[16px] border-b border-slate-200 bg-white">
            <div className="flex flex-wrap items-center justify-between gap-4 px-5 py-5 lg:px-8">
              <div className="flex min-w-0 items-start gap-4">
                <button
                  type="button"
                  className="hidden h-11 w-11 shrink-0 items-center justify-center rounded-[12px] border border-slate-200 bg-white text-slate-500 lg:flex"
                  aria-label="Workspace navigation"
                >
                  <svg viewBox="0 0 20 20" fill="none" className="h-5 w-5" aria-hidden="true">
                    <path d="M4 6h12M4 10h12M4 14h12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                  </svg>
                </button>
                <div>
                  <h2 className="font-display text-[30px] font-semibold leading-tight text-[#111827]">
                  {title}
                  </h2>
                  <p className="mt-1 text-[14px] font-medium text-[#667085]">{subtitle}</p>
                </div>
              </div>
              {showHeaderActions ? (
                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      if (typeof window !== "undefined") {
                        window.dispatchEvent(new Event("joyon-logout"));
                      }
                    }}
                    className="rounded-[12px] border border-slate-200 bg-white px-4 py-2.5 text-[14px] font-semibold text-slate-700 transition hover:bg-slate-50"
                  >
                    Logout
                  </button>
                  <div className="hidden h-11 w-11 items-center justify-center rounded-[12px] border border-slate-200 bg-white text-slate-500 md:flex">
                    <svg viewBox="0 0 20 20" fill="none" className="h-5 w-5" aria-hidden="true">
                      <path d="M5 7.5h10M5 11h10M5 14.5h6.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
                    </svg>
                  </div>
                  <div className="rounded-[12px] border border-slate-200 bg-slate-50 px-4 py-2.5 text-[14px] font-medium text-[#667085]">
                    {statusLabel}
                  </div>
                </div>
              ) : null}
            </div>

            <div className="border-t border-slate-100 px-5 py-4 lg:hidden">
              <div className="space-y-3">
                <div className="flex justify-start">
                  <button
                    type="button"
                    onClick={() => setMobileNavVisible((current) => !current)}
                    className="inline-flex h-10 w-10 items-center justify-center rounded-[12px] border border-slate-200 bg-white text-slate-700 transition hover:bg-slate-50"
                    aria-label={mobileNavVisible ? "Hide sections" : "Show sections"}
                  >
                    <svg viewBox="0 0 20 20" fill="none" className="h-4 w-4" aria-hidden="true">
                      <path d="M4 6h12M4 10h12M4 14h12" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
                    </svg>
                  </button>
                </div>

                {mobileNavVisible ? (
                  <div className="space-y-3 rounded-[14px] border border-slate-200 bg-white p-3 shadow-sm">
                    {sections.map((section) => {
                      const hasActiveChild =
                        section.key === "review" && (mode === "dashboard" || mode === "reviews");
                      const isExpanded = expandedSection === section.key;

                      if (!section.items?.length) {
                        return (
                          <Link key={section.key} href={section.href || "#"}>
                            <div
                              className={`flex items-center gap-3 rounded-[12px] border px-3 py-3 text-left text-[15px] font-semibold transition ${
                                hasActiveChild
                                  ? "border-blue-200 bg-[var(--accent-soft)] text-[var(--accent)]"
                                  : "border-slate-200 bg-slate-50/60 text-slate-700"
                              }`}
                            >
                              {section.icon ? <NavIcon name={section.icon} active={hasActiveChild} /> : null}
                              <span>{section.label}</span>
                            </div>
                          </Link>
                        );
                      }

                      return (
                        <div key={section.key} className="rounded-[12px] border border-slate-200 bg-slate-50/60">
                          <button
                            type="button"
                            onClick={() =>
                              setExpandedSection((current) =>
                                current === section.key ? null : section.key,
                              )
                            }
                            className={`flex w-full items-center justify-between rounded-[12px] px-3 py-3 text-left text-[15px] font-semibold transition ${
                              isExpanded || hasActiveChild
                                ? "bg-[var(--accent-soft)] text-[var(--accent)]"
                                : "text-slate-700"
                            }`}
                          >
                            <span>{section.label}</span>
                            <span className={`text-[13px] transition ${isExpanded ? "rotate-180" : ""}`}>▾</span>
                          </button>

                          {isExpanded ? (
                            <div className="space-y-2 border-t border-slate-200 px-2 py-2">
                              {section.items.map((item) => (
                                <SidebarLink
                                  key={item.label}
                                  item={item}
                                  active={item.href === activeHref}
                                />
                              ))}
                            </div>
                          ) : null}
                        </div>
                      );
                    })}
                  </div>
                ) : null}
              </div>
            </div>
          </header>

          <div className="space-y-6 px-5 py-6 lg:px-8">{children}</div>
        </div>
      </div>
    </main>
  );
}
