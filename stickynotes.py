import ctypes
import os
import random
import tkinter as tk

class StickyNotes:
    """
    Main application class for Sticky Notes utility.
    Handles window state, text editing, context menus etc.
    Uses Tkinter's event system for shortcuts/menus.
    """
    def __init__(self, root):
        """Initialise Sticky Note info, shortcuts and parameter states."""
        self.root = root
        self.root.title("Sticky Note")
        self.root.geometry("400x300")
        # Offsets for geometry adjustment in hide title bar
        self.title_bar_y_offset = 32
        self.title_bar_x_offset = 8
        
        # Define a bank of light pastel colours (hex format)
        pastel_colours = [
            "#f8d9e6",  # Light pink
            "#e6f8d9",  # Light green
            "#d9e6f8",  # Light blue
            "#f8e6d9",  # Light orange
            "#d9f8e6",  # Light teal
            "#e6d9f8",  # Light purple
            "#f8e6f8",  # Light pink
            "#f8f8d9",  # Light yellow
            "#d9f8f8"   # Light cyan
        ]
        
        # Pick a random pastel colour for the note
        random_colour = random.choice(pastel_colours)
        
        # Initialise font and font size
        self.current_font_size = 12
        self.current_font = "Arial"
        
        # Initialise text widget with default font, font size and random colour
        self.text = tk.Text(
            root,
            wrap="word",  # Default to word wrap
            font=(self.current_font, self.current_font_size),
            padx=5,
            pady=5,
            bg=random_colour,
            undo=True
        )
        self.text.pack(fill="both", expand=True)
        
        # Store initial background colour (required for white bg toggle)
        self.initial_bg = random_colour
        
        # Configure window to be resizable
        root.resizable(True, True)
        
        # Add a small frame for visual separation
        self.frame = tk.Frame(root, height=1)
        self.frame.pack(fill="x")
        
        # Initialise track states
        self.word_wrap = tk.BooleanVar(value=True)
        self.white_bg = tk.BooleanVar(value=False)
        self.font_var = tk.StringVar(value="Arial")
        self.hide_title_bar = tk.BooleanVar(value=False)
        
        # Initialise track bold font state (see set_font method)
        self.text.tag_configure("bold_selection", font=self.text.cget("font") + " bold")

        # Initialise backup framework
        self.auto_save = tk.BooleanVar(value=False)
        self.backup_dir = None
        self.backup_files = []

        # Add keyboard shortcuts
        self.root.bind("<Control-b>", self.toggle_bold_shortcut)
        self.root.bind("<Control-g>", self.toggle_white_bg_shortcut)
        self.root.bind("<Control-h>", self.toggle_hide_title_bar_shortcut)
        self.root.bind("<Control-r>", self.toggle_word_wrap_shortcut)
        self.root.bind("<Control-s>", self.save_note_shortcut)
        self.root.bind("<Control-n>", self.create_new_note_shortcut)
        self.root.bind("<Control-w>", self.close_window)
        self.root.bind('<F1>', self.show_about_window)
        self.text.bind("<Control-MouseWheel>", self.font_size)
        self.text.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """Show right-click context menu with nested Fonts submenu."""
        menu = tk.Menu(self.root, tearoff=0)
        
        # New note / Save note commands
        menu.add_command(label="New Note", command=self.create_new_note)
        menu.add_command(label="Save Note", command=self.save_note)
        
        # Word wrap toggle
        menu.add_checkbutton(
            label="Word Wrap",
            command=self.toggle_word_wrap,
            variable=self.word_wrap
        )
        
        # Nested Fonts submenu
        fonts_submenu = tk.Menu(menu, tearoff=0)
        fonts_list = ["Arial",
                      "Consolas",
                      "Comic Sans MS",
                      "Segoe Print",
                      "Trebuchet MS"]
            
        # Radio buttons (mutually exclusive)
        for font_name in fonts_list:
            fonts_submenu.add_radiobutton(
                label=font_name,
                command=lambda f=font_name: self.set_font(f),
                variable=self.font_var
            )
        menu.add_cascade(label="Fonts", menu=fonts_submenu)
        
        # White background toggle
        menu.add_checkbutton(
            label="White Background",
            variable=self.white_bg,
            command=self.toggle_white_bg
        )
        
        # Title bar toggle
        menu.add_checkbutton(
            label="Hide Title Bar",
            variable=self.hide_title_bar,
            command=self.toggle_hide_title_bar  # ← This is the key line
        )
        
        # Auto Save toggle
        menu.add_checkbutton(
            label="Auto Save",
            variable=self.auto_save,
            command=self.toggle_auto_save
        )
               
        # About window
        menu.add_command(label="About", command=self.show_about_window)
        
        # Display the menu
        menu.post(event.x_root, event.y_root)
        
    def font_size(self, event):
        """Adjust font size when CTRL + scroll (delta-based)."""
        # Increase font size when scrolling down (delta > 0)
        if event.delta > 0:
            self.current_font_size += 1
        # Decrease font size when scrolling up (delta < 0)
        else:
            self.current_font_size -= 1
        
        # Update the widget with new font size
        self.text.config(font=(self.font_var.get(), self.current_font_size))
        
        # Update the bold tag to use the font size
        current_font = self.text.cget("font")
        self.text.tag_configure("bold_selection", font=current_font + " bold")
            
        # Apply new font size (clamped between 8 and 36)
        self.current_font_size = max(8, min(36, self.current_font_size))
        self.text.config(font=(self.font_var.get(), self.current_font_size))
        
    def start_auto_save(self):
        """
        Start the auto-save timer that saves after 3 seconds.
        """
        # Cleans any existing timer before starting a new one
        if hasattr(self, 'auto_save_timer'):
            self.root.after_cancel(self.auto_save_timer)
        # Start timer (in ms)
        self.auto_save_timer = self.root.after(3000, self.save_auto_backup)

    def save_auto_backup(self):
        """
        Save the current text to a backup file with content uniqueness check.
        Uses whitespace-normalised content for deduplication.
        """
        # Get current content (with whitespace)
        current_content = self.text.get(1.0, tk.END)
        
        # Normalise content (remove all whitespace)
        current_normalised = ''.join(current_content.split())
        
        # Does not save if normalised content is empty
        if current_normalised == "":
            self.start_auto_save()
            return
        
        # Check against existing backups; does not save if there is a match
        skip = False
        for backup_file in self.backup_files:
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_content = f.read()
                    backup_normalised = ''.join(backup_content.split())
                    if current_normalised == backup_normalised:
                        skip = True
                        break
            except Exception:
                # Skip broken files without stopping the entire check
                continue
    
        if skip:
            self.start_auto_save()
            return
        
        # Keep only last 5 backups
        if len(self.backup_files) >= 5:
            # Delete oldest file
            oldest_backup_file = self.backup_files.pop(0)
            os.remove(oldest_backup_file)
            file_path = oldest_backup_file
        else:
            # Create backup file name (starts at 1)
            file_name = f"backup{len(self.backup_files) + 1}.stnote"
            file_path = os.path.join(self.backup_dir, file_name)
        
        # Write to file with proper encoding
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(current_content)
        
        # Add to backups list
        self.backup_files.append(file_path)
        
        # Schedule next backup
        self.start_auto_save()

    def stop_auto_save(self):
        """Stop the auto-save timer and clear the backup list."""
        if hasattr(self, 'auto_save_timer'):
            self.root.after_cancel(self.auto_save_timer)
        self.backup_files = []

    def toggle_auto_save(self):
        """Toggle the auto-save feature."""
        if self.auto_save.get():
            # Create backup directory only when auto-save is enabled
            if self.backup_dir is None:
                self.backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
                if not os.path.exists(self.backup_dir):
                    os.makedirs(self.backup_dir)
            self.start_auto_save()
        else:
            self.stop_auto_save()
        
    def set_font(self, font_name):
        """Change text font family (keeps current size)."""
        self.text.config(font=(font_name, self.current_font_size))
        # Update font tag, so font changes happen regardless of bold status
        self.text.tag_configure("bold_selection", font=self.text.cget("font") + " bold")
        
    def toggle_bold_shortcut(self, event):
        """
        Applies bold formatting to selected text 
        (or entire document if nothing is selected).
        """
        try:
            start = self.text.index("sel.first")
            end = self.text.index("sel.last")
        except tk.TclError:
            # No selection: apply to ENTIRE TEXT (1.0 = start, end = end)
            start = "1.0"
            end = "end"
        
        current_font = self.text.cget("font")
        self.text.tag_configure("bold_selection", font=current_font + " bold")
        
        if "bold_selection" in self.text.tag_names(start):
            self.text.tag_remove("bold_selection", start, end)
        else:
            self.text.tag_add("bold_selection", start, end)
        return "break"

    def toggle_word_wrap(self,short=0):
        """Toggle word wrap state (with state management for shortcuts)."""
        # Keyboard shortcut switch
        if short == 1:
            self.word_wrap.set(not self.word_wrap.get())
        self.text.config(wrap="word" if self.word_wrap.get() else "none")
        
    def toggle_word_wrap_shortcut(self, event):
        """Keyboard shortcut to toggle word wrap state."""
        self.toggle_word_wrap(short=1)
        
    def toggle_white_bg(self,short=0):
        """
        Toggle background between initial pastel colour and white 
        (with state management for shortcuts).
        """
        # Keyboard shortcut switch
        if short == 1:
            self.white_bg.set(not self.white_bg.get())
        if self.white_bg.get():
            self.text.config(bg="white")
        else:
            self.text.config(bg=self.initial_bg)
            
    def toggle_white_bg_shortcut(self, event):
        """Keyboard shortcut to toggle background colour state."""
        self.toggle_white_bg(short=1)
    
    def toggle_hide_title_bar(self, short=0):
        """
        Toggle title bar visibility (with state management for shortcuts).
        Uses precise window geometry adjustments to preserve text position.
        """
        # Keyboard shortcut switch
        if short == 1:
            self.hide_title_bar.set(not self.hide_title_bar.get())
        # Geometry adjustment
        if self.hide_title_bar.get():
            # Hide title bar: move window DOWN and RIGHT
            self.root.overrideredirect(True)
            self.root.geometry(f"+{self.root.winfo_x() + self.title_bar_x_offset}+{self.root.winfo_y() + self.title_bar_y_offset}")
        else:
            # Show title bar: move window UP and LEFT
            self.root.overrideredirect(False)
            self.root.geometry(f"+{self.root.winfo_x() - self.title_bar_x_offset}+{self.root.winfo_y() - self.title_bar_y_offset}")
            
    def toggle_hide_title_bar_shortcut(self, event):
        """Keyboard shortcut to toggle hide title bar."""
        self.toggle_hide_title_bar(short=1)
    
    def save_note(self):
        """
        Uses sequential naming to save current note to numbered .stnote file.
        (Bespoke state management not required, as function is not a toggle.)
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        num = 1
        while True:
            file_path = os.path.join(current_dir, f"note{num}.stnote")
            if not os.path.exists(file_path):
                break
            num += 1
        content = self.text.get(1.0, tk.END)
        with open(file_path, 'w') as f:
            f.write(content)

    def save_note_shortcut(self, event):
        """Keyboard shortcut to save note."""
        self.save_note()
        
    def load_note(self, file_path):
        """Load content from a .stnote file into the text widget"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            self.text.delete(1.0, tk.END)
            self.text.insert(tk.END, content)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            
    def create_new_note(self):
        """
        Creates a new note window.
        (Bespoke state management not required, as function is not a toggle.)
        """
        root = tk.Tk()
        StickyNotes(root)
        root.mainloop()

    def create_new_note_shortcut(self, event):
        """Keyboard shortcut to create a new note."""
        self.create_new_note()
        
    def close_window(self, event=None):
        """
        Routine for closing window. If a non-empty note does not have a 
        (whitespace normalised) saved copy, a confirmation dialog is produced.
        """
        # Get content without newlines for comparison
        content_without_newlines = self.text.get(1.0, tk.END).replace('\n', '').replace('\r', '').strip()
        
        # Check if note is empty after stripping whitespace
        is_empty = len(content_without_newlines) == 0
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        stnote_files = [f for f in os.listdir(current_dir) if f.endswith('.stnote')]

        existing_file = None
        for file in stnote_files:
            file_path = os.path.join(current_dir, file)
            try:
                with open(file_path, 'r') as f:
                    content = f.read().replace('\n', '').replace('\r', '').strip()
                    if content == content_without_newlines:
                        existing_file = file_path
                        break
            except:
                pass
    
        if existing_file or is_empty:
            self.root.destroy()
        else:
            self.show_save_dialog()
    
    def show_save_dialog(self):
        """
        Displays confirmation dialog before closing with unsaved work.
        """
        root = tk.Toplevel(self.root)
        root.title("Save Note?")
        frame = tk.Frame(root)
        frame.pack(padx=20, pady=20)
    
        label = tk.Label(
            frame, 
            text="⚠️ There is unsaved work on this note. Save a copy before closing?"
        )
        label.pack(pady=5)
        
        # Dialog button functionality
        save_button = tk.Button(frame, text="Save", command=lambda: self.save_and_close_dialog(root))
        dont_save_button = tk.Button(frame, text="Don't Save", command=lambda: self.close_without_saving_dialog(root))
        cancel_button = tk.Button(frame, text="Cancel", command=root.destroy)
        
        # Dialog button display
        save_button.pack(side="right", padx=5, pady=5)
        dont_save_button.pack(side="right", padx=5, pady=5)
        cancel_button.pack(side="right", padx=5, pady=5)
    
        root.grab_set()
        root.wait_window(root)
    
    def save_and_close_dialog(self, root):
        """
        Save and close button option produced by save_button.
        """
        current_content = self.text.get(1.0, tk.END)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Looks for lowest numbered .stnote that can be saved to
        num = 1
        while True:
            file_path = os.path.join(current_dir, f"note{num}.stnote")
            if not os.path.exists(file_path):
                break
            num += 1
        with open(file_path, 'w') as f:
            f.write(current_content)
        self.root.destroy()
        root.destroy()
    
    def close_without_saving_dialog(self, root):
        """
        Save and close button option produced by dont_save_button.
        """
        self.root.destroy()
        root.destroy()
        
    def show_about_window(self, event=None):
        """
        Displays the 'About Window' with application information.
        """
        about_window = tk.Toplevel(self.root)
        about_window.title("About Sticky Notes")
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
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(about_window, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        # Pack with proper alignment
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # About Text
        text_widget.insert("1.0",
                           """
                           Sticky Notes v0.17 \n
                           Shortcuts:
                           • CTRL + N :      New note
                           • CTRL + S :      Save new note
                           • CTRL + W :      Close note 
                           • CTRL + Z :      Undo 
                           • CTRL + W :      Redo
                           • CTRL + Scroll : Font Size
                           • CTRL + B :      Bold text
                           • CTRL + G :      Toggle white background
                           • CTRL + H :      Toggle title bar
                           • CTRL + R :      Toggle word wrap \n
                           Notes on Usage:
                           • When saving, the output will be a numbered .stnote file
                             in the same folder as this program.
                           • When opening this program, all numbered .stnote files in
                             the same folder will be opened.
                           • The bold text shortcut makes all highlighted text bold
                             (or all text if nothing is highlighted).
                           • Autosave, if enabled, backs up Sticky Notes each minute,
                             keeping the previous 5 notes with distinct contents.
                             
                             Coded by Thomas Round
                           """)
        # Disable modification to text
        text_widget.config(state="disabled")
        text_widget.update_idletasks()

if __name__ == "__main__":
    # Hide console window
    if ctypes.windll.kernel32.GetConsoleWindow() != 0:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    # Find all .stnote files in current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    stnote_files = [f for f in os.listdir(current_dir) if f.endswith('.stnote')]
    
    # Create windows for all notes
    windows = []
    for file in stnote_files:
        file_path = os.path.join(current_dir, file)
        root = tk.Tk()
        app = StickyNotes(root)
        app.load_note(file_path)
        windows.append(root)
    
    # Only create new note if no old notes
    if not stnote_files:
        root = tk.Tk()
        app = StickyNotes(root)
        windows.append(root)
    
    # Run a SINGLE mainloop for ALL windows
    # This keeps all windows visible until closed
    windows[0].mainloop()