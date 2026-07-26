import { NextRequest, NextResponse } from "next/server";

type TranslationPayload = {
  texts: string[];
  target?: string;
};

type GoogleTranslateResponse = [string, string | null, string | null][];

async function translateText(text: string, target: string) {
  const url = new URL("https://translate.googleapis.com/translate_a/single");
  url.searchParams.set("client", "gtx");
  url.searchParams.set("sl", "auto");
  url.searchParams.set("tl", target);
  url.searchParams.set("dt", "t");
  url.searchParams.set("q", text);

  const response = await fetch(url.toString(), {
    cache: "no-store",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error("Translation provider request failed.");
  }

  const data = (await response.json()) as [GoogleTranslateResponse];
  return (data[0] || []).map((item) => item[0]).join("").trim();
}

export async function POST(request: NextRequest) {
  const body = (await request.json()) as TranslationPayload;
  const texts = Array.isArray(body.texts) ? body.texts.filter(Boolean) : [];
  const target = body.target || "vi";

  if (texts.length === 0) {
    return NextResponse.json({ items: [] });
  }

  const items = await Promise.all(
    texts.map(async (text) => ({
      source: text,
      translated: await translateText(text, target),
    })),
  );

  return NextResponse.json({ items });
}
