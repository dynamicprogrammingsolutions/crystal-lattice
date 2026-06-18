import MobileHero from "../components/mobile/Hero.astro";

export const mobileHeroSection = {
  type: "mobileHero",
  Component: MobileHero,
} as const;
