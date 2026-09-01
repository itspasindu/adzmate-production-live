import Link from "next/link";
import { APP_HOME } from "@/lib/routes";

export function CtaBand({
  title = "Ready to put your campaigns on auto-pilot?",
  description = "Upload a product photo, let agents decide, and publish to Meta with full control.",
}: {
  title?: string;
  description?: string;
}) {
  return (
    <section className="bg-[var(--sidebar)] py-16 text-white lg:py-20">
      <div className="mx-auto max-w-6xl px-4 text-center lg:px-6">
        <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">{title}</h2>
        <p className="mx-auto mt-3 max-w-xl text-slate-300">{description}</p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Link href="/signup" className="btn-primary bg-white text-[var(--moss)] hover:bg-slate-100">
            Get started free
          </Link>
          <Link
            href={APP_HOME}
            className="inline-flex items-center justify-center rounded-lg border border-white/20 px-3.5 py-2 text-sm font-medium text-white transition hover:bg-white/10"
          >
            Open dashboard
          </Link>
        </div>
      </div>
    </section>
  );
}
