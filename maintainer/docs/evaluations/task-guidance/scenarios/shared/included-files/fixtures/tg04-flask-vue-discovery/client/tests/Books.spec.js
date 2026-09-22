import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import Books from "../src/components/Books.vue";

vi.mock("../src/api/books", () => ({
  getBooks: vi.fn(async () => ({ data: { books: [] } })),
  addBook: vi.fn(),
  updateBook: vi.fn(),
  deleteBook: vi.fn(),
}));

describe("Books", () => {
  it("renders the empty state", async () => {
    const wrapper = mount(Books);
    await Promise.resolve();
    expect(wrapper.text()).toContain("No books found.");
  });
});
