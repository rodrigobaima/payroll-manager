import { endOfWeek, format, startOfWeek } from "date-fns";

export function parseDateInput(value: string) {
  return new Date(`${value}T00:00:00.000Z`);
}

export function toDateInput(value: Date) {
  return format(value, "yyyy-MM-dd");
}

export function formatIrishDate(value: Date) {
  return new Intl.DateTimeFormat("en-IE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(value);
}

export function weekBounds(value: Date) {
  return {
    start: startOfWeek(value, { weekStartsOn: 1 }),
    end: endOfWeek(value, { weekStartsOn: 1 }),
  };
}

