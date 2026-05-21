import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatusBadge, TypeBadge } from "@/components/Badges";

describe("TypeBadge", () => {
  it("renders friendly label for known types", () => {
    render(<TypeBadge type="phrasal_verb" />);
    expect(screen.getByText("PHRASAL VERB")).toBeInTheDocument();
  });

  it.each([
    ["word", "WORD"],
    ["idiom", "IDIOM"],
    ["collocation", "COLLOCATION"],
    ["expression", "EXPRESSION"],
  ])("labels '%s' as '%s'", (input, label) => {
    render(<TypeBadge type={input} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it("falls back to gray for unknown type", () => {
    const { container } = render(<TypeBadge type="unicorn" />);
    expect(container.firstChild).toHaveClass("bg-gray-100");
  });
});

describe("StatusBadge", () => {
  it.each([
    ["pending", "PENDING", "bg-amber-100"],
    ["in_progress", "IN PROGRESS", "bg-orange-100"],
    ["learned", "LEARNED", "bg-green-100"],
    ["suspended", "SUSPENDED", "bg-gray-100"],
  ])("'%s' renders '%s' with %s", (status, label, klass) => {
    const { container } = render(<StatusBadge status={status} />);
    expect(screen.getByText(label)).toBeInTheDocument();
    expect(container.firstChild).toHaveClass(klass);
  });
});
