import { NextResponse } from "next/server";
import { getTickets, type Ticket } from "@/lib/db";
import { checkAuth } from "@/lib/auth";
import { analyzeTicket } from "@/lib/ticket-analysis";
import { isResolvedStatus } from "@/lib/ticket-status";

interface PrioritizationResult {
  sortedIds: string[];
  rationale: Array<{ id: string; reason: string }> | Record<string, string>;
}

export async function POST() {
  if (!(await checkAuth())) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  try {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) return NextResponse.json({ error: "API Key not configured." }, { status: 500 });

    const unresolvedIds = getTickets()
      .filter((ticket) => !isResolvedStatus(ticket.status))
      .map((ticket) => ticket.id);

    for (const ticketId of unresolvedIds) {
      await analyzeTicket(ticketId);
    }

    const tickets = getTickets().filter((ticket) => !isResolvedStatus(ticket.status));
    if (tickets.length === 0) return NextResponse.json([]);

    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`;
    
    let response: Response;
    try {
      response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: `
            Tactical Triage Officer Analysis.
            PROTOCOL:
            1. Tier 1 (minutes): Fire, Drowning, Trauma.
            2. Tier 2 (hours): Food, Water, Shelter.
            Tier 1 overrides Tier 2 regardless of count.

            TICKETS: ${JSON.stringify(tickets)}
          ` }] }],
          generationConfig: {
            responseMimeType: "application/json",
            responseSchema: {
              type: "OBJECT",
              properties: {
                sortedIds: {
                  type: "ARRAY",
                  items: { type: "STRING" }
                },
                rationale: {
                  type: "ARRAY",
                  items: {
                    type: "OBJECT",
                    properties: {
                      id: { type: "STRING" },
                      reason: { type: "STRING" }
                    },
                    required: ["id", "reason"]
                  }
                }
              },
              required: ["sortedIds", "rationale"]
            }
          }
        })
      });
    } catch (error) {
      console.error("Gemini prioritization request failed:", error);
      throw new Error("The AI service is unreachable from the AeroLink server. Check the server internet connection and retry.");
    }

    const data = await response.json();
    if (data.error) throw new Error(data.error.message);
    
    // Gemini 2.5 Flash returns thinking tokens in earlier parts (thought: true).
    const parts = data.candidates?.[0]?.content?.parts;
    if (!parts || parts.length === 0) throw new Error("Empty response from prioritization engine");
    const textPart = parts.find((p: { thought?: boolean; text?: string }) => !p.thought && p.text);
    const responseText = textPart?.text;
    if (!responseText) throw new Error("No text response from prioritization engine");
    
    let result: PrioritizationResult;
    try {
      result = JSON.parse(responseText.trim()) as PrioritizationResult;
    } catch {
      const jsonMatch = responseText.match(/\{[\s\S]*\}/);
      if (jsonMatch) result = JSON.parse(jsonMatch[0]) as PrioritizationResult;
      else throw new Error("Failed to parse prioritization response as JSON");
    }

    if (!Array.isArray(result.sortedIds) || !result.rationale || typeof result.rationale !== "object") {
      throw new Error("Invalid prioritization response");
    }

    const rationale = Array.isArray(result.rationale)
      ? Object.fromEntries(
          result.rationale
            .filter((item) => item && typeof item.id === "string" && typeof item.reason === "string")
            .map((item) => [item.id, item.reason])
        )
      : result.rationale;
    const rankedIds = [...new Set(result.sortedIds.filter((id): id is string => typeof id === "string"))];
    const prioritizedTickets: Array<Ticket & { tacticalReasoning?: string }> = [];
    for (const id of rankedIds) {
      const ticket = tickets.find((item) => item.id === id);
      if (ticket) prioritizedTickets.push({ ...ticket, tacticalReasoning: rationale[id] });
    }

    const missing = tickets
      .filter((ticket) => !rankedIds.includes(ticket.id))
      .sort((left, right) =>
        right.urgency - left.urgency ||
        new Date(left.timestamp).getTime() - new Date(right.timestamp).getTime()
      );
    return NextResponse.json([...prioritizedTickets, ...missing]);
  } catch (error: unknown) {
    console.error("Prioritization Error:", error);
    const message = error instanceof Error ? error.message : "Prioritization failed";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
