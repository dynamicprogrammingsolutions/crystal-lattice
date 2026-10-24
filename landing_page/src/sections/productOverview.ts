import ProductOverview from "../components/ProductOverview.astro";

export const productOverviewSection = {
  type: "productOverview",
  Component: ProductOverview,
} as const;