"""Tkinter library book and lending manager; records are stored in SQLite."""
from __future__ import annotations

import sqlite3
import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, ttk
from pathlib import Path

from analysis import create_library_charts

DB_FILE = Path(__file__).with_name("library.db")
CATEGORIES = ("Fiction", "Science", "Technology", "History", "Education", "Other")


class LibraryApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Library Book Management System")
        self.root.geometry("1120x720")
        self.root.minsize(900, 600)
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        self._build_ui()
        self.refresh()

    def _create_tables(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
                author TEXT NOT NULL, category TEXT NOT NULL, isbn TEXT UNIQUE,
                copies INTEGER NOT NULL CHECK(copies >= 0));
            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT, book_id INTEGER NOT NULL,
                borrower TEXT NOT NULL, borrowed_on TEXT NOT NULL, due_on TEXT NOT NULL,
                returned_on TEXT, FOREIGN KEY(book_id) REFERENCES books(id));
        """)
        self.conn.commit()

    def _build_ui(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground="#174a35")
        style.configure("Treeview", rowheight=27, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        header = ttk.Frame(self.root, padding=(18, 15))
        header.pack(fill="x")
        ttk.Label(header, text="LIBRARY BOOK MANAGEMENT SYSTEM", style="Title.TLabel").pack(side="left")
        ttk.Button(header, text="Reports and Charts", command=self.show_reports).pack(side="right")
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        self.book_tab = ttk.Frame(self.tabs, padding=14)
        self.loan_tab = ttk.Frame(self.tabs, padding=14)
        self.tabs.add(self.book_tab, text="Books")
        self.tabs.add(self.loan_tab, text="Borrow and Return")
        self._build_books_tab()
        self._build_loans_tab()
        self.status = tk.StringVar(value="Ready")
        ttk.Label(self.root, textvariable=self.status, anchor="w", padding=(18, 7)).pack(fill="x")

    def _build_books_tab(self) -> None:
        form = ttk.LabelFrame(self.book_tab, text="Book details", padding=12)
        form.pack(fill="x")
        self.title_var = tk.StringVar()
        self.author_var = tk.StringVar()
        self.category_var = tk.StringVar(value=CATEGORIES[0])
        self.isbn_var = tk.StringVar()
        self.copies_var = tk.StringVar(value="1")
        fields = [("Title", self.title_var, 26), ("Author", self.author_var, 20),
                  ("ISBN", self.isbn_var, 16), ("Copies", self.copies_var, 6)]
        for col, (label, var, width) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=col, sticky="w", padx=5)
            ttk.Entry(form, textvariable=var, width=width).grid(row=1, column=col, padx=5, pady=(3, 0))
        ttk.Label(form, text="Category").grid(row=0, column=4, sticky="w", padx=5)
        ttk.Combobox(form, textvariable=self.category_var, values=CATEGORIES, width=15, state="readonly").grid(row=1, column=4, padx=5)
        ttk.Button(form, text="Add Book", command=self.add_book).grid(row=1, column=5, padx=8)
        toolbar = ttk.Frame(self.book_tab, padding=(0, 12))
        toolbar.pack(fill="x")
        self.search_var = tk.StringVar()
        ttk.Label(toolbar, text="Search title, author, ISBN:").pack(side="left")
        search = ttk.Entry(toolbar, textvariable=self.search_var, width=34)
        search.pack(side="left", padx=8)
        search.bind("<KeyRelease>", lambda _event: self.refresh())
        ttk.Button(toolbar, text="Delete Selected", command=self.delete_book).pack(side="right")
        self.books_tree = self._tree(self.book_tab, ("id", "title", "author", "category", "isbn", "copies", "available"),
                                     (55, 235, 170, 120, 130, 75, 90))

    def _build_loans_tab(self) -> None:
        form = ttk.LabelFrame(self.loan_tab, text="Issue a book", padding=12)
        form.pack(fill="x")
        self.borrower_var = tk.StringVar()
        self.loan_search_var = tk.StringVar()
        ttk.Label(form, text="Book").grid(row=0, column=0, sticky="w")
        self.book_choice = ttk.Combobox(form, width=52, state="readonly")
        self.book_choice.grid(row=1, column=0, padx=(0, 12), pady=4)
        ttk.Label(form, text="Borrower name").grid(row=0, column=1, sticky="w")
        ttk.Entry(form, textvariable=self.borrower_var, width=28).grid(row=1, column=1, padx=(0, 12), pady=4)
        ttk.Label(form, text="Loan period (days)").grid(row=0, column=2, sticky="w")
        self.days_var = tk.StringVar(value="14")
        ttk.Entry(form, textvariable=self.days_var, width=8).grid(row=1, column=2, padx=(0, 12), pady=4)
        ttk.Button(form, text="Issue Book", command=self.issue_book).grid(row=1, column=3, padx=4)
        ttk.Label(self.loan_tab, text="Active loans (overdue rows are highlighted)").pack(anchor="w", pady=(12, 5))
        self.loans_tree = self._tree(self.loan_tab, ("id", "book", "borrower", "borrowed", "due", "status"),
                                     (55, 300, 210, 120, 120, 100))
        self.loans_tree.tag_configure("overdue", foreground="#b42318")
        ttk.Button(self.loan_tab, text="Return Selected Book", command=self.return_book).pack(anchor="e", pady=10)

    @staticmethod
    def _tree(parent, columns, widths):
        holder = ttk.Frame(parent)
        holder.pack(fill="both", expand=True)
        tree = ttk.Treeview(holder, columns=columns, show="headings", selectmode="browse")
        scroll = ttk.Scrollbar(holder, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        for name, width in zip(columns, widths):
            tree.heading(name, text=name.replace("_", " ").title())
            tree.column(name, width=width, anchor="w" if name in ("title", "author", "book", "borrower") else "center")
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tree

    def add_book(self) -> None:
        title, author, isbn = self.title_var.get().strip(), self.author_var.get().strip(), self.isbn_var.get().strip()
        try:
            copies = int(self.copies_var.get())
            if not title or not author or copies < 0:
                raise ValueError
            self.conn.execute("INSERT INTO books(title,author,category,isbn,copies) VALUES(?,?,?,?,?)",
                              (title, author, self.category_var.get(), isbn or None, copies))
            self.conn.commit()
        except ValueError:
            messagebox.showerror("Invalid details", "Enter a title, author, and a non-negative whole number of copies.")
            return
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate ISBN", "That ISBN already exists. Leave it blank if the book has no ISBN.")
            return
        self.title_var.set(""); self.author_var.set(""); self.isbn_var.set(""); self.copies_var.set("1")
        self.refresh()

    def delete_book(self) -> None:
        selected = self.books_tree.selection()
        if not selected:
            messagebox.showinfo("Select a book", "Select a book row first."); return
        book_id = int(self.books_tree.item(selected[0], "values")[0])
        active = self.conn.execute("SELECT COUNT(*) FROM loans WHERE book_id=? AND returned_on IS NULL", (book_id,)).fetchone()[0]
        if active:
            messagebox.showerror("Book is on loan", "Return all copies on loan before deleting this book."); return
        self.conn.execute("DELETE FROM books WHERE id=?", (book_id,)); self.conn.commit(); self.refresh()

    def issue_book(self) -> None:
        choice = self.book_choice.get()
        borrower = self.borrower_var.get().strip()
        try:
            days = int(self.days_var.get())
            if not choice or not borrower or days < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Missing details", "Choose a book, enter a borrower, and use a loan period of at least one day."); return
        book_id = int(choice.split(" | ", 1)[0])
        book = self.conn.execute("SELECT copies FROM books WHERE id=?", (book_id,)).fetchone()
        if not book or book["copies"] < 1:
            messagebox.showerror("Unavailable", "There are no copies available for this book."); return
        today = date.today()
        self.conn.execute("UPDATE books SET copies=copies-1 WHERE id=?", (book_id,))
        self.conn.execute("INSERT INTO loans(book_id,borrower,borrowed_on,due_on) VALUES(?,?,?,?)",
                          (book_id, borrower, today.isoformat(), (today + timedelta(days=days)).isoformat()))
        self.conn.commit(); self.borrower_var.set(""); self.refresh()

    def return_book(self) -> None:
        selected = self.loans_tree.selection()
        if not selected:
            messagebox.showinfo("Select a loan", "Select an active loan row first."); return
        loan_id = int(self.loans_tree.item(selected[0], "values")[0])
        row = self.conn.execute("SELECT book_id FROM loans WHERE id=? AND returned_on IS NULL", (loan_id,)).fetchone()
        if row:
            self.conn.execute("UPDATE loans SET returned_on=? WHERE id=?", (date.today().isoformat(), loan_id))
            self.conn.execute("UPDATE books SET copies=copies+1 WHERE id=?", (row["book_id"],))
            self.conn.commit(); self.refresh()

    def refresh(self) -> None:
        query = f"%{self.search_var.get().strip()}%"
        for item in self.books_tree.get_children(): self.books_tree.delete(item)
        books = self.conn.execute("""SELECT b.*, b.copies + (SELECT COUNT(*) FROM loans l WHERE l.book_id=b.id AND l.returned_on IS NULL) AS total
                                    FROM books b WHERE title LIKE ? OR author LIKE ? OR COALESCE(isbn,'') LIKE ? ORDER BY title""",
                                  (query, query, query)).fetchall()
        available = []
        for book in books:
            on_loan = self.conn.execute("SELECT COUNT(*) FROM loans WHERE book_id=? AND returned_on IS NULL", (book["id"],)).fetchone()[0]
            total = book["copies"] + on_loan
            self.books_tree.insert("", "end", values=(book["id"], book["title"], book["author"], book["category"], book["isbn"] or "", total, book["copies"]))
            if book["copies"] > 0: available.append(f"{book['id']} | {book['title']} — {book['author']} ({book['copies']} available)")
        self.book_choice["values"] = available
        if available and self.book_choice.get() not in available: self.book_choice.set(available[0])
        for item in self.loans_tree.get_children(): self.loans_tree.delete(item)
        loans = self.conn.execute("""SELECT l.*,b.title FROM loans l JOIN books b ON b.id=l.book_id
                                     WHERE l.returned_on IS NULL ORDER BY l.due_on""").fetchall()
        for loan in loans:
            overdue = loan["due_on"] < date.today().isoformat()
            self.loans_tree.insert("", "end", values=(loan["id"], loan["title"], loan["borrower"], loan["borrowed_on"], loan["due_on"], "Overdue" if overdue else "On loan"), tags=("overdue",) if overdue else ())
        self.status.set(f"{len(books)} books shown  •  {len(loans)} active loans  •  {sum(b['copies'] for b in books)} available copies")

    def show_reports(self) -> None:
        books = [dict(row) for row in self.conn.execute("SELECT * FROM books ORDER BY title").fetchall()]
        loans = [dict(row) for row in self.conn.execute("SELECT * FROM loans").fetchall()]
        output = Path(__file__).with_name("output_images")
        paths = create_library_charts(books, loans, output)
        messagebox.showinfo("Library reports created", "Charts saved to:\n" + str(output) + "\n\n" + "\n".join(Path(p).name for p in paths))

    def close(self) -> None:
        self.conn.close(); self.root.destroy()


if __name__ == "__main__":
    window = tk.Tk()
    app = LibraryApp(window)
    window.protocol("WM_DELETE_WINDOW", app.close)
    window.mainloop()
