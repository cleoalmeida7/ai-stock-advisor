import { InstrumentAnalysisView } from "@/components/InstrumentAnalysisView";

// This route is entirely client-rendered and gated on the caller's own
// session token fetched at runtime - it can never be statically
// prerendered. `instant` is a route segment config, so it has to live in
// this Server Component wrapper, not in the "use client" view it renders.
export const instant = false;

interface PageProps {
  params: Promise<{ instrumentId: string }>;
}

export default async function InstrumentAnalysisPage({ params }: PageProps) {
  const { instrumentId } = await params;
  return <InstrumentAnalysisView instrumentId={instrumentId} />;
}
