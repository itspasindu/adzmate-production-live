export function FeatureIcon({ name }: { name: string }) {
  const cls = "h-5 w-5 text-[var(--moss)]";
  switch (name) {
    case "agents":
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="none" stroke="currentColor" strokeWidth="1.75">
          <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z" strokeLinejoin="round" />
          <path d="M5 19l1 2M19 17l1 2" strokeLinecap="round" />
        </svg>
      );
    case "shield":
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="none" stroke="currentColor" strokeWidth="1.75">
          <path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z" strokeLinejoin="round" />
          <path d="M9 12l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "meta":
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="none" stroke="currentColor" strokeWidth="1.75">
          <path d="M4 12h16M12 4v16" strokeLinecap="round" />
          <circle cx="12" cy="12" r="9" />
        </svg>
      );
    case "page":
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="none" stroke="currentColor" strokeWidth="1.75">
          <path d="M6 4h9l3 3v13H6V4z" strokeLinejoin="round" />
          <path d="M15 4v4h4M8 12h8M8 16h5" strokeLinecap="round" />
        </svg>
      );
    case "target":
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="none" stroke="currentColor" strokeWidth="1.75">
          <circle cx="12" cy="12" r="9" />
          <circle cx="12" cy="12" r="5" />
          <circle cx="12" cy="12" r="1" fill="currentColor" />
        </svg>
      );
    case "chart":
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="none" stroke="currentColor" strokeWidth="1.75">
          <path d="M4 19V5M4 19h16" strokeLinecap="round" />
          <path d="M8 15v-4M12 15V9M16 15v-7" strokeLinecap="round" />
        </svg>
      );
    case "workspace":
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="none" stroke="currentColor" strokeWidth="1.75">
          <path d="M3 9l9-5 9 5v11H3V9z" strokeLinejoin="round" />
          <path d="M9 22V12h6v10" strokeLinejoin="round" />
        </svg>
      );
    case "timeline":
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="none" stroke="currentColor" strokeWidth="1.75">
          <path d="M12 8v4l3 2M21 12a9 9 0 11-18 0 9 9 0 0118 0z" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    default:
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="none" stroke="currentColor" strokeWidth="1.75">
          <path d="M12 3l2 5 5 1-4 4 1 5-4-2-4 2 1-5-4-4 5-1 2-5z" strokeLinejoin="round" />
        </svg>
      );
  }
}
