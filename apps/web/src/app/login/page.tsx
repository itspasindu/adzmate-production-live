import { Suspense } from "react";
import LoginPage from "./LoginForm";

export default function Page() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-paper text-sm text-slate-500">
          Loading…
        </div>
      }
    >
      <LoginPage />
    </Suspense>
  );
}
