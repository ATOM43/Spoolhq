/** "1,180 words". */
export function wordCount(text: string): string {
  const words = text.trim() === "" ? 0 : text.trim().split(/\s+/).length;
  return `${words.toLocaleString()} ${words === 1 ? "word" : "words"}`;
}
