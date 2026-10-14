"""Create book inventory and borrowing charts for the library manager."""
from __future__ import annotations

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def create_library_charts(books: list[dict], loans: list[dict], output_dir: Path) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    categories: dict[str, int] = {}
    for book in books:
        category = book.get("category", "Other")
        categories[category] = categories.get(category, 0) + int(book.get("copies", 0))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(categories.keys() or ["No books"], categories.values() or [0], color="#2f855a")
    ax.set_title("Available Copies by Category"); ax.set_ylabel("Copies"); ax.tick_params(axis="x", rotation=20)
    fig.tight_layout(); inventory_path = output_dir / "available_copies_by_category.png"
    fig.savefig(inventory_path, dpi=160); plt.close(fig)
    active = sum(1 for loan in loans if not loan.get("returned_on"))
    returned = len(loans) - active
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.bar(["Active loans", "Returned"], [active, returned], color=["#dd6b20", "#3182ce"])
    ax.set_title("Loan Status Summary"); ax.set_ylabel("Number of loans")
    fig.tight_layout(); loans_path = output_dir / "loan_status_summary.png"
    fig.savefig(loans_path, dpi=160); plt.close(fig)
    return [str(inventory_path), str(loans_path)]
