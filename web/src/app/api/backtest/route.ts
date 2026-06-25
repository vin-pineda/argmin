import { proxy } from "@/lib/api/proxy";

export async function POST(req: Request): Promise<Response> {
  const body = await req.text();
  return proxy("/backtest", { method: "POST", body });
}
