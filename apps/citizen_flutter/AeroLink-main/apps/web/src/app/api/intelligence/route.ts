import { NextResponse } from "next/server";
import { reconstructSignal } from "@/lib/intelligence";
import { checkAuth } from "@/lib/auth";

// Intelligence-only analysis endpoint.
// Decodes garbled signals WITHOUT creating tickets or logging them as active signals.
// Used exclusively by the Intelligence tab for base camp analysis.
export async function POST(req: Request) {
  if (!(await checkAuth())) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  try {
    const body = await req.json();
    const { text } = body;

    if (!text?.trim()) {
      return NextResponse.json({ error: "Empty signal" }, { status: 400 });
    }

    const result = await reconstructSignal(text);

    return NextResponse.json({
      reconstructed: result.reconstructed,
      urgency: result.urgency,
      category: result.category,
    });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
