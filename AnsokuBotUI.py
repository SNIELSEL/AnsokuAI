import customtkinter
from customtkinter import CTkFont  # Import CTkFont
from tensorboard import program
import tkinter
import tkinter.font as tkfont
import threading
import re
from queue import Queue
import builtins
import win32gui
import ctypes
from CommonImports import *
import SharedData

# Initialize colorama with strip=False and convert=False
init(strip=False, convert=False, autoreset=True)
# Custom Input Handling for the GUI Console
def custom_input(prompt=''):
    sys.stdout.write(prompt)
    sys.stdout.flush()
    app.console.input_handler.prompt_input()
    return app.input_queue.get().rstrip('\n')

# Function to get the HWND for the Tkinter window
def get_hwnd_from_tkinter(root):
    root.update_idletasks()
    hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
    return hwnd

class InputHandler:
    def __init__(self, root, text_widget, input_queue):
        self.root = root
        self.text_widget = text_widget
        self.input_queue = input_queue
        self.input_prompt_active = False

    def prompt_input(self):
        self.input_prompt_active = True
        self.entry_var = tkinter.StringVar()
        self.entry = tkinter.Entry(
            self.root, 
            textvariable=self.entry_var,
            bg='#1e1e1e', 
            fg='#f8f8f2', 
            insertbackground='#f8f8f2', 
            borderwidth=0,
            font=self.root.text_font  # Use tkinter font
        )
        self.text_widget.window_create('end', window=self.entry)
        self.entry.bind('<Return>', self.on_enter)
        self.entry.bind('<FocusOut>', self.on_focus_out)
        self.entry.focus()

    def on_enter(self, event):
        user_input = self.entry_var.get()
        self.text_widget.insert('end', user_input + '\n', 'input')  # Assign 'input' tag
        self.text_widget.see('end')
        self.entry.destroy()
        self.input_queue.put(user_input + '\n')
        self.input_prompt_active = False

    def on_focus_out(self, event):
        if self.input_prompt_active:
            self.entry.destroy()
            self.input_queue.put('\n')
            self.input_prompt_active = False

class ConsoleRedirect:
    def __init__(self, text_widget, input_queue, console_font, filter_var):
        self.text_widget = text_widget
        self.input_queue = input_queue
        self.console_font = console_font  # This is the tkinter font
        self.filter_var = filter_var
        self.pattern = re.compile(r'\x1b\[(.*?)m')

        # Define color mappings
        self.foreground_color_map = {
            '30': ('#000000', 'Black'),            # Black
            '31': ('#ff5555', 'Red'),              # Red
            '32': ('#50fa7b', 'Green'),            # Green
            '33': ('#f1fa8c', 'Yellow'),           # Yellow
            '34': ('#bd93f9', 'Blue'),             # Blue
            '35': ('#ff79c6', 'Magenta'),          # Magenta
            '36': ('#8be9fd', 'Cyan'),             # Cyan
            '37': ('#f8f8f2', 'White'),            # White
            '90': ('#4d4d4d', 'LightBlack'),       # Light Black (Bright Black / Gray)
            '91': ('#ff6e6e', 'LightRed'),         # Light Red
            '92': ('#69ff94', 'LightGreen'),       # Light Green
            '93': ('#ffffa5', 'LightYellow'),      # Light Yellow
            '94': ('#d6acff', 'LightBlue'),        # Light Blue
            '95': ('#ff92df', 'LightMagenta'),     # Light Magenta
            '96': ('#a4ffff', 'LightCyan'),        # Light Cyan
            '97': ('#ffffff', 'BrightWhite'),      # Bright White
        }

        # Initialize current text attributes
        self.current_foreground_name = None

        # Configure all color tags using color names
        for code, (color, name) in self.foreground_color_map.items():
            tag_name = f'fg_{name}'
            tag_config = {'foreground': color, 'font': self.console_font}
            self.text_widget.tag_configure(tag_name, **tag_config)

        # Configure 'input' tag
        self.text_widget.tag_configure('input', foreground='#f8f8f2')  # Adjust as needed

    def write(self, message):
        def append():
            pos = 0
            for match in self.pattern.finditer(message):
                start, end = match.span()
                if start > pos:
                    text = message[pos:start]
                    tag_name = self.get_tag_name()
                    if tag_name:
                        self.text_widget.insert('end', text, tag_name)
                    else:
                        self.text_widget.insert('end', text, 'input')  # Assign 'input' tag
                ansi_codes = match.group(1).split(';')
                for code in ansi_codes:
                    if code == '0':
                        self.current_foreground_name = None
                    elif code in self.foreground_color_map:
                        self.current_foreground_name = self.foreground_color_map[code][1]
                pos = end
            if pos < len(message):
                text = message[pos:]
                tag_name = self.get_tag_name()
                if tag_name:
                    self.text_widget.insert('end', text, tag_name)
                else:
                    self.text_widget.insert('end', text, 'input')  # Assign 'input' tag
            self.text_widget.see('end')
        self.text_widget.after(0, append)

    def get_tag_name(self):
        if self.current_foreground_name:
            return f'fg_{self.current_foreground_name}'
        return None

    def readline(self):
        if self.text_widget.input_handler.input_prompt_active:
            pass
        return self.input_queue.get()

    def flush(self):
        pass

class CustomDropdown(customtkinter.CTkFrame):
    def __init__(self, master, options, variable, **kwargs):
        super().__init__(master, **kwargs)
        self.options = options
        self.variable = variable  # StringVar passed from App

        self.button = customtkinter.CTkButton(
            self, 
            textvariable=self.variable, 
            command=self.toggle_dropdown,
            anchor='w',  # Align text to the left
            width=150  # Set a reasonable width
        )
        self.button.pack(fill='x')

        self.dropdown_frame = customtkinter.CTkFrame(self, fg_color="#2F2F2F")
        self.dropdown_visible = False

        # Initially populate dropdown without duplication
        self.populate_dropdown()

        # Trace the variable to update dropdown when selection changes
        self.variable.trace('w', self.on_selection_change)

    def populate_dropdown(self):
        # Clear existing buttons
        for widget in self.dropdown_frame.winfo_children():
            widget.destroy()

        # Add buttons excluding the currently selected option
        for option in self.options:
            if option != self.variable.get():
                option_button = customtkinter.CTkButton(
                    self.dropdown_frame,
                    text=option,
                    command=lambda opt=option: self.select_option(opt),
                    anchor='w',  # Align text to the left
                    width=self.button.winfo_width()  # Match the main button's width
                )
                option_button.pack(fill='x')

    def toggle_dropdown(self):
        if self.dropdown_visible:
            self.dropdown_frame.pack_forget()
            self.dropdown_visible = False
        else:
            self.populate_dropdown()  # Repopulate dropdown to exclude selected option
            self.dropdown_frame.pack(fill='x')
            self.dropdown_visible = True

    def select_option(self, option):
        self.variable.set(option)
        self.toggle_dropdown()

    def on_selection_change(self, *args):
        if self.dropdown_visible:
            self.populate_dropdown()

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("dark-blue")
        self.title("AnsokuBot Command Console")
        self.geometry("1200x600")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Main frame to hold everything
        self.main_frame = customtkinter.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, sticky='nsew')
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=0)
        self.main_frame.grid_columnconfigure(0, weight=45)
        self.main_frame.grid_columnconfigure(1, weight=20)
        self.main_frame.grid_columnconfigure(2, weight=35)

        # Console frame
        self.console_frame = customtkinter.CTkFrame(self.main_frame)
        self.console_frame.grid(row=0, column=0, sticky='nsew')

        # Image frame
        self.image_frame = customtkinter.CTkFrame(self.main_frame)
        self.image_frame.grid(row=0, column=1, sticky='nsew')
        self.image_frame.configure(fg_color='#1e1e1e')

        # Right padding frame to add more breathing space
        self.padding_frame = customtkinter.CTkFrame(self.main_frame, fg_color='#1e1e1e')
        self.padding_frame.grid(row=0, column=2, sticky='nsew')

        # Console setup with increased font size by 1.3 times
        base_font_size = 12
        increased_font_size = int(base_font_size * 1.3)
        self.text_font = tkfont.Font(family="TkDefaultFont", size=increased_font_size)  # tkinter font
        self.ctk_font = CTkFont(family="TkDefaultFont", size=increased_font_size)       # customtkinter font

        self.console = tkinter.Text(
            self.console_frame, 
            wrap='word', 
            bg='#1e1e1e', 
            fg='#f8f8f2', 
            borderwidth=0, 
            highlightthickness=0,
            font=self.text_font  # Use tkinter font
        )
        self.console.pack(expand=True, fill='both')

        self.input_queue = Queue()
        self.console.input_handler = InputHandler(self, self.console, self.input_queue)

        # Create a frame for row=1 to hold the filter_dropdown and the spacer
        self.filter_frame = customtkinter.CTkFrame(self.main_frame, fg_color='#1e1e1e')
        self.filter_frame.grid(row=1, column=0, columnspan=3, sticky='ew', padx=10, pady=10)
        self.filter_frame.grid_columnconfigure(0, weight=0)  # filter_dropdown column
        self.filter_frame.grid_columnconfigure(1, weight=1)  # Spacer column

        # Custom Dropdown menu to filter console output by color
        self.filter_var = tkinter.StringVar(value='Any')
        self.filter_dropdown = CustomDropdown(
            self.filter_frame, 
            options=['Any', 'Green', 'Yellow', 'Red', 'Blue', 'Light'],
            variable=self.filter_var,  # Pass the StringVar
            fg_color="#1e1e1e"
        )
        self.filter_dropdown.grid(row=0, column=0, sticky='w')  # Align to the west

        # Initialize ConsoleRedirect
        self.console_redirect = ConsoleRedirect(self.console, self.input_queue, self.text_font, self.filter_var)  # Use tkinter font
        sys.stdout = self.console_redirect  # Redirect stdout

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Image label setup with breathing space
        # Create a subframe for the Run button and image
        self.image_subframe = customtkinter.CTkFrame(self.image_frame, fg_color='#1e1e1e', corner_radius=0)
        self.image_subframe.grid(row=0, column=0, sticky='nsew')
        self.image_frame.grid_rowconfigure(0, weight=1)
        self.image_frame.grid_columnconfigure(0, weight=1)

        self.image_subframe.grid_rowconfigure(0, weight=0)  # Run button row
        self.image_subframe.grid_rowconfigure(1, weight=1)  # Image display row
        self.image_subframe.grid_columnconfigure(0, weight=1)

        # Create a frame inside image_subframe to hold the Run button
        self.run_button_frame = customtkinter.CTkFrame(self.image_subframe, fg_color='#1e1e1e')
        self.run_button_frame.grid(row=0, column=0, sticky='ew', pady=10)

        # Configure run_button_frame to allow centering
        self.run_button_frame.grid_rowconfigure(0, weight=1)
        self.run_button_frame.grid_columnconfigure(0, weight=1)

        # Create the Run button with hover effect
        self.run_button = customtkinter.CTkButton(
            self.run_button_frame, 
            text="Run", 
            command=self.start_AnsokuENV_output,
            hover_color="#44475a",  # Darker shade on hover
            fg_color="#6272a4",      # Initial color
            text_color="#f8f8f2",    # Text color
            corner_radius=8,
            width=80,
            height=30
        )
        self.run_button.grid(row=0, column=0)

        # Image display frame
        self.image_display_frame = customtkinter.CTkFrame(self.image_subframe, fg_color='#1e1e1e')
        self.image_display_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        self.image_display_frame.grid_rowconfigure(0, weight=1)
        self.image_display_frame.grid_columnconfigure(0, weight=1)
        self.image_display_frame.grid_rowconfigure(0, weight=1)      # Minimum height
        self.image_display_frame.grid_columnconfigure(0, weight=1, minsize=500)   # Minimum width

        self.placeholder_panel = tkinter.Frame(
            self.image_display_frame, 
            bg='#2F2F2F'  # Darker gray
        )
        self.placeholder_label = tkinter.Label(
            self.placeholder_panel,
            text="No Result Loaded",
            bg='#2F2F2F',
            fg='#f8f8f2',
            font=('TkDefaultFont', 14)
        )
        self.placeholder_label.pack(expand=True, fill='both')
        self.placeholder_panel.grid(row=0, column=0, columnspan=1, sticky='nsew')  # Allow expansion

        # Image label below the Run button (initially hidden)
        self.image_label = tkinter.Label(self.image_display_frame, bg='#1e1e1e')
        # Initially, the image_label is not packed or placed

        self.bind("<Configure>", self.on_resize)

        # Add trace to filter_var to update filter when it changes
        self.filter_var.trace('w', self.update_filter)

        # Initialize a flag to prevent multiple threads
        self.AnsokuENV_thread = None

        # Uncomment the following line to start the AnsokuENV output automatically
        # self.start_AnsokuENV_output()

    def initialize_window_handle(self):
        try:
            self.hwnd = get_hwnd_from_tkinter(self)
            if self.hwnd:
                print(Fore.BLUE + f"Successfully retrieved window handle: {self.hwnd}")
            else:
                print(Fore.RED + "Failed to retrieve window handle.")
        except Exception as e:
            print(Fore.RED + f"Error retrieving window handle: {e}")

    def start_AnsokuENV_output(self):
        if self.AnsokuENV_thread and self.AnsokuENV_thread.is_alive():
            print(Fore.YELLOW + "Bot is already running.")
            return

        import SharedData
        SharedData.hwnd = self.hwnd
        SharedData.id = self
        self.run_button.configure(state='disabled')
        self.AnsokuENV_thread = threading.Thread(target=self.AnsokuENV_output, daemon=True)
        self.AnsokuENV_thread.start()
        print(Fore.BLUE + "AI started.")

    def AnsokuENV_output(self):
        try:
            time.sleep(1)

            from AnsokuStartup import StartAI
            sys.modules['AnsokuStartup'].console_redirect = sys.stdout
            StartAI(puzzlePieceFolder, chromeTabTitle)

        except Exception as e:
            print(Fore.RED + f"An error occurred: {e}")
        finally:
            # Re-enable the Run button if the bot_output thread finishes
            self.run_button.configure(state='normal')

    def display_image(self, img, crop_box=None):
        img_rgb = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        self.pil_image = Image.fromarray(img_rgb)

        if crop_box:
            self.pil_image = self.pil_image.crop(crop_box)

        # Store the original image size after cropping
        self.original_width, self.original_height = self.pil_image.size

        # Define the maximum scaling factor (e.g., 2.0 means the image can be up to twice its original size)
        self.max_scale_factor = 2.0

        def resize_image(event=None):
            width = int(self.image_label.winfo_width())
            height = int(self.image_label.winfo_height())
            if width > 0 and height > 0:
                # Calculate the scaling factors for width and height
                scale_w = width / self.original_width
                scale_h = height / self.original_height

                # Choose the smaller scaling factor to maintain aspect ratio
                scale_factor = min(scale_w, scale_h, self.max_scale_factor)

                # Calculate the new size with the scaling factor
                new_width = int(self.original_width * scale_factor)
                new_height = int(self.original_height * scale_factor)

                resized_image = self.pil_image.resize((new_width, new_height), Image.LANCZOS)
                tk_image = ImageTk.PhotoImage(resized_image)
                self.image_label.configure(image=tk_image)
                self.image_label.image = tk_image

        # If placeholder is visible, hide it and show the image
        if self.placeholder_panel.winfo_ismapped():
            self.placeholder_panel.grid_forget()
            self.image_label.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        self.image_label.bind('<Configure>', resize_image)
        self.image_label.after(0, resize_image)

    def on_resize(self, event):
        if event.widget == self:
            self.update_font_size()
            # No need to call on_parent_resize since we removed it to prevent flickering

    def update_font_size(self):
        width = self.winfo_width()
        height = self.winfo_height()
        new_font_size = min(20, max(10, int(height * 0.02)))
        if self.text_font['size'] != new_font_size:
            self.text_font.configure(size=new_font_size)  # Update tkinter font
            self.ctk_font.configure(size=new_font_size)   # Update customtkinter font
            self.console.configure(font=self.text_font)    # Apply updated tkinter font
            # Update other widgets if necessary
            # Note: CustomDropdown handles its own resizing

    def on_closing(self):
        self.destroy()
        os._exit(0)

    def close_app(self):
        def close():
            self.destroy()
            os._exit(0)
        self.after(0, close)

    def update_filter(self, *args):
        filter_value = self.filter_var.get()

        # Define which tags are considered "Light"
        light_colors = ['LightBlack', 'LightRed', 'LightGreen', 'LightYellow', 
                        'LightBlue', 'LightMagenta', 'LightCyan', 'BrightWhite', 'White']
        green_colors = ['Green', 'LightGreen']
        red_colors = ['Red', 'LightRed']           # Added LightRed to Red filter
        yellow_colors = ['Yellow', 'LightYellow'] # Added LightYellow to Yellow filter
        blue_colors = ['Blue', 'LightBlue']        # Added LightBlue to Blue filter

        # Iterate through color tags
        for code, (color, name) in self.console_redirect.foreground_color_map.items():
            tag_name = f'fg_{name}'
            if name == 'White':
                # Always show White messages
                self.console.tag_configure(tag_name, elide=False)
                continue  # Skip further filtering for White
            if filter_value == 'Any':
                # Show all messages except White is already handled
                self.console.tag_configure(tag_name, elide=False)
            elif filter_value == 'Light':
                if name in light_colors:
                    self.console.tag_configure(tag_name, elide=False)
                else:
                    self.console.tag_configure(tag_name, elide=True)
            elif filter_value == 'Green':
                if name in green_colors:
                    self.console.tag_configure(tag_name, elide=False)
                else:
                    self.console.tag_configure(tag_name, elide=True)
            elif filter_value == 'Red':
                if name in red_colors:
                    self.console.tag_configure(tag_name, elide=False)
                else:
                    self.console.tag_configure(tag_name, elide=True)
            elif filter_value == 'Yellow':
                if name in yellow_colors:
                    self.console.tag_configure(tag_name, elide=False)
                else:
                    self.console.tag_configure(tag_name, elide=True)
            elif filter_value == 'Blue':
                if name in blue_colors:
                    self.console.tag_configure(tag_name, elide=False)
                else:
                    self.console.tag_configure(tag_name, elide=True)
            else:
                # For any other filter values, hide all
                self.console.tag_configure(tag_name, elide=True)

        # Ensure 'input' tag is always visible
        self.console.tag_configure('input', elide=False)


def launch_tensorboard(logdir):
    tb = program.TensorBoard()
    tb.configure(argv=[None, '--logdir', logdir])
    url = tb.launch()
    print(f"TensorBoard is running at {url}")

if __name__ == "__main__":
    puzzlePieceFolder = SharedData.puzzlePieceFolder
    chromeTabTitle = SharedData.chromeTabTitle
    logdir = SharedData.logdir

    import threading
    tb_thread = threading.Thread(target=launch_tensorboard, args=(logdir,), daemon=True)
    tb_thread.start()

    app = App()
    builtins.input = custom_input
    app.after(1000, app.initialize_window_handle)  # Ensure window handle is initialized after setup
    app.mainloop()
