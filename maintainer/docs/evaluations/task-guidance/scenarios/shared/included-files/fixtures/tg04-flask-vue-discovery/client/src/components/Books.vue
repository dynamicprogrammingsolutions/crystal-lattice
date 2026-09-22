<template>
  <section>
    <table v-if="books.length">
      <tr v-for="book in books" :key="book.id">
        <td>{{ book.title }}</td>
        <td>{{ book.author }}</td>
      </tr>
    </table>
    <p v-else>No books found.</p>
  </section>
</template>

<script>
import { getBooks, addBook, updateBook, deleteBook } from "../api/books";

export default {
  data: () => ({ books: [] }),
  async mounted() { this.books = (await getBooks()).data.books; },
  methods: {
    async add(book) {
      await addBook(book);
      this.books = (await getBooks()).data.books;
    },
    async update(book) {
      await updateBook(book);
      this.books = (await getBooks()).data.books;
    },
    async remove(id) {
      await deleteBook(id);
      this.books = (await getBooks()).data.books;
    },
  },
};
</script>
