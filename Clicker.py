import tkinter as tk
from tkinter import messagebox
import pyautogui
import threading
import time
import keyboard

class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto-Clicker Manager")
        self.root.geometry("600x600")
        self.root.configure(bg="#282c34")  # Tło aplikacji

        self.click_functions = []  # Lista przechowująca funkcje kliknięcia
        self.running = False
        self.time_delay = 1  # Domyślny odstęp czasowy (w sekundach)

        # Interfejs użytkownika
        self.setup_ui()

        # Uruchomienie wyświetlania pozycji myszy
        self.update_mouse_position()

        # Globalne skróty klawiszowe
        self.setup_global_shortcuts()

    def setup_ui(self):
        # Stylizacja ogólna
        label_font = ("Arial", 12, "bold")
        entry_bg = "#1e1e1e"
        entry_fg = "#ffffff"
        button_bg = "#61afef"
        button_fg = "#ffffff"
        button_radius = 10
        frame_bg = "#282c34"
        entry_borderwidth = 2
        entry_relief = "solid"

        # Sekcja wyświetlania pozycji myszy
        self.mouse_position_label = tk.Label(
            self.root,
            text="Pozycja myszy: X=0, Y=0, Kolor=(0, 0, 0)",
            font=("Arial", 10),
            bg="#282c34",
            fg="#abb2bf",
        )
        self.mouse_position_label.pack(pady=10)

        # Lista funkcji
        self.listbox = tk.Listbox(self.root, width=80, height=10, bg="#1e1e1e", fg="#dcdcdc", font=("Arial", 10))
        self.listbox.pack(pady=10)

        # Ramka dla pól wejściowych
        form_frame = tk.Frame(self.root, bg="#282c34")
        form_frame.pack(pady=10)

        # Pola wejściowe
        tk.Label(form_frame, text="X:", font=label_font, bg=frame_bg, fg="#dcdcdc").grid(row=0, column=0, padx=5)
        self.x_entry = tk.Entry(form_frame, width=10, bg=entry_bg, fg=entry_fg, borderwidth=entry_borderwidth, relief=entry_relief)
        self.x_entry.grid(row=0, column=1, padx=5)

        tk.Label(form_frame, text="Y:", font=label_font, bg=frame_bg, fg="#dcdcdc").grid(row=0, column=2, padx=5)
        self.y_entry = tk.Entry(form_frame, width=10, bg=entry_bg, fg=entry_fg, borderwidth=entry_borderwidth, relief=entry_relief)
        self.y_entry.grid(row=0, column=3, padx=5)

        tk.Label(form_frame, text="R:", font=label_font, bg=frame_bg, fg="#dcdcdc").grid(row=1, column=0, padx=5)
        self.r_entry = tk.Entry(form_frame, width=10, bg=entry_bg, fg=entry_fg, borderwidth=entry_borderwidth, relief=entry_relief)
        self.r_entry.grid(row=1, column=1, padx=5)

        tk.Label(form_frame, text="G:", font=label_font, bg=frame_bg, fg="#dcdcdc").grid(row=1, column=2, padx=5)
        self.g_entry = tk.Entry(form_frame, width=10, bg=entry_bg, fg=entry_fg, borderwidth=entry_borderwidth, relief=entry_relief)
        self.g_entry.grid(row=1, column=3, padx=5)

        tk.Label(form_frame, text="B:", font=label_font, bg=frame_bg, fg="#dcdcdc").grid(row=1, column=4, padx=5)
        self.b_entry = tk.Entry(form_frame, width=10, bg=entry_bg, fg=entry_fg, borderwidth=entry_borderwidth, relief=entry_relief)
        self.b_entry.grid(row=1, column=5, padx=5)

        # Pole do ustawiania odstępu czasowego
        tk.Label(form_frame, text="Czas (s):", font=label_font, bg=frame_bg, fg="#dcdcdc").grid(row=3, column=0, padx=5)
        self.time_entry = tk.Entry(form_frame, width=10, bg=entry_bg, fg=entry_fg, borderwidth=entry_borderwidth, relief=entry_relief)
        self.time_entry.grid(row=3, column=1, padx=5)
        self.time_entry.insert(0, str(self.time_delay))

        # Ramka dla przycisków
        button_frame = tk.Frame(self.root, bg="#282c34")
        button_frame.pack(pady=10)

        # Przyciski
        tk.Button(
            button_frame, text="↑", command=self.move_up, bg=button_bg, fg=button_fg, font=label_font, relief="raised", bd=3
        ).grid(row=1, column=0, padx=10, pady=10, ipadx=10, ipady=5)

        tk.Button(
            button_frame, text="↓", command=self.move_down, bg=button_bg, fg=button_fg, font=label_font, relief="raised", bd=3
        ).grid(row=1, column=1, padx=10, pady=10, ipadx=10, ipady=5)

        tk.Button(
            button_frame, text="Dodaj funkcję", command=self.add_function, bg=button_bg, fg=button_fg, font=label_font, relief="raised", bd=3
        ).grid(row=0, column=0, padx=10, pady=10, ipadx=10, ipady=5)

        tk.Button(
            button_frame, text="Usuń funkcję", command=self.remove_function, bg=button_bg, fg=button_fg, font=label_font, relief="raised", bd=3
        ).grid(row=0, column=1, padx=10, pady=10, ipadx=10, ipady=5)

        tk.Button(
            button_frame, text="Uruchom", command=self.start_clicking, bg="#98c379", fg="#282c34", font=label_font, relief="raised", bd=3
        ).grid(row=0, column=2, padx=10, pady=10, ipadx=10, ipady=5)

        tk.Button(
            button_frame, text="Zatrzymaj", command=self.stop_clicking, bg="#e06c75", fg="#ffffff", font=label_font, relief="raised", bd=3
        ).grid(row=0, column=3, padx=10, pady=10, ipadx=10, ipady=5)

    def update_mouse_position(self):
        try:
            x, y = pyautogui.position()
            color = pyautogui.pixel(x, y)
            self.mouse_position_label.config(text=f"Pozycja myszy: X={x}, Y={y}, Kolor={color}")
        except Exception:
            self.mouse_position_label.config(text="Pozycja myszy: N/A, Kolor=N/A")

        # Odświeżanie co 100 ms
        self.root.after(100, self.update_mouse_position)

    def setup_global_shortcuts(self):
        """Konfiguracja globalnych skrótów klawiszowych."""
        threading.Thread(target=self.monitor_shortcuts, daemon=True).start()

    def monitor_shortcuts(self):
        """Obsługa globalnych skrótów klawiszowych."""
        while True:
            if keyboard.is_pressed("ctrl+q"):
                self.stop_script()
                break
            if keyboard.is_pressed("ctrl+p"):
                self.activate_color_picker()

    def add_function(self):
        try:
            x = int(self.x_entry.get())
            y = int(self.y_entry.get())

            # Pobranie kolorów z obsługą pustych pól
            r = self.r_entry.get()
            g = self.g_entry.get()
            b = self.b_entry.get()

            color = None
            if r and g and b:
                color = (int(r), int(g), int(b))

            self.click_functions.append({"x": x, "y": y, "color": color})
            self.refresh_listbox()
        except ValueError:
            messagebox.showerror("Błąd", "Wprowadź prawidłowe wartości liczbowe!")

    def remove_function(self):
        selected = self.listbox.curselection()
        if selected:
            index = selected[0]
            self.click_functions.pop(index)
            self.refresh_listbox()  # Odśwież listę po usunięciu
        else:
            messagebox.showwarning("Uwaga", "Nie wybrano funkcji do usunięcia.")

    def move_up(self):
        selected = self.listbox.curselection()
        if selected:
            index = selected[0]
            if index > 0:  # Można przesunąć w górę
                self.click_functions[index], self.click_functions[index - 1] = (
                    self.click_functions[index - 1],
                    self.click_functions[index],
                )
                self.refresh_listbox()  # Odśwież listę
                self.listbox.select_set(index - 1)  # Zaznacz przesuniętą funkcję

    def move_down(self):
        selected = self.listbox.curselection()
        if selected:
            index = selected[0]
            if index < len(self.click_functions) - 1:  # Można przesunąć w dół
                self.click_functions[index], self.click_functions[index + 1] = (
                    self.click_functions[index + 1],
                    self.click_functions[index],
                )
                self.refresh_listbox()  # Odśwież listę
                self.listbox.select_set(index + 1)  # Zaznacz przesuniętą funkcję

    def refresh_listbox(self):
        """Odświeża zawartość listy wyświetlanej w interfejsie."""
        self.listbox.delete(0, tk.END)
        for func in self.click_functions:
            self.listbox.insert(tk.END, f"Funkcja: X={func['x']}, Y={func['y']}, Kolor={func['color']}")

    def start_clicking(self):
        try:
            self.time_delay = float(self.time_entry.get())
            if self.time_delay <= 0:
                raise ValueError("Czas musi być dodatnią liczbą.")
        except ValueError as e:
            messagebox.showerror("Błąd", str(e))
            return

        if not self.running:
            self.running = True
            threading.Thread(target=self.run_clicking).start()

    def stop_clicking(self):
        self.running = False

    def run_clicking(self):
        while self.running:
            for func in self.click_functions:
                x, y, color = func["x"], func["y"], func["color"]
                if color:
                    # Sprawdzanie koloru
                    if pyautogui.pixel(x, y) == color:
                        pyautogui.click(x, y)
                        print(f"Kliknięto w punkt ({x}, {y}) z kolorem {color}.")
                else:
                    # Kliknięcie bez sprawdzania koloru
                    pyautogui.click(x, y)
                    print(f"Kliknięto w punkt ({x}, {y}).")
                time.sleep(self.time_delay)
            time.sleep(0.1)

    def stop_script(self, event=None):
        """Zatrzymuje działanie skryptu i zamyka aplikację."""
        self.stop_clicking()
        self.root.quit()

    def activate_color_picker(self, event=None):
        """Aktywuje funkcję próbnika (pobranie koloru i koordynatów)."""
        try:
            x, y = pyautogui.position()
            color = pyautogui.pixel(x, y)
            self.x_entry.delete(0, tk.END)
            self.x_entry.insert(0, str(x))
            self.y_entry.delete(0, tk.END)
            self.y_entry.insert(0, str(y))
            self.r_entry.delete(0, tk.END)
            self.r_entry.insert(0, str(color[0]))
            self.g_entry.delete(0, tk.END)
            self.g_entry.insert(0, str(color[1]))
            self.b_entry.delete(0, tk.END)
            self.b_entry.insert(0, str(color[2]))
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można pobrać koloru: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.mainloop()
