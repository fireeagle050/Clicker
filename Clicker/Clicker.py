import tkinter as tk
from tkinter import ttk, simpledialog, colorchooser, filedialog
from pynput import mouse, keyboard
import threading
import time
import json
from PIL import ImageGrab, ImageTk
import os
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class ClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Clicker by Fire Eagle")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.style = ttk.Style()
        self.light_theme = "default"
        self.dark_theme = "clam"
        self.style.theme_use(self.light_theme)

        self.actions = []
        self.running = False
        self.listener = None
        self.clicker_thread = None
        self.picking_color = False

        # --- App Icon ---
        try:
            icon_path = resource_path(os.path.join("assets", "icon.png"))
            self.root.iconphoto(True, ImageTk.PhotoImage(file=icon_path))
        except Exception as e:
            self.log(f"Could not load icon: {e}")

        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Menu Bar ---
        self.create_menu()

        # --- Action Sequence ---
        action_frame = ttk.LabelFrame(self.main_frame, text="Action Sequence")
        action_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.action_list = tk.Listbox(action_frame)
        self.action_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- Action Management ---
        management_frame = ttk.LabelFrame(self.main_frame, text="Manage Actions")
        management_frame.pack(fill=tk.X, padx=5, pady=5)

        add_button = ttk.Button(management_frame, text="Add", command=self.add_action_dialog)
        add_button.pack(side=tk.LEFT, padx=5, pady=5)

        delete_button = ttk.Button(management_frame, text="Delete", command=self.delete_action)
        delete_button.pack(side=tk.LEFT, padx=5, pady=5)

        up_button = ttk.Button(management_frame, text="Up", command=lambda: self.move_action(-1))
        up_button.pack(side=tk.LEFT, padx=5, pady=5)

        down_button = ttk.Button(management_frame, text="Down", command=lambda: self.move_action(1))
        down_button.pack(side=tk.LEFT, padx=5, pady=5)

        # --- Logs and Status ---
        log_frame = ttk.LabelFrame(self.main_frame, text="Logs & Status")
        log_frame.pack(fill=tk.X, padx=5, pady=5)

        self.log_text = tk.Text(log_frame, height=5)
        self.log_text.pack(fill=tk.X, padx=5, pady=5)
        self.log("Welcome to Clicker!")

        # --- Controls ---
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        self.start_button = ttk.Button(control_frame, text="Start (Ctrl+S)", command=self.start_clicking)
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.stop_button = ttk.Button(control_frame, text="Stop (Ctrl+S)", command=self.stop_clicking, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)

        pick_coords_label = ttk.Label(control_frame, text="Pick Coords (Ctrl+P) / Pick Color (Ctrl+C)")
        pick_coords_label.pack(side=tk.RIGHT, padx=5, pady=5)

        self.setup_hotkeys()
        self.apply_theme()

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Template", command=self.save_template)
        file_menu.add_command(label="Load Template", command=self.load_template)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        edit_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Custom Shortcuts", command=self.custom_shortcuts)

        view_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Switch Theme", command=self.switch_theme)

    def switch_theme(self):
        if self.style.theme_use() == self.light_theme:
            self.style.theme_use(self.dark_theme)
        else:
            self.style.theme_use(self.light_theme)
        self.apply_theme()

    def apply_theme(self):
        is_dark = self.style.theme_use() == self.dark_theme
        bg_color = "#333" if is_dark else "#FFF"
        fg_color = "#FFF" if is_dark else "#000"

        self.root.config(bg=bg_color)
        self.main_frame.config(style="TFrame")

        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ttk.LabelFrame):
                widget.config(style="TLabelframe")
                for child in widget.winfo_children():
                    child.config(style=f"T{type(child).__name__}")
            else:
                widget.config(style=f"T{type(widget).__name__}")

        self.action_list.config(bg=bg_color, fg=fg_color)
        self.log_text.config(bg=bg_color, fg=fg_color)

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)

    def add_action_dialog(self):
        dialog = AddActionDialog(self.root)
        self.root.wait_window(dialog.top)
        if dialog.action:
            action_type = dialog.action["type"]
            if action_type == "color_condition":
                self.picking_color = True
                self.log("Press Ctrl+C to pick a color from the screen.")
                self.pending_action = dialog.action
            elif action_type not in ["key_press", "scroll"]:
                self.log("Press Ctrl+P to pick coordinates for the action.")
                self.pending_action = dialog.action
            else:
                self.add_action(dialog.action)

    def get_coords_for_action(self):
        if not hasattr(self, "pending_action"):
            return

        self.log("Picking coordinates... Move mouse to desired location and left-click.")
        with mouse.Listener(on_click=self.on_pick_coords) as listener:
            listener.join()

    def on_pick_coords(self, x, y, button, pressed):
        if pressed and button == mouse.Button.left:
            self.pending_action["x"] = x
            self.pending_action["y"] = y
            self.add_action(self.pending_action)
            return False  # Stop listener

    def get_color_for_action(self):
        if not hasattr(self, "pending_action"):
            return

        self.log("Picking color... Move mouse to desired location and left-click.")
        with mouse.Listener(on_click=self.on_pick_color) as listener:
            listener.join()

    def on_pick_color(self, x, y, button, pressed):
        if pressed and button == mouse.Button.left:
            screenshot = ImageGrab.grab(bbox=(x, y, x + 1, y + 1))
            color = screenshot.getpixel((0, 0))
            self.pending_action["color"] = color
            self.add_action(self.pending_action)
            self.picking_color = False
            return False

    def add_action(self, action):
        self.actions.append(action)
        self.update_action_list()
        self.log(f"Added action: {action}")
        if hasattr(self, "pending_action"):
            del self.pending_action

    def delete_action(self):
        selected_indices = self.action_list.curselection()
        if not selected_indices:
            return
        for i in sorted(selected_indices, reverse=True):
            del self.actions[i]
        self.update_action_list()

    def move_action(self, direction):
        selected_indices = self.action_list.curselection()
        if not selected_indices:
            return

        for i in selected_indices:
            if 0 <= i + direction < len(self.actions):
                self.actions.insert(i + direction, self.actions.pop(i))

        self.update_action_list()

        new_selection_indices = [i + direction for i in selected_indices]
        for i in new_selection_indices:
            self.action_list.selection_set(i)

    def update_action_list(self):
        self.action_list.delete(0, tk.END)
        for i, action in enumerate(self.actions):
            self.action_list.insert(tk.END, f"{i+1}. {action}")

    def start_clicking(self):
        if not self.actions:
            self.log("No actions to perform.")
            return

        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.log("Starting click sequence...")
        self.clicker_thread = threading.Thread(target=self.run_actions, daemon=True)
        self.clicker_thread.start()

    def stop_clicking(self):
        self.running = False
        if self.clicker_thread and self.clicker_thread.is_alive():
            self.log("Stopping click sequence...")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def run_actions(self):
        mouse_controller = mouse.Controller()
        keyboard_controller = keyboard.Controller()

        i = 0
        while self.running and i < len(self.actions):
            action = self.actions[i]

            if not self.running:
                break

            condition_met = True
            if action.get("type") == "color_condition":
                screenshot = ImageGrab.grab(bbox=(action['x'], action['y'], action['x'] + 1, action['y'] + 1))
                pixel_color = screenshot.getpixel((0, 0))
                if pixel_color != tuple(action['color']):
                    condition_met = False
                self.log(f"Color condition at ({action['x']}, {action['y']}): expected {action['color']}, got {pixel_color}. Condition met: {condition_met}")

            if condition_met:
                action_type = action.get("type")
                if "click" in action_type:
                    mouse_controller.position = (action['x'], action['y'])
                    if action_type == 'left_click':
                        mouse_controller.click(mouse.Button.left)
                    elif action_type == 'right_click':
                        mouse_controller.click(mouse.Button.right)
                    elif action_type == 'double_click':
                        mouse_controller.click(mouse.Button.left, 2)
                elif action_type == "key_press":
                    self.handle_key_press(keyboard_controller, action["key"])
                elif action_type == "scroll":
                    mouse_controller.scroll(0, action["scroll_y"])

                self.log(f"Executed: {action}")
                time.sleep(action.get("delay", 1))
                i += 1
            else:
                time.sleep(1) # Wait before re-checking condition

        self.log("Click sequence finished.")
        self.root.after(0, self.stop_clicking)

    def handle_key_press(self, controller, key_str):
        # This can be expanded to handle more complex key combinations
        try:
            key = getattr(keyboard.Key, key_str, key_str)
            controller.press(key)
            controller.release(key)
        except Exception as e:
            self.log(f"Error pressing key {key_str}: {e}")

    def on_press(self, key):
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = True
            elif hasattr(key, 'char') and self.ctrl_pressed:
                if key.char == 's':
                    if self.running:
                        self.stop_clicking()
                    else:
                        self.start_clicking()
                elif key.char == 'p':
                    self.get_coords_for_action()
                elif key.char == 'c':
                    if self.picking_color:
                        self.get_color_for_action()

        except AttributeError:
            pass

    def on_release(self, key):
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.ctrl_pressed = False

    def setup_hotkeys(self):
        self.ctrl_pressed = False
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

    def save_template(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not filepath:
            return
        with open(filepath, "w") as f:
            json.dump(self.actions, f, indent=4)
        self.log(f"Template saved to {filepath}")

    def load_template(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not filepath:
            return
        with open(filepath, "r") as f:
            self.actions = json.load(f)
        self.update_action_list()
        self.log(f"Template loaded from {filepath}")

    def custom_shortcuts(self):
        self.log("Custom shortcuts functionality not yet implemented.")

    def on_closing(self):
        if self.running:
            self.stop_clicking()
        if self.listener:
            self.listener.stop()
        self.root.destroy()

class AddActionDialog:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Add Action")
        self.action = None

        ttk.Label(self.top, text="Action Type:").grid(row=0, column=0, padx=5, pady=5)
        self.action_type = ttk.Combobox(self.top, values=["left_click", "right_click", "double_click", "scroll", "key_press", "color_condition"])
        self.action_type.grid(row=0, column=1, padx=5, pady=5)
        self.action_type.set("left_click")

        ttk.Label(self.top, text="Delay (s):").grid(row=1, column=0, padx=5, pady=5)
        self.delay = ttk.Entry(self.top)
        self.delay.grid(row=1, column=1, padx=5, pady=5)
        self.delay.insert(0, "1")

        ttk.Label(self.top, text="Key (for key_press):").grid(row=2, column=0, padx=5, pady=5)
        self.key = ttk.Entry(self.top)
        self.key.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(self.top, text="Scroll Y:").grid(row=3, column=0, padx=5, pady=5)
        self.scroll_y = ttk.Entry(self.top)
        self.scroll_y.grid(row=3, column=1, padx=5, pady=5)
        self.scroll_y.insert(0, "-1") # Default to scroll down

        ttk.Button(self.top, text="OK", command=self.ok).grid(row=4, column=0, columnspan=2, pady=10)

    def ok(self):
        action_type = self.action_type.get()
        delay = float(self.delay.get())

        self.action = {"type": action_type, "delay": delay}

        if action_type == "key_press":
            self.action["key"] = self.key.get()
        elif action_type == "scroll":
            self.action["scroll_y"] = int(self.scroll_y.get())

        self.top.destroy()

def main():
    root = tk.Tk()
    app = ClickerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()