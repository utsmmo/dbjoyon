import { NextRequest, NextResponse } from "next/server";
import { getServerApiBaseUrl } from "@/lib/server-api";

const API_BASE_URL = getServerApiBaseUrl();

type RouteContext = {
  params: Promise<{ userId: string }>;
};

export async function PUT(request: NextRequest, context: RouteContext) {
  const { userId } = await context.params;
  const url = new URL(`/api/v1/admin/users/${userId}`, API_BASE_URL);
  const body = await request.text();
  const response = await fetch(url.toString(), {
    method: "PUT",
    cache: "no-store",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body,
  });

  const responseBody = await response.text();
  return new NextResponse(responseBody, {
    status: response.status,
    headers: {
      "content-type": response.headers.get("content-type") || "application/json",
    },
  });
}

export async function DELETE(_request: NextRequest, context: RouteContext) {
  const { userId } = await context.params;
  const url = new URL(`/api/v1/admin/users/${userId}`, API_BASE_URL);
  const response = await fetch(url.toString(), {
    method: "DELETE",
    cache: "no-store",
    headers: {
      Accept: "application/json",
    },
  });

  const responseBody = await response.text();
  return new NextResponse(responseBody, {
    status: response.status,
    headers: {
      "content-type": response.headers.get("content-type") || "application/json",
    },
  });
}
