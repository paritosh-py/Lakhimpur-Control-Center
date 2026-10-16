export interface AnalysisResult {
  reconstructed: string;
  urgency: number;
  category: string;
}

export async function reconstructSignal(
  text: string, 
  victimName?: string, 
  manualLocation?: string
): Promise<AnalysisResult> {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) throw new Error("API Key not configured.");

  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`;
  
  const ctx = `
    VICTIM NAME: ${victimName || "Unknown"}
    REPORTED LOCATION: ${manualLocation || "Not specified"}
  `;

  let geminiResponse: Response;
  try {
    geminiResponse = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: `
          Emergency Response AI Analyst.
          Context: ${ctx}
          Signal Extraction: "${text}"

          Task:
          1. Reconstruct fragmented signal into professional clean text.
          2. Categorize (e.g. Trauma, Fire, Drowning).
          3. Score urgency (1-10).
        ` }] }],
        generationConfig: {
          responseMimeType: "application/json",
          responseSchema: {
            type: "OBJECT",
            properties: {
              reconstructed: { type: "STRING" },
              urgency: { type: "INTEGER" },
              category: { type: "STRING" }
            },
            required: ["reconstructed", "urgency", "category"]
          }
        }
      })
    });
  } catch (error) {
    console.error("Gemini intelligence request failed:", error);
    throw new Error("The AI service is unreachable from the AeroLink server. Check the server internet connection and retry.");
  }

  const data = await geminiResponse.json();
  if (data.error) throw new Error(data.error.message);
  
  // Gemini 2.5 Flash returns thinking tokens in earlier parts (thought: true).
  // The actual JSON response is in a non-thought part.
  const parts = data.candidates?.[0]?.content?.parts;
  if (!parts || parts.length === 0) throw new Error("Empty response from intelligence engine");
  
  // Find the first non-thought text part
  const textPart = parts.find((p: { thought?: boolean; text?: string }) => !p.thought && p.text);
  const textResponse = textPart?.text;
  
  if (!textResponse) throw new Error("No text response from intelligence engine");
  
  // Try direct parse first, then extract JSON object if wrapped in markdown/extra text
  try {
    return JSON.parse(textResponse.trim());
  } catch {
    const jsonMatch = textResponse.match(/\{[\s\S]*\}/);
    if (jsonMatch) return JSON.parse(jsonMatch[0]);
    throw new Error("Failed to parse intelligence response as JSON");
  }
}
