import crypto from "crypto";

// Ensure key is exactly 32 bytes by padding or slicing it in a pre-allocated buffer
const RAW_KEY = process.env.ENCRYPTION_KEY || "emergency-dispatch-secure-key-32"; 
const ENCRYPTION_KEY = Buffer.alloc(32);
Buffer.from(RAW_KEY).copy(ENCRYPTION_KEY);

const IV_LENGTH = 16; 

export function encrypt(text: string): string {
  const iv = crypto.randomBytes(IV_LENGTH);
  const cipher = crypto.createCipheriv("aes-256-cbc", ENCRYPTION_KEY, iv);
  let encrypted = cipher.update(text);
  encrypted = Buffer.concat([encrypted, cipher.final()]);
  return iv.toString("hex") + ":" + encrypted.toString("hex");
}

export function decrypt(text: string): string {
  try {
    const textParts = text.split(":");
    const iv = Buffer.from(textParts.shift()!, "hex");
    const encryptedText = Buffer.from(textParts.join(":"), "hex");
    const decipher = crypto.createDecipheriv("aes-256-cbc", ENCRYPTION_KEY, iv);
    let decrypted = decipher.update(encryptedText);
    decrypted = Buffer.concat([decrypted, decipher.final()]);
    return decrypted.toString();
  } catch (err) {
    console.error("Decryption failed:", err);
    return text; // Fallback to raw if decryption fails (e.g. legacy data)
  }
}
