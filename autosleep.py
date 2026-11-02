import ctypes
import os
import sys
import tkinter as tk
from tkinter import simpledialog
from tkinter import ttk

class SleepTimerApp:
    """
    Sleep timer GUI Application.
    Uses Windows Power API for sleep trigger.
    """
    def __init__(self):
        """
        Initialises sleep timer
        """
        # Get time input via modal dialog (user can cancel here)
        time_input = simpledialog.askstring(" ","Enter time in HH:MM:SS")
        
        # Handle input cancellation (user clicked cancel in dialog)
        if time_input is None:
            print("User canceled time input dialog. Exiting.")
            sys.exit(0)
        
        # Reads different formats of time
        try:
            parts = time_input.split(':')
            if len(parts) == 3:
                h = int(parts[0])
                m = int(parts[1])
                s = int(parts[2])
                self.total_seconds = h * 3600 + m * 60 + s
            elif len(parts) == 2:
                m = int(parts[0])
                s = int(parts[1])
                self.total_seconds = m * 60 + s
            else:
                self.total_seconds = int(parts[0])
        except (ValueError, IndexError):
            print("Invalid time format. Defaulting to 5 minutes.")
            self.total_seconds = 300

        # Create visible countdown window
        self.root = tk.Tk()
        self.root.title("Sleep Timer")
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("light_yellow.Horizontal.TProgressbar", background="#EBE070", foreground="#FFFFE0")
        self.root.geometry("350x120")
        self.root.resizable(False, False)
        
        # Time display
        self.time_label = tk.Label(self.root, text=f"Sleep in: {self.total_seconds//3600:02d}:{(self.total_seconds%3600)//60:02d}:{self.total_seconds%60:02d}")
        self.time_label.pack(pady=10)
        
        # Initialise progress bar
        self.progress_bar = tk.ttk.Progressbar(
            self.root, 
            style="light_yellow.Horizontal.TProgressbar", 
            orient="horizontal", 
            length=300, 
            mode="determinate", 
            maximum=100
        )
        self.progress_bar.pack(pady=5)
        
        # Cancel button
        self.cancel_button = tk.Button(self.root, text="Cancel", command=self.cancel)
        self.cancel_button.pack(pady=5)
        
        # Start countdown
        self.remaining = self.total_seconds
        self.update_countdown()
        
        # About window shortcut
        self.root.bind("<Button-3>", self.show_about_window)
    
    def update_countdown(self):
        """Update countdown display and progress bar."""
        # Update time display
        self.remaining -= 1
        h = self.remaining // 3600
        m = (self.remaining % 3600) // 60
        s = self.remaining % 60
        self.time_label.config(text=f"Sleep in: {h:02d}:{m:02d}:{s:02d}")
        
        # Progress bar set
        self.progress_bar['value'] = (self.remaining * 100) / self.total_seconds
        
        # Check if timer reached 0
        if self.remaining <= 0:
            self.sleep_system()  # Trigger sleep when timer hits 0
            return  # Stop further updates
        
        # Schedule next update
        self.root.after(1000, self.update_countdown)
    
    def cancel(self):
        """Exit application without triggering sleep."""
        self.root.destroy()
        sys.exit(0)

    def sleep_system(self):
        """Trigger system sleep after countdown completes."""
        self.root.destroy()
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        
    def show_about_window(self, event=None):
        """
        Displays the 'About Window' with application information.
        """
        about_window = tk.Toplevel(self.root)
        about_window.title("About Auto Sleep")
        about_window.geometry("540x200")
        
        # Initialise widget
        text_widget = tk.Text(
            about_window,
            wrap="word",
            height=10,
            bg="white",
            font=("Consolas", 10),
            padx=-140,
            pady=5
        )
        
        # Pack with proper alignment
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
 
        # About Text
        text_widget.insert("1.0",
                           """
                           Auto Sleep v0.5
                           
                           Notes on Usage:
                           • Closing the countdown window does cancel the countdown timer.
                           
                           Coded by Thomas Round
                           """)
        # Disable modification to text
        text_widget.config(state="disabled")
        about_window.resizable(False, False)
        text_widget.update_idletasks()

if __name__ == "__main__":
    # Hide console window
    if ctypes.windll.kernel32.GetConsoleWindow() != 0:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    app = SleepTimerApp()
    app.root.mainloop()
