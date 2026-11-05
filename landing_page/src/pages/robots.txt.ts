import type { APIRoute } from "astro";
import { isStagingSite } from "../../site-variant.mjs";

export const prerender = true;

export const GET: APIRoute = () => {
  const body = isStagingSite
    ? "User-agent: *\nDisallow: /\n"
    : "User-agent: *\nAllow: /\n";
  return new Response(body, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
    },
  });
};