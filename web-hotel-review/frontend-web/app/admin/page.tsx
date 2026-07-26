export default function AdminPlaceholderPage() {
  return (
    <main className="min-h-screen px-6 py-12 text-[#1e1a17]">
      <div className="mx-auto max-w-4xl rounded-[32px] border border-[var(--border)] bg-[var(--surface)] p-10 shadow-[var(--shadow)]">
        <p className="mb-4 text-sm uppercase tracking-[0.24em] text-[#a15e3b]">
          Phase 2
        </p>
        <h1 className="font-display text-4xl leading-tight">
          Admin panel will plug in here after auth and RBAC endpoints are ready.
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-7 text-[var(--muted)]">
          The dashboard route is live now. This admin route is reserved for the
          next phase once login, role checks, and CRUD endpoints are exposed by
          the backend.
        </p>
      </div>
    </main>
  );
}
