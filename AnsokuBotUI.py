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

# ---- Minimal addition: import filedialog for picking a .zip file
import tkinter.filedialog as filedialog

# Initialize colorama with strip=False and convert=False
init(strip=False, convert=False, autoreset=True)

def custom_input(prompt=''):
    sys.stdout.write(prompt)
    sys.stdout.flush()
    app.console.input_handler.prompt_input()
    return app.input_queue.get().rstrip('\n')

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
            font=self.root.text_font
        )
        self.text_widget.window_create('end', window=self.entry)
        self.entry.bind('<Return>', self.on_enter)
        self.entry.bind('<FocusOut>', self.on_focus_out)
        self.entry.focus()

    def on_enter(self, event):
        user_input = self.entry_var.get()
        self.text_widget.insert('end', user_input + '\n', 'input')  
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
        self.console_font = console_font
        self.filter_var = filter_var
        self.pattern = re.compile(r'\x1b\[(.*?)m')

        self.foreground_color_map = {
            '30': ('#000000', 'Black'),
            '31': ('#ff5555', 'Red'),
            '32': ('#50fa7b', 'Green'),
            '33': ('#f1fa8c', 'Yellow'),
            '34': ('#bd93f9', 'Blue'),
            '35': ('#ff79c6', 'Magenta'),
            '36': ('#8be9fd', 'Cyan'),
            '37': ('#f8f8f2', 'White'),
            '90': ('#4d4d4d', 'LightBlack'),
            '91': ('#ff6e6e', 'LightRed'),
            '92': ('#69ff94', 'LightGreen'),
            '93': ('#ffffa5', 'LightYellow'),
            '94': ('#d6acff', 'LightBlue'),
            '95': ('#ff92df', 'LightMagenta'),
            '96': ('#a4ffff', 'LightCyan'),
            '97': ('#ffffff', 'BrightWhite'),
        }

        self.current_foreground_name = None

        # Configure color tags
        for code, (color, name) in self.foreground_color_map.items():
            tag_name = f'fg_{name}'
            tag_config = {'foreground': color, 'font': self.console_font}
            self.text_widget.tag_configure(tag_name, **tag_config)

        self.text_widget.tag_configure('input', foreground='#f8f8f2')

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
                        self.text_widget.insert('end', text, 'input')
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
                    self.text_widget.insert('end', text, 'input')
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
        self.variable = variable

        self.button = customtkinter.CTkButton(
            self,
            textvariable=self.variable,
            command=self.toggle_dropdown,
            anchor='w',
            width=150
        )
        self.button.pack(fill='x')

        self.dropdown_frame = customtkinter.CTkFrame(self, fg_color="#2F2F2F")
        self.dropdown_visible = False

        self.populate_dropdown()
        self.variable.trace('w', self.on_selection_change)

    def populate_dropdown(self):
        for widget in self.dropdown_frame.winfo_children():
            widget.destroy()

        for option in self.options:
            if option != self.variable.get():
                option_button = customtkinter.CTkButton(
                    self.dropdown_frame,
                    text=option,
                    command=lambda opt=option: self.select_option(opt),
                    anchor='w',
                    width=self.button.winfo_width()
                )
                option_button.pack(fill='x')

    def toggle_dropdown(self):
        if self.dropdown_visible:
            self.dropdown_frame.pack_forget()
            self.dropdown_visible = False
        else:
            self.populate_dropdown()
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

        # Right padding frame
        self.padding_frame = customtkinter.CTkFrame(self.main_frame, fg_color='#1e1e1e')
        self.padding_frame.grid(row=0, column=2, sticky='nsew')

        base_font_size = 12
        increased_font_size = int(base_font_size * 1.3)
        self.text_font = tkfont.Font(family="TkDefaultFont", size=increased_font_size)
        self.ctk_font = CTkFont(family="TkDefaultFont", size=increased_font_size)

        self.console = tkinter.Text(
            self.console_frame,
            wrap='word',
            bg='#1e1e1e',
            fg='#f8f8f2',
            borderwidth=0,
            highlightthickness=0,
            font=self.text_font
        )
        self.console.pack(expand=True, fill='both')

        self.input_queue = Queue()
        self.console.input_handler = InputHandler(self, self.console, self.input_queue)

        # Filter frame
        self.filter_frame = customtkinter.CTkFrame(self.main_frame, fg_color='#1e1e1e')
        self.filter_frame.grid(row=1, column=0, columnspan=3, sticky='ew', padx=10, pady=10)
        self.filter_frame.grid_columnconfigure(0, weight=0)
        self.filter_frame.grid_columnconfigure(1, weight=1)

        self.filter_var = tkinter.StringVar(value='Any')
        self.filter_dropdown = CustomDropdown(
            self.filter_frame,
            options=['Any', 'Green', 'Yellow', 'Red', 'Blue', 'Light'],
            variable=self.filter_var,
            fg_color="#1e1e1e"
        )
        self.filter_dropdown.grid(row=0, column=0, sticky='w')

        self.console_redirect = ConsoleRedirect(self.console, self.input_queue, self.text_font, self.filter_var)
        sys.stdout = self.console_redirect

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Image subframe
        self.image_subframe = customtkinter.CTkFrame(self.image_frame, fg_color='#1e1e1e', corner_radius=0)
        self.image_subframe.grid(row=0, column=0, sticky='nsew')
        self.image_frame.grid_rowconfigure(0, weight=1)
        self.image_frame.grid_columnconfigure(0, weight=1)

        self.image_subframe.grid_rowconfigure(0, weight=0)
        self.image_subframe.grid_rowconfigure(1, weight=1)
        self.image_subframe.grid_columnconfigure(0, weight=1)

        # Button frame
        self.run_button_frame = customtkinter.CTkFrame(self.image_subframe, fg_color='#1e1e1e')
        self.run_button_frame.grid(row=0, column=0, sticky='nsew', pady=10)

        # ---- Minimal change: center the 2 existing buttons by adding "stretch" columns on sides
        self.run_button_frame.grid_columnconfigure(0, weight=1)  # left stretch
        self.run_button_frame.grid_columnconfigure(1, weight=0)  # PPO button
        self.run_button_frame.grid_columnconfigure(2, weight=0)  # A2C button
        self.run_button_frame.grid_columnconfigure(3, weight=0)  # Continue Training
        self.run_button_frame.grid_columnconfigure(4, weight=1)  # right stretch

        self.run_button_frame.grid_rowconfigure(0, weight=0)

        # Label
        self.title_label = customtkinter.CTkLabel(
            self.run_button_frame,
            text="AnsokuBot",
            text_color="#f8f8f2",
            fg_color="#1e1e1e",
            font=CTkFont(family="TkDefaultFont", size=16, weight="bold")
        )
        # Place label above buttons in row=0, centered across columns 1..3
        self.title_label.grid(row=0, column=1, columnspan=3, pady=(0, 5))

        # ---- First Button (PPO) in row=1 col=1
        self.run_button = customtkinter.CTkButton(
            self.run_button_frame,
            text="Train AI (PPO)",
            command=self.start_AnsokuENV_output,
            hover_color="#44475a",
            fg_color="#6272a4",
            text_color="#f8f8f2",
            corner_radius=8,
            width=80,
            height=30
        )
        self.run_button.grid(row=1, column=1, padx=5)

        # ---- Second Button (A2C) in row=1 col=2
        self.run_button2 = customtkinter.CTkButton(
            self.run_button_frame,
            text="Train AI (A2C)",
            command=self.start_AnsokuENV_output_A2C,
            hover_color="#44475a",
            fg_color="#6272a4",
            text_color="#f8f8f2",
            corner_radius=8,
            width=80,
            height=30
        )
        self.run_button2.grid(row=1, column=2, padx=5)

        # ---- Minimal addition: Continue Training button in row=1 col=3
        self.continue_button = customtkinter.CTkButton(
            self.run_button_frame,
            text="Continue Training",
            command=self.start_continue_training,
            hover_color="#44475a",
            fg_color="#6272a4",
            text_color="#f8f8f2",
            corner_radius=8,
            width=120,
            height=30
        )
        self.continue_button.grid(row=1, column=3, padx=5)

        self.image_display_frame = customtkinter.CTkFrame(self.image_subframe, fg_color='#1e1e1e')
        self.image_display_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        self.image_display_frame.grid_rowconfigure(0, weight=1)
        self.image_display_frame.grid_columnconfigure(0, weight=1)
        self.image_display_frame.grid_rowconfigure(0, weight=1)
        self.image_display_frame.grid_columnconfigure(0, weight=1, minsize=500)

        self.placeholder_panel = tkinter.Frame(
            self.image_display_frame,
            bg='#2F2F2F'
        )
        self.placeholder_label = tkinter.Label(
            self.placeholder_panel,
            text="No Result Loaded",
            bg='#2F2F2F',
            fg='#f8f8f2',
            font=('TkDefaultFont', 14)
        )
        self.placeholder_label.pack(expand=True, fill='both')
        self.placeholder_panel.grid(row=0, column=0, columnspan=1, sticky='nsew')

        self.image_label = tkinter.Label(self.image_display_frame, bg='#1e1e1e')

        self.bind("<Configure>", self.on_resize)
        self.filter_var.trace('w', self.update_filter)

        self.AnsokuENV_thread = None

    # ----------------------------------------------------------------------
    #  Minimal addition: Continue Training logic
    # ----------------------------------------------------------------------
    def start_continue_training(self):

        self.continue_button.configure(state='disabled')
        self.AnsokuENV_thread = threading.Thread(target=self.Ansoku_Continue_ENV_output, daemon=True)
        self.AnsokuENV_thread.start()

    def Ansoku_Continue_ENV_output(self):
        """Environment thread function for continuing training."""
        try:

            import SharedData
            """Pick a .zip file, set SharedData.models_Continue_dir, ask model name (PPO/A2C), then run environment."""
            file_path = filedialog.askopenfilename(filetypes=[("Zip Files", "*.zip")], initialdir="Models/")
            if not file_path:
                print("No file selected. Aborting.")
                return
            SharedData.models_Continue_dir = file_path
            print(f"Selected zip: {file_path}")
        
            print("Which model do you want to use? (PPO or A2C)")
            model_choice = input("").strip().upper()
            if model_choice == "PPO":
                SharedData.model_name = "PPO"
            elif model_choice == "A2C":
                SharedData.model_name = "A2C"
            else:
                print("Invalid choice, defaulting to PPO.")
                SharedData.model_name = "PPO"

            SharedData.hwnd = self.hwnd
            SharedData.id = self

            time.sleep(1)
            SharedData.continue_training = True  # per your snippet
            from AnsokuStartup import StartAI
            sys.modules['AnsokuStartup'].console_redirect = sys.stdout
            StartAI(puzzlePieceFolder, chromeTabTitle)
        except Exception as e:
            print(Fore.RED + f"An error occurred: {e}")
        finally:
            # Re-enable the Continue button afterward
            self.continue_button.configure(state='normal')

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
        """Starts environment with PPO."""
        if self.AnsokuENV_thread and self.AnsokuENV_thread.is_alive():
            print(Fore.YELLOW + "Bot is already running.")
            return

        import SharedData
        SharedData.hwnd = self.hwnd
        SharedData.id = self

        self.run_button.configure(state='disabled')
        self.AnsokuENV_thread = threading.Thread(target=self.Ansoku_PPO_ENV_output, daemon=True)
        self.AnsokuENV_thread.start()
        print(Fore.BLUE + "AI started (PPO).")

    def start_AnsokuENV_output_A2C(self):
        """Starts environment with A2C."""
        if self.AnsokuENV_thread and self.AnsokuENV_thread.is_alive():
            print(Fore.YELLOW + "Bot is already running.")
            return

        import SharedData
        SharedData.hwnd = self.hwnd
        SharedData.id = self

        self.run_button2.configure(state='disabled')
        self.AnsokuENV_thread = threading.Thread(target=self.Ansoku_A2C_ENV_output, daemon=True)
        self.AnsokuENV_thread.start()
        print(Fore.BLUE + "AI started (A2C).")

    def Ansoku_PPO_ENV_output(self):
        """Environment thread function for PPO."""
        try:
            time.sleep(1)
            SharedData.using_PPO_model = True
            from AnsokuStartup import StartAI
            sys.modules['AnsokuStartup'].console_redirect = sys.stdout
            StartAI(puzzlePieceFolder, chromeTabTitle)
        except Exception as e:
            print(Fore.RED + f"An error occurred: {e}")
        finally:
            self.run_button.configure(state='normal')

    def Ansoku_A2C_ENV_output(self):
        """Environment thread function for A2C."""
        try:
            time.sleep(1)
            SharedData.using_PPO_model = False
            from AnsokuStartup import StartAI
            sys.modules['AnsokuStartup'].console_redirect = sys.stdout
            StartAI(puzzlePieceFolder, chromeTabTitle)
        except Exception as e:
            print(Fore.RED + f"An error occurred: {e}")
        finally:
            self.run_button2.configure(state='normal')

    def display_image(self, img, crop_box=None):
        img_rgb = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        self.pil_image = Image.fromarray(img_rgb)

        if crop_box:
            self.pil_image = self.pil_image.crop(crop_box)

        self.original_width, self.original_height = self.pil_image.size
        self.max_scale_factor = 2.0

        def resize_image(event=None):
            width = int(self.image_label.winfo_width())
            height = int(self.image_label.winfo_height())
            if width > 0 and height > 0:
                scale_w = width / self.original_width
                scale_h = height / self.original_height
                scale_factor = min(scale_w, scale_h, self.max_scale_factor)
                new_width = int(self.original_width * scale_factor)
                new_height = int(self.original_height * scale_factor)

                resized_image = self.pil_image.resize((new_width, new_height), Image.LANCZOS)
                tk_image = ImageTk.PhotoImage(resized_image)
                self.image_label.configure(image=tk_image)
                self.image_label.image = tk_image

        if self.placeholder_panel.winfo_ismapped():
            self.placeholder_panel.grid_forget()
            self.image_label.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        self.image_label.bind('<Configure>', resize_image)
        self.image_label.after(0, resize_image)

    def on_resize(self, event):
        if event.widget == self:
            self.update_font_size()

    def update_font_size(self):
        width = self.winfo_width()
        height = self.winfo_height()
        new_font_size = min(20, max(10, int(height * 0.02)))
        if self.text_font['size'] != new_font_size:
            self.text_font.configure(size=new_font_size)
            self.ctk_font.configure(size=new_font_size)
            self.console.configure(font=self.text_font)

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
        light_colors = ['LightBlack', 'LightRed', 'LightGreen', 'LightYellow',
                        'LightBlue', 'LightMagenta', 'LightCyan', 'BrightWhite', 'White']
        green_colors = ['Green', 'LightGreen']
        red_colors = ['Red', 'LightRed']
        yellow_colors = ['Yellow', 'LightYellow']
        blue_colors = ['Blue', 'LightBlue']

        for code, (color, name) in self.console_redirect.foreground_color_map.items():
            tag_name = f'fg_{name}'
            if name == 'White':
                self.console.tag_configure(tag_name, elide=False)
                continue
            if filter_value == 'Any':
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
                self.console.tag_configure(tag_name, elide=True)

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
    # Minimal change: keep the call to initialize_window_handle
    app.after(1000, app.initialize_window_handle)
    app.mainloop()
