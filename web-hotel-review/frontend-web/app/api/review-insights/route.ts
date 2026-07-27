import { NextRequest, NextResponse } from "next/server";

const REVIEW_AI_BASE_URL =
  process.env.REVIEW_AI_BASE_URL || "https://r7dnyxy.abc-tunnel.us/v1";
const REVIEW_AI_API_KEY =
  process.env.REVIEW_AI_API_KEY || "sk-51c6e48e4c4ececa-d4mh3m-307caa8c";
const REVIEW_AI_MODEL =
  process.env.REVIEW_AI_MODEL || "cx/gpt-5.4-mini-review";
const REVIEW_AI_TIMEOUT_MS = 45_000;

type InsightReview = {
  hotel_name: string;
  platform_code: string | null;
  reviewer_country_code: string | null;
  rating: number | null;
  rating_scale: number | null;
  reviewed_at: string;
  is_bad_review: boolean;
  title: string;
  body: string;
};

type InsightCategory = {
  label: string;
  value: number;
  scale: number;
};

type InsightPayload = {
  totalMatches: number;
  visibleReviewCount: number;
  filters: Record<string, string | string[] | boolean | null | undefined>;
  analyticsSummary?: Record<string, unknown> | null;
  countryBreakdown?: Array<{ label: string; value: number }>;
  hotelBreakdown?: Array<{ label: string; value: number }>;
  keywordSummary?: Array<{ label: string; value: number }>;
  categories?: InsightCategory[];
  reviews: InsightReview[];
};

function buildPrompt(payload: InsightPayload) {
  return [
    "Ban la chuyen gia van hanh khach san va phan tich review.",
    "Hay phan tich dung tren du lieu da loc, viet bang tieng Viet, ro rang, thuc dung, khong viet chung chung.",
    "Chi duoc dua tren du lieu duoc cung cap. Neu du lieu it thi phai noi ro do la mau nho.",
    "",
    "Yeu cau dinh dang:",
    "1. Tong quan ngan",
    "2. Van de chinh can khac phuc",
    "3. Uu tien hanh dong ngay",
    "4. Tin hieu can theo doi them",
    "",
    "Quy tac:",
    "- Neu co category score thi chi ra category nao yeu nhat va category nao tot nhat.",
    "- Neu co bad review thi neu ro nhom van de lap lai.",
    "- Neu tap review hien tai chi la mau hien thi, phai noi ro do la mau dang xem tren man hinh.",
    "- Uu tien de xuat hanh dong cu the cho team van hanh, le tan, housekeeping, phong, wifi, vi tri, pricing neu co dau hieu.",
    "- Khong chen markdown phuc tap. Chi dung van ban thuong, xuong dong ro rang.",
    "",
    "Du lieu dau vao:",
    JSON.stringify(payload),
  ].join("\n");
}

export async function POST(request: NextRequest) {
  const payload = (await request.json()) as InsightPayload;

  if (!REVIEW_AI_BASE_URL || !REVIEW_AI_API_KEY || !REVIEW_AI_MODEL) {
    return NextResponse.json(
      { message: "Review AI is not configured." },
      { status: 500 },
    );
  }

  if (!Array.isArray(payload.reviews) || payload.reviews.length === 0) {
    return NextResponse.json({
      content:
        "Chua co review nao trong tap du lieu dang loc, nen AI chua the dua ra nhan dinh co y nghia.",
    });
  }

  const response = await fetch(`${REVIEW_AI_BASE_URL}/chat/completions`, {
    method: "POST",
    cache: "no-store",
    signal: AbortSignal.timeout(REVIEW_AI_TIMEOUT_MS),
    headers: {
      Authorization: `Bearer ${REVIEW_AI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: REVIEW_AI_MODEL,
      temperature: 0.2,
      max_tokens: 900,
      messages: [
        {
          role: "system",
          content:
            "You are a Vietnamese review analyst. Always answer in Vietnamese, practical, evidence-based, concise but useful.",
        },
        {
          role: "user",
          content: buildPrompt(payload),
        },
      ],
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    return NextResponse.json(
      {
        message: "Review AI request failed.",
        detail: errorText,
      },
      { status: response.status },
    );
  }

  const data = (await response.json()) as {
    choices?: Array<{ message?: { content?: string } }>;
  };

  const content = data.choices?.[0]?.message?.content?.trim();

  return NextResponse.json({
    content:
      content ||
      "AI da nhan request nhung chua tra ve noi dung phan tich co the hien thi.",
  });
}
