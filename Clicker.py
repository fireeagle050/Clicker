import tkinter as tk
from tkinter import messagebox, filedialog, ttk, scrolledtext
import pyautogui
import threading
import time
import keyboard
import json
from datetime import datetime
from PIL import Image, ImageTk

class AutoClickerApp:
    """
    A feature-rich application for automating mouse and keyboard actions.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Auto-Clicker Manager")
        self.root.geometry("650x850") # Adjusted size for better layout
        self.root.minsize(600, 700)

        # --- Set Application Icon ---
        try:
            self.icon = ImageTk.PhotoImage(file="icon.png")
            self.root.iconphoto(True, self.icon)
        except Exception as e:
            print(f"Error loading icon: {e}")

        # --- App State ---
        self.actions = []
        self.running = False
        self.automation_thread = None
        self.time_delay = 1.0
        self.full_log = []

        # --- Theme Colors ---
        self.themes = {
            "Dark": {
                "bg": "#282c34", "fg": "#dcdcdc", "entry_bg": "#1e1e1e",
                "entry_fg": "#ffffff", "button_bg": "#61afef", "button_fg": "#ffffff",
                "list_bg": "#1e1e1e", "list_fg": "#dcdcdc", "label_fg": "#abb2bf",
                "log_bg": "#1e1e1e", "log_fg": "#dcdcdc", "select_bg": "#61afef", "select_fg": "#ffffff"
            },
            "Light": {
                "bg": "#f0f0f0", "fg": "#000000", "entry_bg": "#ffffff",
                "entry_fg": "#000000", "button_bg": "#007acc", "button_fg": "#ffffff",
                "list_bg": "#ffffff", "list_fg": "#000000", "label_fg": "#333333",
                "log_bg": "#ffffff", "log_fg": "#000000", "select_bg": "#007acc", "select_fg": "#ffffff"
            }
        }
        self.current_theme = "Dark"

        # --- UI Setup ---
        self.setup_ui()
        self.apply_theme("Dark")
        self.update_mouse_position()
        self.setup_global_shortcuts()
        self.log("Application initialized. Press Ctrl+S to start/stop, Ctrl+P to pick coordinates.")
        self._schedule_log_clearing()

    def setup_ui(self):
        """Sets up the main UI using themed LabelFrames for better organization."""
        self.root.columnconfigure(0, weight=1)

        self._setup_menu()
        self._setup_mouse_display()

        # --- Main Frames ---
        self._setup_config_frame()
        self._setup_sequence_frame()
        self._setup_control_frame()
        self._setup_log_frame()

        self.update_input_fields()

    def _setup_menu(self):
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Template", command=self.save_template)
        file_menu.add_command(label="Load Template", command=self.load_template)
        file_menu.add_command(label="Save Log", command=self.save_log)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.stop_script)

        options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Options", menu=options_menu)
        theme_menu = tk.Menu(options_menu, tearoff=0)
        options_menu.add_cascade(label="Themes", menu=theme_menu)
        theme_menu.add_command(label="Dark", command=lambda: self.apply_theme("Dark"))
        theme_menu.add_command(label="Light", command=lambda: self.apply_theme("Light"))

    def _setup_mouse_display(self):
        self.mouse_position_label = tk.Label(self.root, text="Mouse Position: X=0, Y=0, Color=(0, 0, 0)", font=("Arial", 10))
        self.mouse_position_label.pack(pady=5)

    def _setup_config_frame(self):
        """Frame for configuring a single action."""
        self.config_frame = tk.LabelFrame(self.root, text="Action Configuration", font=("Arial", 12, "bold"), padx=10, pady=10)
        self.config_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(self.config_frame, text="Action Type:", font=("Arial", 11)).grid(row=0, column=0, padx=5, sticky="w")
        self.action_type = tk.StringVar(value="Left Click")
        action_menu = ttk.OptionMenu(self.config_frame, self.action_type, "Left Click", "Left Click", "Right Click", "Double Click", "Scroll", "Key Press", command=lambda e: self.update_input_fields())
        action_menu.grid(row=0, column=1, columnspan=3, padx=5, sticky="ew")

        self.input_fields_frame = tk.Frame(self.config_frame)
        self.input_fields_frame.grid(row=1, column=0, columnspan=4, pady=(10,0))

        # --- Input Fields ---
        font_small = ("Arial", 11)
        self.x_label = tk.Label(self.input_fields_frame, text="X:", font=font_small); self.x_entry = tk.Entry(self.input_fields_frame, width=8, borderwidth=2, relief="solid")
        self.y_label = tk.Label(self.input_fields_frame, text="Y:", font=font_small); self.y_entry = tk.Entry(self.input_fields_frame, width=8, borderwidth=2, relief="solid")
        self.r_label = tk.Label(self.input_fields_frame, text="R:", font=font_small); self.r_entry = tk.Entry(self.input_fields_frame, width=8, borderwidth=2, relief="solid")
        self.g_label = tk.Label(self.input_fields_frame, text="G:", font=font_small); self.g_entry = tk.Entry(self.input_fields_frame, width=8, borderwidth=2, relief="solid")
        self.b_label = tk.Label(self.input_fields_frame, text="B:", font=font_small); self.b_entry = tk.Entry(self.input_fields_frame, width=8, borderwidth=2, relief="solid")
        self.key_label = tk.Label(self.input_fields_frame, text="Key:", font=font_small); self.key_entry = tk.Entry(self.input_fields_frame, width=15, borderwidth=2, relief="solid")
        self.scroll_label = tk.Label(self.input_fields_frame, text="Scroll Amt:", font=font_small); self.scroll_entry = tk.Entry(self.input_fields_frame, width=10, borderwidth=2, relief="solid")

        tk.Label(self.config_frame, text="Delay (s):", font=font_small).grid(row=2, column=0, padx=5, pady=(10,0), sticky="w")
        self.time_entry = tk.Entry(self.config_frame, width=10, borderwidth=2, relief="solid"); self.time_entry.grid(row=2, column=1, padx=5, pady=(10,0), sticky="w"); self.time_entry.insert(0, str(self.time_delay))

    def _setup_sequence_frame(self):
        """Frame for displaying and managing the action sequence."""
        self.sequence_frame = tk.LabelFrame(self.root, text="Action Sequence", font=("Arial", 12, "bold"), padx=10, pady=10)
        self.sequence_frame.pack(pady=10, padx=10, fill="x")
        self.sequence_frame.columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(self.sequence_frame, height=10, font=("Arial", 10), exportselection=False)
        self.listbox.grid(row=0, column=0, sticky="nsew", rowspan=2)

        up_button = tk.Button(self.sequence_frame, text="↑", command=self.move_up, font=("Arial", 12, "bold"), relief="raised", bd=3)
        up_button.grid(row=0, column=1, padx=(10,0), sticky="ew")
        down_button = tk.Button(self.sequence_frame, text="↓", command=self.move_down, font=("Arial", 12, "bold"), relief="raised", bd=3)
        down_button.grid(row=1, column=1, padx=(10,0), sticky="ew")

    def _setup_control_frame(self):
        """Frame for the main control buttons."""
        self.control_frame = tk.LabelFrame(self.root, text="Controls", font=("Arial", 12, "bold"), padx=10, pady=10)
        self.control_frame.pack(pady=10, padx=10, fill="x")
        self.control_frame.columnconfigure([0,1,2,3], weight=1) # Distribute space

        btn_font = ("Arial", 11, "bold")
        tk.Button(self.control_frame, text="Add Action", command=self.add_action, font=btn_font, relief="raised", bd=3).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        tk.Button(self.control_frame, text="Remove Action", command=self.remove_action, font=btn_font, relief="raised", bd=3).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.start_button = tk.Button(self.control_frame, text="Start", command=self.start_automation, font=btn_font, relief="raised", bd=3); self.start_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        self.stop_button = tk.Button(self.control_frame, text="Stop", command=self.stop_automation, font=btn_font, relief="raised", bd=3); self.stop_button.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # --- Loop Controls ---
        tk.Label(self.control_frame, text="Loops (0=inf):", font=("Arial", 11)).grid(row=1, column=0, padx=5, pady=(5,0), sticky="e")
        self.loops_entry = tk.Entry(self.control_frame, width=10, borderwidth=2, relief="solid")
        self.loops_entry.grid(row=1, column=1, padx=5, pady=(5,0), sticky="w")
        self.loops_entry.insert(0, "0")

        # --- Shortcut Labels ---
        shortcut_font = ("Arial", 10, "italic")
        tk.Label(self.control_frame, text="Start/Stop: Ctrl+S", font=shortcut_font).grid(row=1, column=2, padx=5, pady=(5,0), sticky="e")
        tk.Label(self.control_frame, text="Picker: Ctrl+P", font=shortcut_font).grid(row=1, column=3, padx=5, pady=(5,0), sticky="w")

    def _setup_log_frame(self):
        """Creates the logging area."""
        self.log_frame = tk.LabelFrame(self.root, text="Log", font=("Arial", 12, "bold"), padx=10, pady=10)
        self.log_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.log_frame.columnconfigure(0, weight=1)
        self.log_frame.rowconfigure(0, weight=1)

        self.log_area = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, font=("Arial", 9))
        self.log_area.grid(row=0, column=0, sticky="nsew")
        self.log_area.config(state='disabled')

    def apply_theme(self, theme_name):
        self.current_theme = theme_name
        theme = self.themes[theme_name]
        self.root.configure(bg=theme["bg"])

        # Configure all LabelFrames
        for frame in [self.config_frame, self.sequence_frame, self.control_frame, self.log_frame]:
            frame.config(bg=theme["bg"], fg=theme["fg"])

        # Configure other widgets
        self.mouse_position_label.config(bg=theme["bg"], fg=theme["label_fg"])
        self.listbox.config(bg=theme["list_bg"], fg=theme["list_fg"], selectbackground=theme["select_bg"], selectforeground=theme["select_fg"])
        self.log_area.config(bg=theme["log_bg"], fg=theme["log_fg"])

        # Dynamic input fields frame
        self.input_fields_frame.config(bg=theme["bg"])

        # All labels, entries, and buttons
        all_widgets = self.config_frame.winfo_children() + self.input_fields_frame.winfo_children() + self.sequence_frame.winfo_children() + self.control_frame.winfo_children()
        for widget in all_widgets:
            widget_type = widget.winfo_class()
            if widget_type in ['Label', 'TLabel', 'TCheckbutton']:
                widget.config(bg=theme["bg"], fg=theme["fg"])
            elif widget_type == 'Entry':
                widget.config(bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["entry_fg"])
            elif widget_type == 'Button':
                widget.config(bg=theme["button_bg"], fg=theme["button_fg"])

        self.start_button.config(bg="#98c379" if theme_name == "Dark" else "#28a745", fg=theme["bg"] if theme_name == "Dark" else "#ffffff")
        self.stop_button.config(bg="#e06c75" if theme_name == "Dark" else "#dc3545", fg=theme["button_fg"])

    def update_input_fields(self):
        for widget in self.input_fields_frame.winfo_children(): widget.grid_forget()
        action = self.action_type.get()
        if action in ["Left Click", "Right Click", "Double Click", "Scroll"]:
            self.x_label.grid(row=0, column=0, padx=5, pady=2, sticky="w"); self.x_entry.grid(row=0, column=1, padx=5, pady=2)
            self.y_label.grid(row=0, column=2, padx=5, pady=2, sticky="w"); self.y_entry.grid(row=0, column=3, padx=5, pady=2)
            self.r_label.grid(row=1, column=0, padx=5, pady=2, sticky="w"); self.r_entry.grid(row=1, column=1, padx=5, pady=2)
            self.g_label.grid(row=1, column=2, padx=5, pady=2, sticky="w"); self.g_entry.grid(row=1, column=3, padx=5, pady=2)
            self.b_label.grid(row=1, column=4, padx=5, pady=2, sticky="w"); self.b_entry.grid(row=1, column=5, padx=5, pady=2)
            if action == "Scroll": self.scroll_label.grid(row=2, column=0, padx=5, pady=2, sticky="w"); self.scroll_entry.grid(row=2, column=1, padx=5, pady=2)
        elif action == "Key Press":
            self.key_label.grid(row=0, column=0, padx=5, pady=2, sticky="w"); self.key_entry.grid(row=0, column=1, padx=5, pady=2)

    def _schedule_log_clearing(self):
        """Schedules the log display to be cleared periodically."""
        self.root.after(30000, self._clear_log_display) # 30 seconds

    def _clear_log_display(self):
        """Clears the on-screen log widget and reschedules itself."""
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        # Add a quiet message to the log without displaying it on screen
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.full_log.append(f"[{timestamp}] On-screen log cleared automatically.\n")
        self._schedule_log_clearing() # Reschedule the next clear

    def log(self, message):
        """Logs a message to the UI, the console, and the in-memory full log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"

        self.full_log.append(log_message) # Add to the full log

        # To avoid UI blocking from other threads, schedule the UI update
        self.root.after(0, self.update_log_widget, log_message)
        print(log_message.strip())

    def update_log_widget(self, message):
        """Appends a message to the log widget, making sure it's thread-safe."""
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message)
        self.log_area.see(tk.END) # Scroll to the bottom
        self.log_area.config(state='disabled')

    def update_mouse_position(self):
        try:
            x, y = pyautogui.position(); color = pyautogui.pixel(x, y)
            self.mouse_position_label.config(text=f"Mouse Position: X={x}, Y={y}, Color={color}")
        except Exception:
            self.mouse_position_label.config(text="Mouse Position: N/A, Color=N/A")
        self.root.after(100, self.update_mouse_position)

    def setup_global_shortcuts(self):
        threading.Thread(target=self.monitor_shortcuts, daemon=True).start()

    def monitor_shortcuts(self):
        keyboard.add_hotkey("ctrl+s", self.toggle_automation)
        keyboard.add_hotkey("ctrl+p", self.activate_color_picker)
        keyboard.add_hotkey("ctrl+q", self.stop_script)
        keyboard.wait()

    def add_action(self):
        action_type = self.action_type.get(); new_action = {"type": action_type}
        try:
            if action_type in ["Left Click", "Right Click", "Double Click", "Scroll"]:
                new_action["x"] = int(self.x_entry.get()); new_action["y"] = int(self.y_entry.get())
                r, g, b = self.r_entry.get(), self.g_entry.get(), self.b_entry.get()
                new_action["color"] = (int(r), int(g), int(b)) if r and g and b else None
                if action_type == "Scroll": new_action["amount"] = int(self.scroll_entry.get())
            elif action_type == "Key Press":
                key = self.key_entry.get()
                if not key: raise ValueError("Key cannot be empty.")
                new_action["key"] = key
            self.actions.append(new_action); self.refresh_listbox()
            self.log(f"Added action: {new_action}")
        except ValueError as e: messagebox.showerror("Error", f"Invalid input: {e}")

    def remove_action(self):
        selected_indices = self.listbox.curselection()
        if selected_indices:
            removed_action = self.actions.pop(selected_indices[0])
            self.refresh_listbox()
            self.log(f"Removed action: {removed_action}")
        else: messagebox.showwarning("Warning", "No action selected to remove.")

    def move_up(self):
        selected_indices = self.listbox.curselection()
        if selected_indices:
            index = selected_indices[0]
            if index > 0:
                self.actions[index], self.actions[index - 1] = self.actions[index - 1], self.actions[index]
                self.refresh_listbox(); self.listbox.select_set(index - 1)
                self.log(f"Moved action up at index {index}")

    def move_down(self):
        selected_indices = self.listbox.curselection()
        if selected_indices:
            index = selected_indices[0]
            if index < len(self.actions) - 1:
                self.actions[index], self.actions[index + 1] = self.actions[index + 1], self.actions[index]
                self.refresh_listbox(); self.listbox.select_set(index + 1)
                self.log(f"Moved action down at index {index}")

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for action in self.actions:
            action_str = f"Type: {action['type']}"
            if action['type'] in ["Left Click", "Right Click", "Double Click", "Scroll"]:
                action_str += f" | X={action['x']}, Y={action['y']}"
                if action['color']: action_str += f", Color={action['color']}"
                if action['type'] == "Scroll": action_str += f", Amount={action['amount']}"
            elif action['type'] == "Key Press": action_str += f" | Key='{action['key']}'"
            self.listbox.insert(tk.END, action_str)

    def toggle_automation(self):
        if self.running: self.stop_automation()
        else: self.start_automation()

    def start_automation(self):
        try:
            self.time_delay = float(self.time_entry.get())
            if self.time_delay <= 0: raise ValueError("Time delay must be a positive number.")

            self.loop_count = int(self.loops_entry.get())
            if self.loop_count < 0: raise ValueError("Loop count cannot be negative.")

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
            return

        if not self.running:
            self.running = True
            self.log(f"Automation started with {self.loop_count if self.loop_count > 0 else 'infinite'} loops.")
            self.automation_thread = threading.Thread(target=self.run_automation_loop)
            self.automation_thread.start()

    def stop_automation(self):
        if self.running:
            self.running = False
            self.log("Automation stopped.")

    def run_automation_loop(self):
        loops_completed = 0
        while self.running:
            # For finite loops, check if we're done. If loop_count is 0, this is always false.
            if self.loop_count > 0 and loops_completed >= self.loop_count:
                break

            if self.loop_count > 0:
                self.log(f"Starting loop {loops_completed + 1}/{self.loop_count}.")
            else:
                self.log(f"Starting loop #{loops_completed + 1} (infinite).")

            for i, action in enumerate(self.actions):
                if not self.running: break

                # Schedule UI update on the main thread
                def highlight_item(index):
                    self.listbox.selection_clear(0, tk.END)
                    self.listbox.selection_set(index)
                    self.listbox.see(index)
                self.root.after(0, highlight_item, i)

                if 'color' in action and action['color']:
                    if pyautogui.pixel(action['x'], action['y']) != action['color']:
                        self.log(f"Skipping action at ({action['x']}, {action['y']}) due to color mismatch.")
                        time.sleep(self.time_delay); continue

                action_type = action['type']
                self.log(f"Executing: {action_type} - {action}")
                if action_type == "Left Click": pyautogui.click(x=action['x'], y=action['y'], button='left')
                elif action_type == "Right Click": pyautogui.click(x=action['x'], y=action['y'], button='right')
                elif action_type == "Double Click": pyautogui.doubleClick(x=action['x'], y=action['y'])
                elif action_type == "Scroll": pyautogui.scroll(action['amount'], x=action['x'], y=action['y'])
                elif action_type == "Key Press": pyautogui.press(action['key'])
                time.sleep(self.time_delay)

            if not self.running:
                break

            loops_completed += 1
            if self.running: time.sleep(0.1) # Pause between sequence repeats

        self.log("Automation sequence finished.")
        self.root.after(0, self.listbox.selection_clear, 0, tk.END)
        self.running = False

    def stop_script(self):
        self.stop_automation(); self.root.quit()

    def activate_color_picker(self):
        try:
            x, y = pyautogui.position(); color = pyautogui.pixel(x, y)
            if self.action_type.get() not in ["Key Press"]:
                self.x_entry.delete(0, tk.END); self.x_entry.insert(0, str(x))
                self.y_entry.delete(0, tk.END); self.y_entry.insert(0, str(y))
                self.r_entry.delete(0, tk.END); self.r_entry.insert(0, str(color[0]))
                self.g_entry.delete(0, tk.END); self.g_entry.insert(0, str(color[1]))
                self.b_entry.delete(0, tk.END); self.b_entry.insert(0, str(color[2]))
                self.log(f"Picked color at X={x}, Y={y}, Color={color}")
        except Exception as e: messagebox.showerror("Error", f"Could not pick color: {e}")

    def save_template(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], title="Save Action Template")
        if not filepath: return
        try:
            with open(filepath, 'w') as f: json.dump(self.actions, f, indent=4)
            self.log(f"Template saved to {filepath}")
        except Exception as e: messagebox.showerror("Error", f"Failed to save template: {e}")

    def load_template(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")], title="Load Action Template")
        if not filepath: return
        try:
            with open(filepath, 'r') as f: self.actions = json.load(f)
            self.refresh_listbox()
            self.log(f"Template loaded from {filepath}")
        except Exception as e: messagebox.showerror("Error", f"Failed to load template: {e}")

    def save_log(self):
        """Saves the complete, in-memory log to a text file."""
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")], title="Save Log")
        if not filepath: return
        try:
            with open(filepath, 'w') as f:
                f.writelines(self.full_log)
            self.log(f"Log saved to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save log: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.mainloop()