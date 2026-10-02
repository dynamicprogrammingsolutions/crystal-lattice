import { http } from "../http";

export async function getBooks(params = {}) {
  return http.get("/books", { params });
}

export async function addBook(book) {
  return http.post("/books", book);
}

export const updateBook = (book) => http.put(`/books/${book.id}`, book);
export const deleteBook = (id) => http.delete(`/books/${id}`);
