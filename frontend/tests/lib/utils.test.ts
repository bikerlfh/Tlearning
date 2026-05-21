import { describe, expect, it } from "vitest";
import { cn } from "@/lib/utils";

describe("cn", () => {
  it("merges class names with a single space", () => {
    expect(cn("p-2", "bg-red-500")).toBe("p-2 bg-red-500");
  });

  it("dedupes conflicting Tailwind utilities (last wins)", () => {
    expect(cn("p-2", "p-4")).toBe("p-4");
  });

  it("ignores falsy values", () => {
    expect(cn("p-2", null, undefined, false && "skipped")).toBe("p-2");
  });

  it("flattens nested arrays of classes", () => {
    expect(cn(["p-2", "m-2"], "bg-white")).toBe("p-2 m-2 bg-white");
  });
});
