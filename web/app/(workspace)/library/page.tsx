import Link from "next/link";

import { BOOKS_HOME, READING_HOME } from "@/lib/learning-routes";

const LINKS = [
  { href: BOOKS_HOME, label: "Books" },
  { href: "/knowledge-bases", label: "Knowledge bases" },
  { href: "/notebooks", label: "Notebooks" },
  { href: READING_HOME, label: "Immersive Reading" },
  { href: "/space/chat-history", label: "Chat history" },
  { href: "/space/journal", label: "Learning journal" },
  { href: "/space/questions", label: "Question bank" },
];

export default function LibraryPage() {
  return (
    <div className="mx-auto flex h-full max-w-xl flex-col gap-4 overflow-auto px-6 py-8">
      <h1 className="text-2xl font-medium text-[var(--foreground)]">Library</h1>
      <p className="text-[14px] leading-relaxed text-[var(--muted-foreground)]">
        Materials and your record. A skill on Home can attach these. Personas, memory, and MCP stay under More.
      </p>
      <ul className="divide-y divide-[var(--border)] rounded-xl border border-[var(--border)]">
        {LINKS.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              className="block px-4 py-3 text-[14px] text-[var(--foreground)] hover:bg-[var(--muted)]"
            >
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
