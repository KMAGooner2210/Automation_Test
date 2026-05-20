import tkinter as tk
import pyautogui

class App:
    def __init__(self, root):
        self.root = root
        self.value = 0
        self.running = False
        self.direction = 0

        self.label = tk.Label(root, text=f"Value: {self.value}", font=("Arial", 24))
        self.label.pack(pady=10)

        self.instruction = tk.Label(root, text="Press and hold the key ↑ to increase, ↓ to decrease", font=("Arial", 12))
        self.instruction.pack(pady=5)

        self.instruction = tk.Label(root, text="Press C to clear value", font=("Arial", 12))
        self.instruction.pack(pady=5)

        self.mouse_label = tk.Label(root, text="Mouse: (x=0, y=0)", font=("Arial", 12))
        self.mouse_label.pack(pady=5)

        root.bind("<KeyPress-Up>", self.start_increase)
        root.bind("<KeyPress-Down>", self.start_decrease)
        root.bind("<KeyRelease-Up>", self.stop)
        root.bind("<KeyRelease-Down>", self.stop)

        root.bind("<KeyPress>", self.on_key_press)

        self.label.focus_set()

        # update the mouse position
        self.update_mouse_position()

    def on_key_press(self, event):
        if event.char == 'c':
            self.value = 0
            self.label.config(text=f"Value: {self.value}")

    def start_increase(self, event=None):
        self.direction = 20
        if not self.running:
            self.running = True
            self.update_value()

    def start_decrease(self, event=None):
        self.direction = -20
        if not self.running:
            self.running = True
            self.update_value()

    def stop(self, event=None):
        self.running = False

    def update_value(self):
        if self.running:
            self.value += self.direction
            pyautogui.scroll(self.direction)
            self.label.config(text=f"Value: {self.value}")
            self.root.after(20, self.update_value)

    def update_mouse_position(self):
        x, y = pyautogui.position()
        self.mouse_label.config(text=f"Mouse (Global): (x={x}, y={y})")
        self.root.after(100, self.update_mouse_position)

root = tk.Tk()
root.title("Get Mouse Position and scroll by key ↑↓")
root.geometry("400x250")
app = App(root)
pyautogui.moveTo(573, 641)
root.mainloop()
