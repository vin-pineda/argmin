import { proxy } from "@/lib/api/proxy";

export async function GET(req: Request): Promise<Response> {
  const { searchParams } = new URL(req.url);
  const params: Record<string, string> = {};
  const universe = searchParams.get("universe");
  const asOf = searchParams.get("as_of");
  if (universe) params.universe = universe;
  if (asOf) params.as_of = asOf;
  return proxy("/frontier", { method: "GET", searchParams: params });
}
