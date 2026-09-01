export function PageHero({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  children?: React.ReactNode;
}) {
  return (
    <section className="border-b border-[var(--line)] bg-white">
      <div className="mx-auto max-w-6xl px-4 py-16 lg:px-6 lg:py-20">
        {eyebrow && (
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--moss)]">{eyebrow}</p>
        )}
        <h1 className="mt-2 max-w-3xl text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl lg:text-5xl">
          {title}
        </h1>
        {description && <p className="mt-4 max-w-2xl text-lg text-slate-600">{description}</p>}
        {children && <div className="mt-8 flex flex-wrap gap-3">{children}</div>}
      </div>
    </section>
  );
}
