import json
import tkinter
from tkinter import ttk, filedialog, messagebox
from model import TCGCard, TCGSet, TCGBoosterBox, TCGBoosterPack

default_set_path = "C:/Users/Joseph/Geeb Software/TCGBoxEV/lorwyn_eclipsed_set_v1.json"
default_booster_path = "C:/Users/Joseph/Geeb Software/TCGBoxEV/lorwyn_eclipsed_booster.json"

class TCGBoxEVApp(tkinter.Tk):
    def __init__(self, master=None):
        super().__init__()
        self.title("TCG Box EV Calculator")
        self.geometry("900x520")
        self.minsize(720, 460)
        self.tcg_set = None
        self.booster_pack = None

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=1)

        heading = ttk.Label(self, text="TCG Box EV Calculator", font=("Segoe UI", 18, "bold"))
        heading.grid(row=0, column=0, columnspan=2, padx=16, pady=(16, 8), sticky="w")

        ttk.Label(self, text="Set JSON Path:").grid(row=1, column=0, padx=16, pady=8, sticky="w")
        self.set_entry_text = tkinter.StringVar(value=default_set_path) 
        self.set_path = ttk.Entry(self, textvariable=self.set_entry_text)
        self.set_path.grid(row=1, column=1, padx=16, pady=8, sticky="ew")

        self.select_set_button = ttk.Button(self, text="Select set json...", command=self.select_set_file)
        self.select_set_button.grid(row=1, column=2, padx=8, pady=8, sticky="ew")

        ttk.Label(self, text="Booster JSON Path:").grid(row=2, column=0, padx=16, pady=8, sticky="w")
        self.booster_entry_text = tkinter.StringVar(value=default_booster_path)
        self.booster_path = ttk.Entry(self, textvariable=self.booster_entry_text)
        self.booster_path.grid(row=2, column=1, padx=16, pady=8, sticky="ew")
    
        self.select_booster_button = ttk.Button(self, text="Select booster json...", command=self.select_booster_file)
        self.select_booster_button.grid(row=2, column=2, padx=8, pady=8, sticky="ew")

        button_frame = ttk.Frame(self)
        button_frame.grid(row=3, column=0, columnspan=2, padx=16, pady=12, sticky="nsew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

        self.calculate_button = ttk.Button(button_frame, text="Calculate EV", command=self.calculate_ev)
        self.calculate_button.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        self.load_json_button = ttk.Button(self, text="Load Set and Booster", command=self.load_json_files)
        self.load_json_button.grid(row=0, column=1, padx=16, pady=16, sticky="nsew")
        
        self.edit_card_button = ttk.Button(button_frame, text="Edit Card List", command=self.edit_card_dialog)
        self.edit_card_button.grid(row=1, column=0, padx=8, pady=8, sticky="nsew")

        self.edit_set_button = ttk.Button(button_frame, text="Edit Set Info", command=self.edit_set_info)
        self.edit_set_button.grid(row=1, column=1, padx=8, pady=8, sticky="nsew")

        self.save_set_button = ttk.Button(button_frame, text="Save Set As", command=self.save_set_as)
        self.save_set_button.grid(row=1, column=2, padx=8, pady=8, sticky="nsew")

        self.status_label = ttk.Label(self, text="Ready", anchor="w", relief="sunken")
        self.status_label.grid(row=4, column=0, columnspan=2, padx=16, pady=(0, 16), sticky="ew")

    def calculate_ev(self):
        set_file = self.set_path.get().strip()
        booster_file = self.booster_path.get().strip()
        if not set_file or not booster_file:
            messagebox.showwarning("Input Required", "Please fill both set and booster JSON path fields.")
            return
        self._compute_ev(set_file, booster_file)

    def select_set_file(self):
        set_file = filedialog.askopenfilename(title="Select TCG Set JSON file", filetypes=[("JSON files", "*.json")])
        if set_file:
            self.set_path.delete(0, "end")
            self.set_path.insert(0, set_file)
            self.status_label.config(text=f"Set JSON selected: {set_file}")

    def load_set_file(self):
        set_file = self.set_path.get().strip()
        if set_file:
            self.tcg_set = TCGSet.load_from_json(set_file)
            self.status_label.config(text=f"Set JSON loaded: {set_file}")

    def select_booster_file(self):
        booster_file = filedialog.askopenfilename(title="Select TCG Booster JSON file", filetypes=[("JSON files", "*.json")])
        if booster_file:
            self.booster_path.delete(0, "end")
            self.booster_path.insert(0, booster_file)
            self.status_label.config(text=f"Booster JSON selected: {booster_file}")

    def load_booster_file(self):
        booster_file = self.booster_path.get().strip()
        if booster_file:
            self.booster_pack = TCGBoosterPack.from_json(self.tcg_set, booster_file)
            self.status_label.config(text=f"Booster JSON loaded: {booster_file}")

    def load_json_files(self):
        self.load_set_file()
        self.load_booster_file()

    def _ensure_set_loaded(self):
        if not hasattr(self, 'tcg_set') or self.tcg_set is None:
            messagebox.showwarning("No set loaded", "Load a set first with Load Set and Booster before editing or saving.")
            return False
        return True

    def edit_card_dialog(self):
        if not self._ensure_set_loaded():
            return

        dialog = tkinter.Toplevel(self)
        dialog.title("Manage Cards")
        dialog.transient(self)
        dialog.grab_set()

        rarity_options = ["Common", "Uncommon", "Rare", "Mythic", "Basic Land", "Special"]
        foil_options = ["", "normal", "none"]

        card_listbox = tkinter.Listbox(dialog, width=55, height=12)
        card_listbox.grid(row=0, column=0, rowspan=6, padx=8, pady=8, sticky='ns')
        scrollbar = ttk.Scrollbar(dialog, orient='vertical', command=card_listbox.yview)
        scrollbar.grid(row=0, column=1, rowspan=6, sticky='ns')
        card_listbox.config(yscrollcommand=scrollbar.set)

        def refresh_variant_options():
            variants = sorted({c.variant for c in self.tcg_set.card_list if c.variant})
            variant_combobox['values'] = variants

        def refresh_card_list():
            card_listbox.delete(0, 'end')
            for idx, c in enumerate(self.tcg_set.card_list, start=1):
                variant = f" ({c.variant})" if c.variant else ""
                foil = f" [foil:{c.foil_type}]" if c.foil_type else ""
                price = f"${c.price:.2f}" if isinstance(c.price, (int, float)) else "N/A"
                card_listbox.insert('end', f"{idx}. {c.name} - {c.rarity}{variant}{foil} - {price}")
            refresh_variant_options()

        def clear_form():
            name_entry.delete(0, 'end')
            rarity_combobox.set("")
            variant_combobox.set("")
            foil_combobox.set("")
            price_entry.delete(0, 'end')

        def on_select_card(event=None):
            sel = card_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            c = self.tcg_set.card_list[idx]
            name_entry.delete(0, 'end'); name_entry.insert(0, c.name)
            rarity_combobox.set(c.rarity)
            variant_combobox.set(c.variant or "")
            foil_combobox.set(c.foil_type or "")
            price_entry.delete(0, 'end'); price_entry.insert(0, '' if c.price is None else str(c.price))

        ttk.Label(dialog, text="Name:").grid(row=0, column=2, padx=8, pady=4, sticky="e")
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=3, padx=8, pady=4)

        ttk.Label(dialog, text="Rarity:").grid(row=1, column=2, padx=8, pady=4, sticky="e")
        rarity_combobox = ttk.Combobox(dialog, values=rarity_options, width=28)
        rarity_combobox.grid(row=1, column=3, padx=8, pady=4)

        variant_options = sorted({c.variant for c in self.tcg_set.card_list if c.variant})
        ttk.Label(dialog, text="Variant:").grid(row=2, column=2, padx=8, pady=4, sticky="e")
        variant_combobox = ttk.Combobox(dialog, values=variant_options, width=28)
        variant_combobox.grid(row=2, column=3, padx=8, pady=4)

        ttk.Label(dialog, text="Foil Type:").grid(row=3, column=2, padx=8, pady=4, sticky="e")
        foil_combobox = ttk.Combobox(dialog, values=foil_options, width=28)
        foil_combobox.grid(row=3, column=3, padx=8, pady=4)

        ttk.Label(dialog, text="Price:").grid(row=4, column=2, padx=8, pady=4, sticky="e")
        price_entry = ttk.Entry(dialog, width=30)
        price_entry.grid(row=4, column=3, padx=8, pady=4)

        def add_card():
            name = name_entry.get().strip()
            rarity = rarity_combobox.get().strip()
            variant = variant_combobox.get().strip() or None
            foil_type = foil_combobox.get().strip() or None
            price_text = price_entry.get().strip()
            if not name or not rarity:
                messagebox.showerror("Validation Error", "Name and rarity are required.")
                return
            price = None
            if price_text:
                try:
                    price = float(price_text)
                except ValueError:
                    messagebox.showerror("Validation Error", "Price must be a number.")
                    return
            new_card = TCGCard(name, rarity, price=price, variant=variant, foil_type=foil_type)
            self.tcg_set.card_list.append(new_card)
            refresh_card_list()
            clear_form()
            self.status_label.config(text=f"Added card: {name}")

        def update_card():
            sel = card_listbox.curselection()
            if not sel:
                messagebox.showwarning("Select Card", "Please select a card to update from the list.")
                return
            idx = sel[0]
            name = name_entry.get().strip()
            rarity = rarity_combobox.get().strip()
            variant = variant_combobox.get().strip() or None
            foil_type = foil_combobox.get().strip() or None
            price_text = price_entry.get().strip()
            if not name or not rarity:
                messagebox.showerror("Validation Error", "Name and rarity are required.")
                return
            price = None
            if price_text:
                try:
                    price = float(price_text)
                except ValueError:
                    messagebox.showerror("Validation Error", "Price must be a number.")
                    return
            card = self.tcg_set.card_list[idx]
            card.name = name
            card.rarity = rarity
            card.variant = variant
            card.foil_type = foil_type
            card.price = price
            refresh_card_list()
            self.status_label.config(text=f"Updated card: {name}")

        def delete_card():
            sel = card_listbox.curselection()
            if not sel:
                messagebox.showwarning("Select Card", "Please select a card to delete from the list.")
                return
            idx = sel[0]
            card = self.tcg_set.card_list.pop(idx)
            refresh_card_list()
            clear_form()
            self.status_label.config(text=f"Deleted card: {card.name}")

        card_listbox.bind('<<ListboxSelect>>', on_select_card)

        ttk.Button(dialog, text="Add New", command=add_card).grid(row=5, column=2, padx=8, pady=8, sticky='ew')
        ttk.Button(dialog, text="Update Selected", command=update_card).grid(row=5, column=3, padx=8, pady=8, sticky='ew')
        ttk.Button(dialog, text="Delete Selected", command=delete_card).grid(row=6, column=2, padx=8, pady=8, sticky='ew')
        ttk.Button(dialog, text="Close", command=dialog.destroy).grid(row=6, column=3, padx=8, pady=8, sticky='ew')

        refresh_card_list()

    def edit_set_info(self):
        if not self._ensure_set_loaded():
            return

        dialog = tkinter.Toplevel(self)
        dialog.title("Edit Set Info")
        dialog.transient(self)
        dialog.grab_set()

        bulk_data = dict(self.tcg_set.bulk_price)
        cards_data = dict(self.tcg_set.cards_per_rarity)

        def refresh_bulk_list():
            bulk_list.delete(0, 'end')
            for key in sorted(bulk_data.keys()):
                bulk_list.insert('end', f"{key}: {bulk_data[key]}")

        def refresh_cards_list():
            cards_list.delete(0, 'end')
            for key in sorted(cards_data.keys()):
                cards_list.insert('end', f"{key}: {cards_data[key]}")

        # Bulk price frame
        bulk_frame = ttk.LabelFrame(dialog, text="Bulk Price")
        bulk_frame.grid(row=0, column=0, padx=8, pady=8, sticky='nsew')
        bulk_list = tkinter.Listbox(bulk_frame, height=6)
        bulk_list.grid(row=0, column=0, columnspan=3, padx=8, pady=4, sticky='ew')
        bulk_list.bind('<<ListboxSelect>>', lambda e: fill_bulk_fields())

        ttk.Label(bulk_frame, text="Category:").grid(row=1, column=0, padx=4, pady=4, sticky='e')
        bulk_category = ttk.Entry(bulk_frame, width=20)
        bulk_category.grid(row=1, column=1, padx=4, pady=4, sticky='w')

        ttk.Label(bulk_frame, text="Price:").grid(row=2, column=0, padx=4, pady=4, sticky='e')
        bulk_price_entry = ttk.Entry(bulk_frame, width=20)
        bulk_price_entry.grid(row=2, column=1, padx=4, pady=4, sticky='w')

        def fill_bulk_fields():
            try:
                sel = bulk_list.curselection()
                if not sel:
                    return
                text = bulk_list.get(sel[0])
                key, value = text.split(":", 1)
                bulk_category.delete(0, 'end')
                bulk_price_entry.delete(0, 'end')
                bulk_category.insert(0, key.strip())
                bulk_price_entry.insert(0, value.strip())
            except Exception:
                pass

        def add_update_bulk():
            key = bulk_category.get().strip()
            val = bulk_price_entry.get().strip()
            if not key:
                messagebox.showerror("Validation", "Category is required")
                return
            try:
                val_float = float(val)
            except ValueError:
                messagebox.showerror("Validation", "Price must be numeric")
                return
            bulk_data[key] = val_float
            refresh_bulk_list()
            self.status_label.config(text=f"Bulk price set updated: {key}")

        def delete_bulk():
            key = bulk_category.get().strip()
            if key in bulk_data:
                del bulk_data[key]
                refresh_bulk_list()
                bulk_category.delete(0, 'end')
                bulk_price_entry.delete(0, 'end')

        ttk.Button(bulk_frame, text="Add/Update", command=add_update_bulk).grid(row=1, column=2, padx=4, pady=4)
        ttk.Button(bulk_frame, text="Delete", command=delete_bulk).grid(row=2, column=2, padx=4, pady=4)

        # Cards per rarity frame
        cards_frame = ttk.LabelFrame(dialog, text="Cards Per Rarity")
        cards_frame.grid(row=1, column=0, padx=8, pady=8, sticky='nsew')
        cards_list = tkinter.Listbox(cards_frame, height=6)
        cards_list.grid(row=0, column=0, columnspan=3, padx=8, pady=4, sticky='ew')
        cards_list.bind('<<ListboxSelect>>', lambda e: fill_cards_fields())

        ttk.Label(cards_frame, text="Category:").grid(row=1, column=0, padx=4, pady=4, sticky='e')
        cards_category = ttk.Entry(cards_frame, width=20)
        cards_category.grid(row=1, column=1, padx=4, pady=4, sticky='w')

        ttk.Label(cards_frame, text="Count:").grid(row=2, column=0, padx=4, pady=4, sticky='e')
        cards_count_entry = ttk.Entry(cards_frame, width=20)
        cards_count_entry.grid(row=2, column=1, padx=4, pady=4, sticky='w')

        def fill_cards_fields():
            try:
                sel = cards_list.curselection()
                if not sel:
                    return
                text = cards_list.get(sel[0])
                key, value = text.split(":", 1)
                cards_category.delete(0, 'end')
                cards_count_entry.delete(0, 'end')
                cards_category.insert(0, key.strip())
                cards_count_entry.insert(0, value.strip())
            except Exception:
                pass

        def add_update_cards():
            key = cards_category.get().strip()
            val = cards_count_entry.get().strip()
            if not key:
                messagebox.showerror("Validation", "Category is required")
                return
            try:
                val_int = int(val)
            except ValueError:
                messagebox.showerror("Validation", "Count must be integer")
                return
            cards_data[key] = val_int
            refresh_cards_list()
            self.status_label.config(text=f"Cards per rarity updated: {key}")

        def delete_cards():
            key = cards_category.get().strip()
            if key in cards_data:
                del cards_data[key]
                refresh_cards_list()
                cards_category.delete(0, 'end')
                cards_count_entry.delete(0, 'end')

        ttk.Button(cards_frame, text="Add/Update", command=add_update_cards).grid(row=1, column=2, padx=4, pady=4)
        ttk.Button(cards_frame, text="Delete", command=delete_cards).grid(row=2, column=2, padx=4, pady=4)

        refresh_bulk_list()
        refresh_cards_list()

        def save_set_info():
            self.tcg_set.bulk_price = bulk_data
            self.tcg_set.cards_per_rarity = cards_data
            self.status_label.config(text="Set info updated in memory")
            messagebox.showinfo("Set Updated", "Bulk price and cards per rarity updated in memory.")
            dialog.destroy()

        ttk.Button(dialog, text="Save", command=save_set_info).grid(row=2, column=0, padx=8, pady=10, sticky="w")
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).grid(row=2, column=0, padx=8, pady=10, sticky="e")

    def save_set_as(self):
        if not self._ensure_set_loaded():
            return

        file_path = filedialog.asksaveasfilename(title="Save Set JSON As", defaultextension=".json",
                                                 filetypes=[("JSON files", "*.json")])
        if not file_path:
            return

        payload = {
            "name": self.tcg_set.name,
            "cards": [
                {
                    "name": c.name,
                    "rarity": c.rarity,
                    "price": c.price,
                    "foil_type": c.foil_type,
                    "variant": c.variant,
                }
                for c in self.tcg_set.card_list
            ],
            "bulk_price": self.tcg_set.bulk_price,
            "cards_per_rarity": self.tcg_set.cards_per_rarity,
        }
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2)
            self.status_label.config(text=f"Set saved as {file_path}")
            messagebox.showinfo("Saved", f"Set JSON saved to {file_path}.")
        except Exception as ex:
            messagebox.showerror("Save Error", f"Failed to save JSON: {ex}")

    def _compute_ev(self, set_file, booster_file):
        try:
            tcg_set = TCGSet.load_from_json(set_file)
            booster_pack = TCGBoosterPack.from_json(tcg_set, booster_file)
            box = TCGBoosterBox("Custom Box", tcg_set, 0, 30, booster_pack=booster_pack)

            self.tcg_set = tcg_set
            self.booster_pack = booster_pack
            self.set_path.delete(0, "end")
            self.set_path.insert(0, set_file)
            self.booster_path.delete(0, "end")
            self.booster_path.insert(0, booster_file)

            ev_per_booster = booster_pack.expected_value()
            ev_per_box = box.expected_value()
            self.status_label.config(text=f"EV: ${ev_per_booster:.2f}/booster, ${ev_per_box:.2f}/box")
            messagebox.showinfo("EV Calculation Result",
                                f"Expected value per booster: ${ev_per_booster:.2f}\nExpected value per box (30 boosters): ${ev_per_box:.2f}")
        except Exception as e:
            self.status_label.config(text="Error")
            messagebox.showerror("Error", f"Failed to load set or booster: {e}")


if __name__ == "__main__":
    app = TCGBoxEVApp()
    app.load_json_files()
    app.mainloop()