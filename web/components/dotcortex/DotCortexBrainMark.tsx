"use client";

/**
 * Engraved brain mark for the empty-chat greeting.
 * Keep it modest (≈56px) beside the greeting — DeepTutor pins this row
 * just above the composer (`items-end`); a tall hero logo overlaps the input.
 */
export function DotCortexBrainMark({
  className = "h-14 w-14",
}: {
  className?: string;
}) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src="/logo.png"
      alt="DotCortex"
      width={56}
      height={56}
      draggable={false}
      className={`shrink-0 select-none rounded-xl object-cover drop-shadow-[0_4px_16px_rgba(255,107,0,0.3)] ${className}`}
    />
  );
}
