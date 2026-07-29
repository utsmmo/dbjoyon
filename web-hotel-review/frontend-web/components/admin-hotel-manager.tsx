"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import { WorkspaceShell } from "@/components/workspace-shell";
import type { AdminHotel, HotelLinks, PaginatedResponse } from "@/lib/types";

const OTA_FIELDS = ["booking", "agoda", "google", "traveloka", "expedia", "ctrip"] as const;
const API_PREFIX = process.env.NEXT_PUBLIC_BASE_PATH || "";

type HotelFormState = {
  id: string | null;
  hotel_code: string;
  hotel_name: string;
  city: string;
  country_code: string;
  status: "active" | "inactive";
  links: Record<(typeof OTA_FIELDS)[number], string>;
};

const EMPTY_FORM: HotelFormState = {
  id: null,
  hotel_code: "",
  hotel_name: "",
  city: "",
  country_code: "VN",
  status: "active",
  links: {
    booking: "",
    agoda: "",
    google: "",
    traveloka: "",
    expedia: "",
    ctrip: "",
  },
};

function hotelLinksFromMetadata(hotel: AdminHotel): HotelLinks {
  return hotel.metadata?.source_links ?? {};
}

function serializeLinks(form: HotelFormState): HotelLinks {
  const result: HotelLinks = {};
  for (const ota of OTA_FIELDS) {
    const lines = form.links[ota]
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
    if (lines.length) {
      result[ota] = lines;
    }
  }
  return result;
}

function formFromHotel(hotel: AdminHotel): HotelFormState {
  const links = hotelLinksFromMetadata(hotel);
  return {
    id: hotel.id,
    hotel_code: hotel.hotel_code,
    hotel_name: hotel.hotel_name,
    city: hotel.city ?? "",
    country_code: hotel.country_code ?? "VN",
    status: hotel.status === "inactive" ? "inactive" : "active",
    links: {
      booking: (links.booking ?? []).join("\n"),
      agoda: (links.agoda ?? []).join("\n"),
      google: (links.google ?? []).join("\n"),
      traveloka: (links.traveloka ?? []).join("\n"),
      expedia: (links.expedia ?? []).join("\n"),
      ctrip: (links.ctrip ?? []).join("\n"),
    },
  };
}

export function AdminHotelManager() {
  const [hotels, setHotels] = useState<AdminHotel[]>([]);
  const [form, setForm] = useState<HotelFormState>(EMPTY_FORM);
  const [error, setError] = useState<string>("");
  const [notice, setNotice] = useState<string>("");
  const [isPending, startTransition] = useTransition();

  async function loadHotels() {
    const response = await fetch(`${API_PREFIX}/api/hotels?limit=200&offset=0`, { cache: "no-store" });
    const payload = (await response.json()) as PaginatedResponse<AdminHotel>;
    setHotels(payload.items);
  }

  useEffect(() => {
    startTransition(() => {
      loadHotels().catch((loadError: unknown) => {
        setError(loadError instanceof Error ? loadError.message : "Failed to load hotels");
      });
    });
  }, []);

  const sortedHotels = useMemo(
    () => [...hotels].sort((a, b) => a.hotel_name.localeCompare(b.hotel_name)),
    [hotels],
  );

  async function submitHotel() {
    setError("");
    setNotice("");

    const payload = {
      hotel_code: form.hotel_code.trim(),
      hotel_name: form.hotel_name.trim(),
      city: form.city.trim() || null,
      country_code: form.country_code.trim() || null,
      status: form.status,
      metadata: {},
      links: serializeLinks(form),
    };

    const isEditing = Boolean(form.id);
    const response = await fetch(
      isEditing ? `${API_PREFIX}/api/hotels/${form.id}` : `${API_PREFIX}/api/hotels`,
      {
      method: isEditing ? "PUT" : "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      },
    );

    if (!response.ok) {
      const body = await response.text();
      throw new Error(body || "Failed to save hotel");
    }

    await loadHotels();
    setForm(EMPTY_FORM);
    setNotice(isEditing ? "Hotel updated." : "Hotel created.");
  }

  async function deleteHotel(hotel: AdminHotel) {
    if (!window.confirm(`Delete ${hotel.hotel_name}?`)) {
      return;
    }
    setError("");
    setNotice("");

    const response = await fetch(`${API_PREFIX}/api/hotels/${hotel.id}`, { method: "DELETE" });
    if (!response.ok) {
      const body = await response.text();
      throw new Error(body || "Failed to delete hotel");
    }

    await loadHotels();
    if (form.id === hotel.id) {
      setForm(EMPTY_FORM);
    }
    setNotice(`Deleted ${hotel.hotel_name}.`);
  }

  return (
    <WorkspaceShell
      mode="admin"
      title="Hotel Administration"
      subtitle="Clean the hotel list, maintain internal names, and manage OTA links from one panel."
      statusLabel={`${hotels.length} hotels`}
    >
      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm">
          <div>
            <h3 className="text-xl font-semibold text-slate-900">Current hotel list</h3>
            <p className="mt-1 text-sm text-slate-500">
              Internal names come from business. OTA names can differ.
            </p>
            <div className="mt-4 rounded-[16px] border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-900">
              <p className="font-semibold">Data rule</p>
              <p className="mt-1">
                One hotel here means one internal hotel record. Each OTA can contain many links, and each link is
                only a crawl source, not a new hotel.
              </p>
            </div>
          </div>

          <div className="mt-5 space-y-3">
            {sortedHotels.map((hotel) => {
              const links = hotelLinksFromMetadata(hotel);
              return (
                <div key={hotel.id} className="rounded-[18px] border border-slate-200 bg-slate-50/70 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h4 className="text-lg font-semibold text-slate-900">{hotel.hotel_name}</h4>
                      <p className="mt-1 text-sm text-slate-500">
                        {hotel.hotel_code} · {hotel.city ?? "No city"} · {hotel.status}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setForm(formFromHotel(hotel))}
                        className="rounded-[10px] border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          startTransition(() => {
                            deleteHotel(hotel).catch((actionError: unknown) => {
                              setError(actionError instanceof Error ? actionError.message : "Delete failed");
                            });
                          });
                        }}
                        className="rounded-[10px] border border-rose-200 bg-white px-3 py-2 text-sm font-semibold text-rose-700"
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    {OTA_FIELDS.map((ota) => (
                      <div key={ota} className="rounded-[14px] border border-slate-200 bg-white p-3">
                        <div className="flex items-center justify-between gap-3">
                          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{ota}</p>
                          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">
                            {(links[ota] ?? []).length} link{(links[ota] ?? []).length === 1 ? "" : "s"}
                          </span>
                        </div>
                        <div className="mt-2 space-y-2 text-sm text-slate-600">
                          {(links[ota] ?? []).length ? (
                            (links[ota] ?? []).map((link, index) => (
                              <div key={link} className="rounded-[12px] border border-slate-100 bg-slate-50 px-3 py-2">
                                <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">
                                  Link {index + 1}
                                </p>
                                <p className="mt-1 break-all text-slate-700">{link}</p>
                              </div>
                            ))
                          ) : (
                            <p className="text-slate-400">No link</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h3 className="text-xl font-semibold text-slate-900">
                {form.id ? "Edit hotel" : "Add hotel"}
              </h3>
              <p className="mt-1 text-sm text-slate-500">
                Add internal hotel info first, then maintain OTA links below.
              </p>
              <p className="mt-2 text-sm text-slate-500">
                Use one line per link. Multiple Booking links still belong to the same hotel record.
              </p>
            </div>
            {form.id ? (
              <button
                type="button"
                onClick={() => setForm(EMPTY_FORM)}
                className="rounded-[10px] border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700"
              >
                New
              </button>
            ) : null}
          </div>

          {error ? (
            <div className="mt-4 rounded-[14px] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          ) : null}
          {notice ? (
            <div className="mt-4 rounded-[14px] border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
              {notice}
            </div>
          ) : null}

          <div className="mt-5 grid gap-4">
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              Hotel code
              <input
                value={form.hotel_code}
                onChange={(event) => setForm((current) => ({ ...current, hotel_code: event.target.value }))}
                className="rounded-[12px] border border-slate-200 px-4 py-3 outline-none transition focus:border-slate-400"
              />
            </label>
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              Hotel name
              <input
                value={form.hotel_name}
                onChange={(event) => setForm((current) => ({ ...current, hotel_name: event.target.value }))}
                className="rounded-[12px] border border-slate-200 px-4 py-3 outline-none transition focus:border-slate-400"
              />
            </label>
            <div className="grid gap-4 md:grid-cols-3">
              <label className="grid gap-2 text-sm font-medium text-slate-700">
                City
                <input
                  value={form.city}
                  onChange={(event) => setForm((current) => ({ ...current, city: event.target.value }))}
                  className="rounded-[12px] border border-slate-200 px-4 py-3 outline-none transition focus:border-slate-400"
                />
              </label>
              <label className="grid gap-2 text-sm font-medium text-slate-700">
                Country
                <input
                  value={form.country_code}
                  onChange={(event) => setForm((current) => ({ ...current, country_code: event.target.value }))}
                  className="rounded-[12px] border border-slate-200 px-4 py-3 outline-none transition focus:border-slate-400"
                />
              </label>
              <label className="grid gap-2 text-sm font-medium text-slate-700">
                Status
                <select
                  value={form.status}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      status: event.target.value === "inactive" ? "inactive" : "active",
                    }))
                  }
                  className="rounded-[12px] border border-slate-200 px-4 py-3 outline-none transition focus:border-slate-400"
                >
                  <option value="active">active</option>
                  <option value="inactive">inactive</option>
                </select>
              </label>
            </div>

            <div className="grid gap-4">
              {OTA_FIELDS.map((ota) => (
                <label key={ota} className="grid gap-2 text-sm font-medium text-slate-700">
                  {ota.toUpperCase()} links
                  <textarea
                    value={form.links[ota]}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        links: {
                          ...current.links,
                          [ota]: event.target.value,
                        },
                      }))
                    }
                    rows={3}
                    placeholder={`One link per line for ${ota}`}
                    className="rounded-[12px] border border-slate-200 px-4 py-3 outline-none transition focus:border-slate-400"
                  />
                  <span className="text-xs font-normal text-slate-500">
                    One link = one crawl source. Do not create a new hotel just because this OTA has multiple links.
                  </span>
                </label>
              ))}
            </div>

            <button
              type="button"
              onClick={() => {
                startTransition(() => {
                  submitHotel().catch((actionError: unknown) => {
                    setError(actionError instanceof Error ? actionError.message : "Save failed");
                  });
                });
              }}
              className="rounded-[14px] bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
              disabled={isPending}
            >
              {form.id ? "Update hotel" : "Create hotel"}
            </button>
          </div>
        </div>
      </section>
    </WorkspaceShell>
  );
}
