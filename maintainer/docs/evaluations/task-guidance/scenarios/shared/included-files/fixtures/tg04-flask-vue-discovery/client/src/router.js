import { createRouter, createWebHistory } from "vue-router";
import Books from "./components/Books.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: "/books", component: Books }],
});
