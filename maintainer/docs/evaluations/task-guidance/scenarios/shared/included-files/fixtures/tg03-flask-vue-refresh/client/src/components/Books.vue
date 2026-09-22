<template>
  <section>
    <nav aria-label="Book status filter">
      <button
        v-for="filter in ['all', 'read', 'unread']"
        :key="filter"
        :aria-pressed="selectedFilter === filter"
        @click="selectFilter(filter)"
      >
        {{ filter }}
      </button>
    </nav>
    <table v-if="books.length">
      <tr v-for="book in books" :key="book.id"><td>{{ book.title }}</td></tr>
    </table>
    <p v-else>No books found.</p>
  </section>
</template>

<script>
import { getBooks, addBook, updateBook, deleteBook } from "../api/books";

export default {
  data: () => ({ books: [], selectedFilter: "all" }),
  methods: {
    async selectFilter(value) {
      this.selectedFilter = value;
      this.books = (await getBooks(value)).data.books;
    },
    async add(book) {
      await addBook(book);
      this.books = (await getBooks()).data.books; // regression: filter lost
    },
    async update(book) {
      await updateBook(book);
      this.books = (await getBooks()).data.books; // regression: filter lost
    },
    async remove(id) {
      await deleteBook(id);
      this.books = (await getBooks()).data.books; // regression: filter lost
    },
  },
};
</script>
