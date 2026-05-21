import { Badge } from "@/components/ui/badge";

const TYPE_STYLES: Record<string, string> = {
  word: "bg-blue-100 text-blue-800",
  phrasal_verb: "bg-violet-100 text-violet-800",
  idiom: "bg-pink-100 text-pink-800",
  collocation: "bg-teal-100 text-teal-800",
  expression: "bg-indigo-100 text-indigo-800",
};

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-amber-100 text-amber-800",
  in_progress: "bg-orange-100 text-orange-800",
  learned: "bg-green-100 text-green-800",
  suspended: "bg-gray-100 text-gray-800",
};

function formatLabel(value: string) {
  return value.replace(/_/g, " ").toUpperCase();
}

export function TypeBadge({ type }: { type: string }) {
  return (
    <Badge variant="outline" className={TYPE_STYLES[type] ?? "bg-gray-100"}>
      {formatLabel(type)}
    </Badge>
  );
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <Badge variant="outline" className={STATUS_STYLES[status] ?? "bg-gray-100"}>
      {formatLabel(status)}
    </Badge>
  );
}
