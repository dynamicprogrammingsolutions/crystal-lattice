import { http } from "../http";

export async function getBooks(filter = "all") {
  const params = filter === "all" ? {} : { read: filter === "read" };
  return http.get("/books", { params });
}

export const addBook = (book) => http.post("/books", book);
export const updateBook = (book) => http.put(`/books/${book.id}`, book);
export const deleteBook = (id) => http.delete(`/books/${id}`);
