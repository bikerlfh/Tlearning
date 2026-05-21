const LANG_MAP: Record<string, string> = {
  en: "en-US",
  es: "es-ES",
  fr: "fr-FR",
  de: "de-DE",
  it: "it-IT",
  pt: "pt-PT",
  ja: "ja-JP",
  zh: "zh-CN",
};

function bcp47For(lang: string | undefined | null): string {
  if (!lang) return "en-US";
  const lower = lang.toLowerCase();
  return LANG_MAP[lower] ?? (lower.includes("-") ? lower : `${lower}-${lower.toUpperCase()}`);
}

export function ttsAvailable(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

export function speak(text: string, lang?: string | null): boolean {
  if (!ttsAvailable() || !text) return false;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = bcp47For(lang);
  window.speechSynthesis.speak(u);
  return true;
}
