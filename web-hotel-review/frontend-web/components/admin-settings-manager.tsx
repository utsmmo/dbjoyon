"use client";

import { useEffect, useMemo, useState, useSyncExternalStore, useTransition } from "react";
import { WorkspaceShell } from "@/components/workspace-shell";
import { getAuthSessionSnapshot, hasPermission, isAdmin, subscribeToAuthState } from "@/lib/auth";
import type { AdminSetting, AdminSettingListResponse } from "@/lib/types";

const API_PREFIX = process.env.NEXT_PUBLIC_BASE_PATH || "";
const AI_REGISTRY_KEY = "ai.providers_registry";
const LEGACY_AI_KEYS = {
  baseUrl: "review_ai.base_url",
  apiKey: "review_ai.api_key",
  model: "review_ai.model",
  timeoutMs: "review_ai.timeout_ms",
} as const;

const GROUP_META: Record<string, { title: string; description: string }> = {
  integrations: {
    title: "Channex",
    description: "Webhook secret, API key, forward webhook, timeout, and channel mapping for the Channex bridge.",
  },
  review: {
    title: "Review rules",
    description: "Shared thresholds and scoring rules used by the review dashboard.",
  },
  notifications: {
    title: "Notifications",
    description: "Webhook and timeout settings for operational alerts.",
  },
};

const SETTINGS_GROUP_ORDER = ["integrations", "review", "notifications"];
const SERVICE_OPTIONS = [
  { value: "review_insights", label: "Review insights" },
  { value: "review_translation", label: "Review translation" },
];

type AiRegistryItem = {
  id: string;
  name: string;
  apiKey: string;
  baseUrl: string;
  model: string;
  timeoutMs: number;
  services: string[];
  enabled: boolean;
  isDefault: boolean;
};

type AiRegistryDraft = {
  id: string;
  name: string;
  apiKey: string;
  baseUrl: string;
  model: string;
  timeoutMs: string;
  services: string[];
  enabled: boolean;
  isDefault: boolean;
};

function createEmptyDraft(): AiRegistryDraft {
  return {
    id: `provider-${Date.now()}`,
    name: "",
    apiKey: "",
    baseUrl: "",
    model: "",
    timeoutMs: "45000",
    services: [],
    enabled: true,
    isDefault: false,
  };
}

function maskSecret(value: string) {
  const stripped = value.trim();
  if (!stripped) {
    return "No key";
  }
  if (stripped.length <= 8) {
    return "*".repeat(stripped.length);
  }
  return `${stripped.slice(0, 3)}${"*".repeat(Math.max(stripped.length - 7, 4))}${stripped.slice(-4)}`;
}

function normalizeRegistryItem(item: Partial<AiRegistryItem>, index: number): AiRegistryItem {
  return {
    id: String(item.id || `provider-${index + 1}`),
    name: String(item.name || `AI Provider ${index + 1}`),
    apiKey: String(item.apiKey || ""),
    baseUrl: String(item.baseUrl || ""),
    model: String(item.model || ""),
    timeoutMs: Number.isFinite(Number(item.timeoutMs)) ? Number(item.timeoutMs) : 45000,
    services: Array.isArray(item.services)
      ? item.services.map((service) => String(service)).filter(Boolean)
      : [],
    enabled: item.enabled !== false,
    isDefault: Boolean(item.isDefault),
  };
}

export function AdminSettingsManager() {
  const session = useSyncExternalStore(
    subscribeToAuthState,
    getAuthSessionSnapshot,
    () => null,
  );
  const canAccessAdmin = isAdmin(session);
  const canView = hasPermission(session, ["settings.view", "settings.manage"]);
  const canManage = hasPermission(session, "settings.manage");
  const [items, setItems] = useState<AdminSetting[]>([]);
  const [draftValues, setDraftValues] = useState<Record<string, string>>({});
  const [savingKeys, setSavingKeys] = useState<Record<string, boolean>>({});
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({
    integrations: true,
    review: false,
    notifications: false,
  });
  const [editorDraft, setEditorDraft] = useState<AiRegistryDraft | null>(null);
  const [editorMode, setEditorMode] = useState<"create" | "edit">("create");
  const [registrySaving, setRegistrySaving] = useState(false);
  const [validationState, setValidationState] = useState<{
    status: "idle" | "checking" | "passed" | "failed";
    message: string;
  }>({
    status: "idle",
    message: "",
  });
  const [isPending, startTransition] = useTransition();

  function localizeError(message: string) {
    if (message.includes("Failed to load settings")) {
      return "Unable to load settings.";
    }
    return message;
  }

  async function loadSettings() {
    const response = await fetch(`${API_PREFIX}/api/admin/settings`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error((await response.text()) || "Failed to load settings");
    }

    const payload = (await response.json()) as AdminSettingListResponse;
    setItems(payload.items);
  }

  useEffect(() => {
    if (!canView) {
      return;
    }

    startTransition(() => {
      loadSettings().catch((loadError: unknown) => {
        setError(loadError instanceof Error ? localizeError(loadError.message) : "Unable to load settings.");
      });
    });
  }, [canView]);

  const aiRegistrySetting = useMemo(
    () => items.find((item) => item.setting_key === AI_REGISTRY_KEY) || null,
    [items],
  );

  const aiRegistryItems = useMemo(() => {
    if (!aiRegistrySetting?.value) {
      const fallbackBaseUrl = items.find((item) => item.setting_key === LEGACY_AI_KEYS.baseUrl)?.value || "";
      const fallbackApiKey = items.find((item) => item.setting_key === LEGACY_AI_KEYS.apiKey)?.masked_value || "";
      const fallbackModel = items.find((item) => item.setting_key === LEGACY_AI_KEYS.model)?.value || "";
      const fallbackTimeout = items.find((item) => item.setting_key === LEGACY_AI_KEYS.timeoutMs)?.value || "45000";

      if (!fallbackBaseUrl && !fallbackApiKey && !fallbackModel) {
        return [];
      }

      return [
        {
          id: "legacy-review-ai",
          name: "Review AI Primary",
          apiKey: fallbackApiKey,
          baseUrl: fallbackBaseUrl,
          model: fallbackModel,
          timeoutMs: Number(fallbackTimeout) || 45000,
          services: ["review_insights", "review_translation"],
          enabled: true,
          isDefault: true,
        },
      ];
    }

    try {
      const raw = JSON.parse(aiRegistrySetting.value) as Partial<AiRegistryItem>[];
      if (!Array.isArray(raw)) {
        return [];
      }
      const normalized = raw.map((item, index) => normalizeRegistryItem(item, index));
      if (normalized.some((item) => item.isDefault)) {
        return normalized;
      }
      if (normalized[0]) {
        normalized[0].isDefault = true;
      }
      return normalized;
    } catch {
      return [];
    }
  }, [aiRegistrySetting, items]);

  const groupedItems = useMemo(() => {
    const hiddenKeys = new Set([
      AI_REGISTRY_KEY,
      LEGACY_AI_KEYS.baseUrl,
      LEGACY_AI_KEYS.apiKey,
      LEGACY_AI_KEYS.model,
      LEGACY_AI_KEYS.timeoutMs,
      "connections.review_ai_primary",
      "connections.translation_primary",
      "connections.lark_bad_review_primary",
      "connections.lark_handoff_primary",
      "service_bindings.review_insights_connection",
      "service_bindings.review_translation_connection",
      "service_bindings.bad_review_lark_connection",
      "service_bindings.chatbot_handoff_lark_connection",
    ]);

    const visibleGroups = Object.entries(
      items.reduce<Record<string, AdminSetting[]>>((groups, item) => {
        if (hiddenKeys.has(item.setting_key)) {
          return groups;
        }
        if (!SETTINGS_GROUP_ORDER.includes(item.group_code)) {
          return groups;
        }
        if (!groups[item.group_code]) {
          groups[item.group_code] = [];
        }
        groups[item.group_code].push(item);
        return groups;
      }, {}),
    );

    return SETTINGS_GROUP_ORDER.flatMap((groupCode) =>
      visibleGroups
        .filter(([currentGroupCode]) => currentGroupCode === groupCode)
        .map(([currentGroupCode, groupItems]) => [currentGroupCode, groupItems] as const),
    );
  }, [items]);

  function currentInputValue(item: AdminSetting) {
    if (Object.prototype.hasOwnProperty.call(draftValues, item.setting_key)) {
      return draftValues[item.setting_key];
    }
    if (item.is_secret) {
      return "";
    }
    if (item.value_type === "boolean") {
      return (item.value || "false").toLowerCase() === "true" ? "true" : "false";
    }
    return item.value || "";
  }

  function draftValueForSubmit(item: AdminSetting): string | boolean | null {
    const hasDraft = Object.prototype.hasOwnProperty.call(draftValues, item.setting_key);
    const nextValue = hasDraft ? draftValues[item.setting_key] : item.value || "";

    if (item.value_type === "boolean") {
      return nextValue === "true";
    }

    return nextValue;
  }

  async function saveSingleSetting(
    item: AdminSetting,
    value: string | boolean | null,
    options?: { quiet?: boolean },
  ) {
    const response = await fetch(
      `${API_PREFIX}/api/admin/settings/${encodeURIComponent(item.setting_key)}`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          value,
          updated_by_user_id: session?.user.id || null,
        }),
      },
    );

    if (!response.ok) {
      throw new Error((await response.text()) || `Failed to update ${item.label}`);
    }

    const updated = (await response.json()) as AdminSetting;
    setItems((current) =>
      current.map((currentItem) =>
        currentItem.setting_key === updated.setting_key ? updated : currentItem,
      ),
    );

    if (!options?.quiet) {
      setDraftValues((current) => {
        const next = { ...current };
        delete next[item.setting_key];
        return next;
      });
      setNotice(`Updated ${item.label}.`);
    }

    return updated;
  }

  async function saveSetting(item: AdminSetting) {
    if (!canManage || !item.is_editable) {
      return;
    }

    const hasDraft = Object.prototype.hasOwnProperty.call(draftValues, item.setting_key);
    if (!hasDraft && item.is_secret) {
      setNotice(`No new value entered for ${item.label}.`);
      return;
    }

    const nextValue = draftValueForSubmit(item);

    setError("");
    setNotice("");
    setSavingKeys((current) => ({ ...current, [item.setting_key]: true }));

    try {
      await saveSingleSetting(item, nextValue);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : `Failed to update ${item.label}.`);
    } finally {
      setSavingKeys((current) => ({ ...current, [item.setting_key]: false }));
    }
  }

  function openCreateEditor() {
    setEditorMode("create");
    setEditorDraft(createEmptyDraft());
    setError("");
    setNotice("");
    setValidationState({ status: "idle", message: "" });
  }

  function openEditEditor(item: AiRegistryItem) {
    setEditorMode("edit");
    setEditorDraft({
      id: item.id,
      name: item.name,
      apiKey: item.apiKey,
      baseUrl: item.baseUrl,
      model: item.model,
      timeoutMs: String(item.timeoutMs || 45000),
      services: [...item.services],
      enabled: item.enabled,
      isDefault: item.isDefault,
    });
    setError("");
    setNotice("");
    setValidationState({ status: "idle", message: "" });
  }

  function closeEditor() {
    setEditorDraft(null);
    setValidationState({ status: "idle", message: "" });
  }

  async function validateAiDraft(draft: AiRegistryDraft) {
    setValidationState({ status: "checking", message: "Checking API..." });

    const response = await fetch(`${API_PREFIX}/api/admin/settings/ai/validate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: draft.name.trim(),
        api_key: draft.apiKey.trim(),
        base_url: draft.baseUrl.trim(),
        model: draft.model.trim(),
        timeout_ms: Number(draft.timeoutMs || "45000"),
      }),
    });

    const body = await response.text();
    let parsedMessage = body;

    try {
      const json = JSON.parse(body) as { message?: string; detail?: string };
      parsedMessage = json.message || json.detail || body;
    } catch {
      parsedMessage = body;
    }

    if (!response.ok) {
      setValidationState({
        status: "failed",
        message: parsedMessage || "API validation failed.",
      });
      throw new Error(parsedMessage || "API validation failed.");
    }

    setValidationState({
      status: "passed",
      message: parsedMessage || "API verified successfully.",
    });
  }

  async function persistAiRegistry(nextRegistry: AiRegistryItem[]) {
    if (!aiRegistrySetting) {
      throw new Error("AI registry setting is not available yet. Reload the page after backend sync.");
    }

    const normalized = nextRegistry.map((item, index) => ({
      ...normalizeRegistryItem(item, index),
    }));

    const defaultIndex = normalized.findIndex((item) => item.isDefault);
    const effectiveDefaultIndex = defaultIndex >= 0 ? defaultIndex : 0;
    normalized.forEach((item, index) => {
      item.isDefault = index === effectiveDefaultIndex;
    });

    const primary = normalized[effectiveDefaultIndex];
    setRegistrySaving(true);
    setError("");
    setNotice("");

    try {
      await saveSingleSetting(aiRegistrySetting, JSON.stringify(normalized, null, 2), { quiet: true });

      const legacySettings = {
        baseUrl: items.find((item) => item.setting_key === LEGACY_AI_KEYS.baseUrl) || null,
        apiKey: items.find((item) => item.setting_key === LEGACY_AI_KEYS.apiKey) || null,
        model: items.find((item) => item.setting_key === LEGACY_AI_KEYS.model) || null,
        timeoutMs: items.find((item) => item.setting_key === LEGACY_AI_KEYS.timeoutMs) || null,
      };

      if (primary) {
        if (legacySettings.baseUrl) {
          await saveSingleSetting(legacySettings.baseUrl, primary.baseUrl, { quiet: true });
        }
        if (legacySettings.apiKey) {
          await saveSingleSetting(legacySettings.apiKey, primary.apiKey, { quiet: true });
        }
        if (legacySettings.model) {
          await saveSingleSetting(legacySettings.model, primary.model, { quiet: true });
        }
        if (legacySettings.timeoutMs) {
          await saveSingleSetting(legacySettings.timeoutMs, String(primary.timeoutMs), { quiet: true });
        }
      }

      setNotice("AI registry updated.");
      closeEditor();
    } finally {
      setRegistrySaving(false);
    }
  }

  async function saveAiRegistryDraft() {
    if (!editorDraft) {
      return;
    }

    if (!editorDraft.name.trim()) {
      setError("Provider name is required.");
      return;
    }
    if (!editorDraft.apiKey.trim()) {
      setError("API key is required.");
      return;
    }
    if (!editorDraft.baseUrl.trim()) {
      setError("Base URL is required.");
      return;
    }
    if (!editorDraft.baseUrl.startsWith("http://") && !editorDraft.baseUrl.startsWith("https://")) {
      setError("Base URL must start with http:// or https://");
      return;
    }

    const timeoutMs = Number(editorDraft.timeoutMs);
    if (!Number.isFinite(timeoutMs) || timeoutMs < 1000) {
      setError("Timeout must be a number greater than or equal to 1000.");
      return;
    }

    await validateAiDraft(editorDraft);

    let nextRegistry = aiRegistryItems.map((item) => ({ ...item }));
    const nextItem: AiRegistryItem = {
      id: editorDraft.id,
      name: editorDraft.name.trim(),
      apiKey: editorDraft.apiKey.trim(),
      baseUrl: editorDraft.baseUrl.trim(),
      model: editorDraft.model.trim(),
      timeoutMs,
      services: editorDraft.services,
      enabled: editorDraft.enabled,
      isDefault: editorDraft.isDefault,
    };

    if (editorMode === "create") {
      nextRegistry = [nextItem, ...nextRegistry];
    } else {
      nextRegistry = nextRegistry.map((item) => (item.id === nextItem.id ? nextItem : item));
    }

    if (nextItem.isDefault) {
      nextRegistry = nextRegistry.map((item) => ({
        ...item,
        isDefault: item.id === nextItem.id,
      }));
    }

    await persistAiRegistry(nextRegistry);
  }

  async function deleteAiProvider(providerId: string) {
    const nextRegistry = aiRegistryItems.filter((item) => item.id !== providerId);
    await persistAiRegistry(nextRegistry);
  }

  function renderSettingRow(item: AdminSetting) {
    const isSaving = Boolean(savingKeys[item.setting_key]);
    const isInteger = item.value_type === "integer";
    const isFloat = item.value_type === "float";
    const isBoolean = item.value_type === "boolean";
    const isJson = item.value_type === "json";
    const inputType = item.is_secret ? "password" : isInteger || isFloat ? "number" : "text";

    return (
      <div key={item.setting_key} className="rounded-[18px] border border-slate-200 bg-slate-50/70 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h4 className="text-base font-semibold text-slate-900">{item.label}</h4>
            <p className="mt-1 text-sm text-slate-500">{item.description || item.setting_key}</p>
            <p className="mt-2 text-xs font-medium text-slate-400">
              {item.setting_key}
              {item.updated_by_email ? ` · updated by ${item.updated_by_email}` : ""}
            </p>
          </div>
          <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
            {item.value_type}
          </span>
        </div>

        <div className="mt-4 grid gap-3 lg:grid-cols-[1fr_auto]">
          <div className="space-y-2">
            {isBoolean ? (
              <label className="flex h-11 items-center justify-between rounded-[14px] border border-slate-200 bg-white px-4 text-sm text-slate-800">
                <span>{currentInputValue(item) === "true" ? "Enabled" : "Disabled"}</span>
                <input
                  type="checkbox"
                  checked={currentInputValue(item) === "true"}
                  onChange={(event) =>
                    setDraftValues((current) => ({
                      ...current,
                      [item.setting_key]: event.target.checked ? "true" : "false",
                    }))
                  }
                  disabled={!canManage || !item.is_editable || isSaving}
                  className="h-4 w-4 rounded border-slate-300 text-slate-900"
                />
              </label>
            ) : isJson ? (
              <textarea
                value={currentInputValue(item)}
                onChange={(event) =>
                  setDraftValues((current) => ({
                    ...current,
                    [item.setting_key]: event.target.value,
                  }))
                }
                disabled={!canManage || !item.is_editable || isSaving}
                placeholder={item.value || "{}"}
                rows={5}
                className="min-h-[120px] w-full rounded-[14px] border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 outline-none transition focus:border-slate-400 disabled:bg-slate-100"
              />
            ) : (
              <input
                type={inputType}
                step={isFloat ? "0.01" : isInteger ? "1" : undefined}
                value={currentInputValue(item)}
                onChange={(event) =>
                  setDraftValues((current) => ({
                    ...current,
                    [item.setting_key]: event.target.value,
                  }))
                }
                disabled={!canManage || !item.is_editable || isSaving}
                placeholder={item.is_secret ? item.masked_value || "Not set" : item.value || "Empty"}
                className="h-11 w-full rounded-[14px] border border-slate-200 bg-white px-4 text-sm text-slate-800 outline-none transition focus:border-slate-400 disabled:bg-slate-100"
              />
            )}
          </div>

          <button
            type="button"
            onClick={() => {
              startTransition(() => {
                saveSetting(item).catch(() => undefined);
              });
            }}
            disabled={!canManage || !item.is_editable || isSaving}
            className="h-11 rounded-[14px] bg-slate-900 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {isSaving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <WorkspaceShell
      mode="settings"
      title="System Settings"
      subtitle="Manage global settings in a simpler admin layout."
      statusLabel={`${items.length} settings`}
    >
      {!canAccessAdmin ? (
        <section className="rounded-[24px] border border-amber-200 bg-amber-50 p-6 text-amber-900 shadow-sm">
          <h3 className="text-lg font-semibold">Administrator access required</h3>
          <p className="mt-2 text-sm">This account is not allowed to access Administration.</p>
        </section>
      ) : !canView ? (
        <section className="rounded-[24px] border border-amber-200 bg-amber-50 p-6 text-amber-900 shadow-sm">
          <h3 className="text-lg font-semibold">Settings permission required</h3>
          <p className="mt-2 text-sm">This account does not have permission to view or edit settings.</p>
        </section>
      ) : (
        <section className="space-y-6">
          <div className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-xl font-semibold text-slate-900">System settings</h3>
            <p className="mt-2 text-sm text-slate-600">
              This page only keeps global system settings. AI providers are managed as a compact list with add, edit, and delete actions.
            </p>
          </div>

          {error ? (
            <div className="rounded-[16px] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          ) : null}

          {notice ? (
            <div className="rounded-[16px] border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
              {notice}
            </div>
          ) : null}

          <div className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="text-xl font-semibold text-slate-900">AI keys</h3>
                <p className="mt-1 text-sm text-slate-500">One row per API key. Use edit to manage URL, model, timeout, and services.</p>
              </div>
              <button
                type="button"
                onClick={openCreateEditor}
                disabled={!canManage}
                className="rounded-[14px] bg-orange-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-orange-400 disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                Add API
              </button>
            </div>

            {!aiRegistrySetting ? (
              <div className="mb-4 rounded-[16px] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                `ai.providers_registry` has not been seeded by backend yet. The row below is a fallback built from the current legacy AI settings.
              </div>
            ) : null}

            <div className="space-y-3">
              {aiRegistryItems.map((item) => (
                <div key={item.id} className="rounded-[18px] border border-slate-200 bg-slate-50/70 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <h4 className="text-base font-semibold text-slate-900">{item.name}</h4>
                        {item.isDefault ? (
                          <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-700">
                            Default
                          </span>
                        ) : null}
                        {!item.enabled ? (
                          <span className="rounded-full border border-slate-200 bg-slate-100 px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                            Disabled
                          </span>
                        ) : null}
                      </div>
                      <p className="mt-2 text-sm text-slate-600">{maskSecret(item.apiKey)}</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {item.services.map((service) => (
                          <span
                            key={service}
                            className="rounded-full border border-slate-200 bg-white px-2 py-1 text-[11px] font-semibold text-slate-600"
                          >
                            {service}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => openEditEditor(item)}
                        disabled={!canManage}
                        className="rounded-[12px] border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-300 disabled:cursor-not-allowed disabled:bg-slate-100"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          startTransition(() => {
                            deleteAiProvider(item.id).catch((deleteError: unknown) => {
                              setError(deleteError instanceof Error ? deleteError.message : "Unable to delete API.");
                            });
                          });
                        }}
                        disabled={!canManage || registrySaving || aiRegistryItems.length <= 1}
                        className="rounded-[12px] border border-rose-200 bg-white px-3 py-2 text-sm font-semibold text-rose-700 transition hover:border-rose-300 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {editorDraft ? (
            <div className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm">
              <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="text-xl font-semibold text-slate-900">
                    {editorMode === "create" ? "Add AI key" : `Edit ${editorDraft.name || "AI key"}`}
                  </h3>
                  <p className="mt-1 text-sm text-slate-500">
                    URL, model, timeout, and services stay inside the editor so the list remains compact.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={closeEditor}
                  className="rounded-[12px] border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700"
                >
                  Close
                </button>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <label className="space-y-2 text-sm">
                  <span className="font-semibold text-slate-900">Name</span>
                  <input
                    value={editorDraft.name}
                    onChange={(event) => setEditorDraft((current) => (current ? { ...current, name: event.target.value } : current))}
                    className="h-11 w-full rounded-[14px] border border-slate-200 bg-white px-4 text-sm text-slate-800 outline-none transition focus:border-slate-400"
                  />
                </label>
                <label className="space-y-2 text-sm">
                  <span className="font-semibold text-slate-900">API key</span>
                  <input
                    value={editorDraft.apiKey}
                    onChange={(event) => setEditorDraft((current) => (current ? { ...current, apiKey: event.target.value } : current))}
                    className="h-11 w-full rounded-[14px] border border-slate-200 bg-white px-4 text-sm text-slate-800 outline-none transition focus:border-slate-400"
                  />
                </label>
                <label className="space-y-2 text-sm">
                  <span className="font-semibold text-slate-900">Base URL</span>
                  <input
                    value={editorDraft.baseUrl}
                    onChange={(event) => setEditorDraft((current) => (current ? { ...current, baseUrl: event.target.value } : current))}
                    className="h-11 w-full rounded-[14px] border border-slate-200 bg-white px-4 text-sm text-slate-800 outline-none transition focus:border-slate-400"
                  />
                </label>
                <label className="space-y-2 text-sm">
                  <span className="font-semibold text-slate-900">Model</span>
                  <input
                    value={editorDraft.model}
                    onChange={(event) => setEditorDraft((current) => (current ? { ...current, model: event.target.value } : current))}
                    className="h-11 w-full rounded-[14px] border border-slate-200 bg-white px-4 text-sm text-slate-800 outline-none transition focus:border-slate-400"
                  />
                </label>
                <label className="space-y-2 text-sm">
                  <span className="font-semibold text-slate-900">Timeout (ms)</span>
                  <input
                    type="number"
                    min="1000"
                    value={editorDraft.timeoutMs}
                    onChange={(event) => setEditorDraft((current) => (current ? { ...current, timeoutMs: event.target.value } : current))}
                    className="h-11 w-full rounded-[14px] border border-slate-200 bg-white px-4 text-sm text-slate-800 outline-none transition focus:border-slate-400"
                  />
                </label>
                <div className="space-y-2 text-sm">
                  <span className="font-semibold text-slate-900">Status</span>
                  <div className="grid gap-2 sm:grid-cols-2">
                    <label className="flex items-center gap-2 rounded-[14px] border border-slate-200 bg-white px-4 py-3">
                      <input
                        type="checkbox"
                        checked={editorDraft.enabled}
                        onChange={(event) => setEditorDraft((current) => (current ? { ...current, enabled: event.target.checked } : current))}
                      />
                      <span>Enabled</span>
                    </label>
                    <label className="flex items-center gap-2 rounded-[14px] border border-slate-200 bg-white px-4 py-3">
                      <input
                        type="checkbox"
                        checked={editorDraft.isDefault}
                        onChange={(event) => setEditorDraft((current) => (current ? { ...current, isDefault: event.target.checked } : current))}
                      />
                      <span>Default</span>
                    </label>
                  </div>
                </div>
              </div>

              <div className="mt-4 space-y-2 text-sm">
                <span className="font-semibold text-slate-900">Services</span>
                <div className="grid gap-2 md:grid-cols-2">
                  {SERVICE_OPTIONS.map((service) => {
                    const checked = editorDraft.services.includes(service.value);
                    return (
                      <label
                        key={service.value}
                        className="flex items-center gap-2 rounded-[14px] border border-slate-200 bg-white px-4 py-3"
                      >
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(event) =>
                            setEditorDraft((current) => {
                              if (!current) {
                                return current;
                              }
                              const nextServices = event.target.checked
                                ? [...current.services, service.value]
                                : current.services.filter((item) => item !== service.value);
                              return { ...current, services: nextServices };
                            })
                          }
                        />
                        <span>{service.label}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              {validationState.message ? (
                <div
                  className={`mt-4 rounded-[14px] px-4 py-3 text-sm ${
                    validationState.status === "failed"
                      ? "border border-rose-200 bg-rose-50 text-rose-700"
                      : validationState.status === "passed"
                        ? "border border-emerald-200 bg-emerald-50 text-emerald-700"
                        : "border border-slate-200 bg-slate-50 text-slate-600"
                  }`}
                >
                  {validationState.message}
                </div>
              ) : null}

              <div className="mt-5 flex flex-wrap justify-end gap-3">
                <button
                  type="button"
                  onClick={closeEditor}
                  className="rounded-[12px] border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => {
                    startTransition(() => {
                      saveAiRegistryDraft().catch((saveError: unknown) => {
                        setError(saveError instanceof Error ? saveError.message : "Unable to save AI key.");
                      });
                    });
                  }}
                  disabled={!canManage || registrySaving || validationState.status === "checking"}
                  className="rounded-[12px] bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
                >
                  {validationState.status === "checking"
                    ? "Checking..."
                    : registrySaving
                      ? "Saving..."
                      : editorMode === "create"
                        ? "Create API"
                        : "Save changes"}
                </button>
              </div>
            </div>
          ) : null}

          {groupedItems.map(([groupCode, groupItems]) => {
            const groupMeta = GROUP_META[groupCode] || {
              title: groupCode,
              description: "Settings group",
            };
            const isExpanded = expandedGroups[groupCode] ?? false;

            return (
              <div key={groupCode} className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm">
                <button
                  type="button"
                  onClick={() =>
                    setExpandedGroups((current) => ({
                      ...current,
                      [groupCode]: !isExpanded,
                    }))
                  }
                  className="flex w-full items-start justify-between gap-4 text-left"
                >
                  <div>
                    <h3 className="text-xl font-semibold text-slate-900">{groupMeta.title}</h3>
                    <p className="mt-1 text-sm text-slate-500">{groupMeta.description}</p>
                  </div>
                  <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-500">
                    {isExpanded ? "Collapse" : "Expand"}
                  </span>
                </button>

                {isExpanded ? <div className="mt-5 space-y-4">{groupItems.map((item) => renderSettingRow(item))}</div> : null}
              </div>
            );
          })}

          {isPending ? <div className="text-sm text-slate-500">Reloading settings...</div> : null}
        </section>
      )}
    </WorkspaceShell>
  );
}
