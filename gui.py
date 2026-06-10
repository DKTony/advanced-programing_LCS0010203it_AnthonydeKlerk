from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable

import requests


class NamLogGUI:
    def __init__(self, root: tk.Tk, api_base_url: str = "http://127.0.0.1:5000/api") -> None:
        self.root = root
        self.api_base_url = api_base_url.rstrip("/")
        self.root.title("NamLog Freight Tracker")
        self.root.geometry("980x620")
        self.root.minsize(840, 520)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        self.trucks_frame = ttk.Frame(self.notebook, padding=10)
        self.deliveries_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.trucks_frame, text="Trucks")
        self.notebook.add(self.deliveries_frame, text="Deliveries")

        self._build_trucks_tab()
        self._build_deliveries_tab()
        self.refresh_trucks()
        self.refresh_deliveries()

    def _build_trucks_tab(self) -> None:
        toolbar = ttk.Frame(self.trucks_frame)
        toolbar.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(toolbar, text="Refresh", command=self.refresh_trucks).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Delete Selected", command=self.delete_selected_truck).pack(
            side=tk.LEFT,
            padx=(8, 0),
        )

        columns = ("id", "registration", "capacity_tonnes", "current_location", "is_available")
        self.trucks_tree = ttk.Treeview(self.trucks_frame, columns=columns, show="headings", height=18)
        for column in columns:
            self.trucks_tree.heading(column, text=column.replace("_", " ").title())
            self.trucks_tree.column(column, width=150, anchor=tk.CENTER)
        self.trucks_tree.pack(fill=tk.BOTH, expand=True)

    def _build_deliveries_tab(self) -> None:
        form = ttk.LabelFrame(self.deliveries_frame, text="New Delivery", padding=10)
        form.pack(fill=tk.X, pady=(0, 10))

        self.origin_var = tk.StringVar(value="Walvis Bay")
        self.destination_var = tk.StringVar()
        self.weight_var = tk.StringVar()
        self.truck_id_var = tk.StringVar()

        fields = [
            ("Origin", self.origin_var),
            ("Destination", self.destination_var),
            ("Weight kg", self.weight_var),
            ("Truck ID", self.truck_id_var),
        ]
        for index, (label, variable) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=index * 2, sticky=tk.W, padx=(0, 4))
            ttk.Entry(form, textvariable=variable, width=18).grid(
                row=0,
                column=index * 2 + 1,
                sticky=tk.EW,
                padx=(0, 12),
            )

        ttk.Button(form, text="Submit", command=self.submit_delivery).grid(row=0, column=8, sticky=tk.E)
        form.columnconfigure(7, weight=1)

        toolbar = ttk.Frame(self.deliveries_frame)
        toolbar.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(toolbar, text="Refresh", command=self.refresh_deliveries).pack(side=tk.LEFT)

        columns = ("id", "origin", "destination", "weight_kg", "assigned_truck_id", "status")
        self.deliveries_tree = ttk.Treeview(
            self.deliveries_frame,
            columns=columns,
            show="headings",
            height=15,
        )
        for column in columns:
            self.deliveries_tree.heading(column, text=column.replace("_", " ").title())
            self.deliveries_tree.column(column, width=145, anchor=tk.CENTER)
        self.deliveries_tree.pack(fill=tk.BOTH, expand=True)

    def _run_request(
        self,
        request_function: Callable[[], requests.Response],
        success_callback: Callable[[Any], None],
    ) -> None:
        def worker() -> None:
            try:
                response = request_function()
                if response.status_code == 204:
                    data: Any = {}
                else:
                    data = response.json()
                if response.status_code >= 400:
                    message = data.get("error", "The API request failed.")
                    self.root.after(0, lambda: messagebox.showerror("NamLog API Error", message))
                    return
                self.root.after(0, lambda: success_callback(data))
            except requests.RequestException as exc:
                self.root.after(0, lambda: messagebox.showerror("Connection Error", str(exc)))
            except ValueError as exc:
                self.root.after(0, lambda: messagebox.showerror("Response Error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def refresh_trucks(self) -> None:
        self._run_request(
            lambda: requests.get(f"{self.api_base_url}/trucks", timeout=5),
            self._populate_trucks,
        )

    def _populate_trucks(self, trucks: list[dict[str, Any]]) -> None:
        self.trucks_tree.delete(*self.trucks_tree.get_children())
        for truck in trucks:
            self.trucks_tree.insert(
                "",
                tk.END,
                values=(
                    truck["id"],
                    truck["registration"],
                    truck["capacity_tonnes"],
                    truck["current_location"],
                    "Yes" if truck["is_available"] else "No",
                ),
            )

    def delete_selected_truck(self) -> None:
        selected = self.trucks_tree.selection()
        if not selected:
            messagebox.showerror("Selection Required", "Select a truck to delete.")
            return
        truck_id = self.trucks_tree.item(selected[0], "values")[0]
        self._run_request(
            lambda: requests.delete(f"{self.api_base_url}/trucks/{truck_id}", timeout=5),
            lambda _data: self.refresh_trucks(),
        )

    def submit_delivery(self) -> None:
        try:
            payload = {
                "origin": self.origin_var.get(),
                "destination": self.destination_var.get(),
                "weight_kg": float(self.weight_var.get()),
                "assigned_truck_id": int(self.truck_id_var.get()) if self.truck_id_var.get() else None,
            }
        except ValueError:
            messagebox.showerror("Invalid Form Data", "Weight and Truck ID must be numeric.")
            return

        self._run_request(
            lambda: requests.post(f"{self.api_base_url}/deliveries", json=payload, timeout=5),
            self._delivery_created,
        )

    def _delivery_created(self, _delivery: dict[str, Any]) -> None:
        self.destination_var.set("")
        self.weight_var.set("")
        self.truck_id_var.set("")
        self.refresh_deliveries()

    def refresh_deliveries(self) -> None:
        self._run_request(
            lambda: requests.get(f"{self.api_base_url}/deliveries", timeout=5),
            self._populate_deliveries,
        )

    def _populate_deliveries(self, deliveries: list[dict[str, Any]]) -> None:
        self.deliveries_tree.delete(*self.deliveries_tree.get_children())
        for delivery in deliveries:
            self.deliveries_tree.insert(
                "",
                tk.END,
                values=(
                    delivery["id"],
                    delivery["origin"],
                    delivery["destination"],
                    delivery["weight_kg"],
                    delivery["assigned_truck_id"] or "",
                    delivery["status"],
                ),
            )


def launch_gui(api_base_url: str = "http://127.0.0.1:5000/api") -> None:
    root = tk.Tk()
    NamLogGUI(root, api_base_url)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
