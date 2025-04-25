import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter.scrolledtext import ScrolledText
import threading
import subprocess
import random
import time
import os
import sys
import string
from typing import List, Dict, Optional, Any

# Add parent directory to path to ensure imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import backend components
from bridge.tools.tools import list_tools, run_tool
import Engine.raven as raven
import bridge.crew as crew

class MatrixRain(tk.Canvas):
    """Digital rain effect in Matrix style"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg='black', highlightthickness=0)
        self.width = self.winfo_reqwidth()
        self.height = self.winfo_reqheight()
        self.chars = "a〒bc*defgh010㋞10ijclemmklmnopqrstuvw0101※01010x1SgodofdoubtBBCﾇDEF〒GHIJKL0MNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,./<>?"
        self.streams = []
        self.active = False
        
    def start_animation(self):
        self.active = True
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        # Create initial streams
        self.streams = []
        for i in range(int(self.width / 20)):  # Adjust density of streams
            x = random.randint(10, self.width - 10)
            speed = random.uniform(1, 3)
            self.streams.append({"x": x, "y": 0, "speed": speed, "length": random.randint(5, 15), 
                                "chars": [random.choice(self.chars) for _ in range(20)]})
        self.animate()
    
    def animate(self):
        if not self.active:
            return
        
        self.delete("all")
        
        # Process each stream
        for stream in self.streams:
            x, y = stream["x"], stream["y"]
            speed = stream["speed"]
            stream_chars = stream["chars"]
            length = stream["length"]
            
            # Draw characters in stream with fading effect
            for i in range(length):
                char_y = y - (i * 15)
                if 0 <= char_y <= self.height:
                    # Calculate green intensity based on position (brighter at head)
                    intensity = int(255 * (1 - i/length))
                    color = f"#{0:02x}{intensity:02x}{0:02x}"
                    self.create_text(x, char_y, text=stream_chars[i % len(stream_chars)], 
                                    fill=color, font=("Courier", 12, "bold"))
            
            # Move stream down
            stream["y"] += speed
            
            # Replace first character randomly
            if random.random() < 0.1:
                stream_chars[0] = random.choice(self.chars)
            
            # Restart stream if it's gone too far
            if y > self.height + length * 15:
                stream["y"] = 0
                stream["x"] = random.randint(10, self.width - 10)
                stream["chars"] = [random.choice(self.chars) for _ in range(20)]
        
        # Randomly add new streams
        if random.random() < 0.05 and len(self.streams) < self.width / 10:
            x = random.randint(10, self.width - 10)
            speed = random.uniform(1, 3)
            self.streams.append({"x": x, "y": 0, "speed": speed, "length": random.randint(5, 15), 
                                "chars": [random.choice(self.chars) for _ in range(20)]})
        
        self.after(50, self.animate)
    
    def stop_animation(self):
        self.active = False


class TypewriterText(ScrolledText):
    """Text widget that displays text with a typewriter effect and initial garbled text"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.is_typing = False
        self._typing_thread = None
    
    def typewrite(self, text, delay=10, callback=None, garble_duration=100, garble_speed=20):
        """Add text with typewriter effect and initial garbled text, processing character by character"""
        if self.is_typing:  # Prevent multiple simultaneous typing animations
            return
            
        self.is_typing = True
        
        # Fix: Make sure text is properly prepared for line processing
        lines = text.splitlines() if text else [""]
        
        def _process_lines():
            """Process the text line by line with a proper typewriter effect"""
            try:
                for line in lines:
                    self.configure(state='normal')
                    current_pos = self.index(tk.END + "-1c")
                    
                    # Process each character with garbled text effect
                    for char in line:
                        # Add a garbled character first
                        garbled_char = random.choice(string.ascii_letters + string.digits)
                        self.insert(current_pos, garbled_char)
                        self.see(tk.END)
                        self.update_idletasks()
                        time.sleep(garble_speed / 1000)
                        
                        # Replace with correct character
                        self.delete(current_pos)
                        self.insert(current_pos, char)
                        self.see(tk.END)
                        self.update_idletasks()
                        time.sleep(delay / 1000)
                        
                        # Update current position
                        current_pos = self.index(tk.END + "-1c")
                    
                    # Add a newline after each line
                    self.insert(tk.END, "\n")
                    self.see(tk.END)
                    self.update_idletasks()
                    time.sleep(delay / 1000)
                    
                    self.configure(state='disabled')
            
            finally:
                self.is_typing = False
                if callback:
                    self.after(0, callback)
        
        # Start the typing process in a separate thread to prevent UI freezing
        self._typing_thread = threading.Thread(target=_process_lines, daemon=True)
        self._typing_thread.start()




class ClemmMatrixUI(tk.Tk):
    def __init__(self, crew_instance=None, model=None, max_tokens=None, model_name="UNKNOWN_MODEL", available_tools=None):
        super().__init__()
        self.title("CLEMM- MATRIX TERMINAL")
        self.geometry("968x1400")
        self.configure(bg='black')
        
        # Store backend components
        self.model = model
        self.max_tokens = max_tokens
        self.model_name = model_name
        self.available_tools = available_tools if available_tools else []
        self.crew_instance = crew_instance
        
        # Matrix theme colors
        self.matrix_green = "#00ff00"
        self.dark_green = "#003300"
        self.black = "#000000"
                 # Matrix theme colors with improved contrast
        #self.matrix_green = "#00ff66"  # Brighter green
        #self.dark_green = "#004422"    # Darker background for contrast
        #self.highlight_green = "#88ffaa"  # Highlight color
        #self.black = "#000000"
        #self.bg_dark = "#001100"  # Very dark green for better contrast


        # Create frame for the matrix rain effect background
        self.bg_frame = tk.Frame(self, bg=self.black)
        self.bg_frame.place(relwidth=1, relheight=1)
        
        # Matrix rain canvas in background
        self.matrix_canvas = MatrixRain(self.bg_frame, bg=self.black, highlightthickness=0)
        self.matrix_canvas.place(relwidth=1, relheight=1)
        
        # Semi-transparent frame for content
        self.content_frame = tk.Frame(self, bg=self.black)
        self.content_frame.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)
        
        # Header with system title
        self.header_frame = tk.Frame(self.content_frame, bg=self.black)
        self.header_frame.pack(fill='x', pady=(0, 10))
        
        self.title_label = tk.Label(self.header_frame, text="CLEMM MATRIX TERMINAL", 
                                   bg=self.black, fg=self.matrix_green, 
                                   font=("Courier", 18, "bold"))
        self.title_label.pack(side="left", padx=10)
        
        self.status_label = tk.Label(self.header_frame, text="STATUS: CONNECTED", 
                                    bg=self.black, fg=self.matrix_green, 
                                    font=("Courier", 12))
        self.status_label.pack(side="right", padx=10)
        
        # Output text area with matrix styling
        self.output_frame = tk.Frame(self.content_frame, bg=self.dark_green, bd=2, 
                                   relief="sunken", padx=2, pady=2)
        self.output_frame.pack(expand=True, fill='both', padx=10, pady=10)
        
        self.output_text = TypewriterText(self.output_frame, wrap='word', 
                                         bg=self.black, fg=self.matrix_green,
                                         insertbackground=self.matrix_green,
                                         selectbackground=self.dark_green,
                                         selectforeground=self.matrix_green,
                                         font=("Courier", 11),
                                         bd=0, padx=10, pady=10)
        self.output_text.pack(expand=True, fill='both')
        self.output_text.configure(state='disabled')
        
        # Command prompt frame
        self.command_frame = tk.Frame(self.content_frame, bg=self.black)
        self.command_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.prompt_label = tk.Label(self.command_frame, text="> ", 
                                    bg=self.black, fg=self.matrix_green, 
                                    font=("Courier", 12, "bold"))
        self.prompt_label.pack(side="left")
        
        # Input field with matrix styling
        self.input_entry = tk.Entry(self.command_frame, bg=self.black, fg=self.matrix_green,
                                  insertbackground=self.matrix_green, bd=0,
                                  font=("Courier", 12), relief="flat")
        self.input_entry.pack(fill='x', expand=True)
        self.input_entry.bind("<Return>", self.process_command_event)
        
        # Status bar
        self.status_bar = tk.Frame(self.content_frame, bg=self.dark_green, height=20)
        self.status_bar.pack(fill='x', padx=10, pady=(0, 10))
        
        self.crew_status = tk.Label(self.status_bar, text="NO CREW SELECTED", 
                                  bg=self.dark_green, fg=self.matrix_green, 
                                  font=("Courier", 10))
        self.crew_status.pack(side="left", padx=5)
        
        # Add tools status label
        self.tools_status = tk.Label(self.status_bar, text="TOOLS LOADED", 
                                  bg=self.dark_green, fg=self.matrix_green, 
                                  font=("Courier", 10))
        self.tools_status.pack(side="left", padx=5)
        
        self.system_status = tk.Label(self.status_bar, text="SYSTEM ONLINE", 
                                    bg=self.dark_green, fg=self.matrix_green, 
                                    font=("Courier", 10))
        self.system_status.pack(side="right", padx=5)
        
        # Animation and blinking cursor effect
        self.cursor_visible = True
        self.cursor_blink()
        
        # Store last code response
        self.last_code_response = ""
        
        # Initialize crew and tools
        self.crew = {}
        self.current_crew = None
        
        # Load available tools
        self.available_tools = []

        try:
            self.available_tools = list_tools()
            self.tools_status.config(text=f"TOOLS: {len(self.available_tools)} LOADED")
        except Exception as e:
            self.tools_status.config(text="TOOLS: ERROR LOADING")
            print(f"Error loading tools: {e}")
        
        # Initialize crew if provided
        if crew_instance:
            self.crew = crew_instance
            if self.crew:
                # Fix: Handle crew initialization properly
                if isinstance(self.crew, dict) and len(self.crew) > 0:
                    self.current_crew = next(iter(self.crew))
                    self.crew_status.config(text=f"ACTIVE: {self.current_crew.upper()}")
                else:
                    self.crew = None
                    self.current_crew = None
        else:
            # Initialize the system in a separate thread
            threading.Thread(target=self.initialize_system, daemon=True).start()
        
        # Setup menu for crew and tools actions with matrix style
        menubar = tk.Menu(self, bg=self.black, fg=self.matrix_green, activebackground=self.dark_green, 
                        activeforeground=self.matrix_green, bd=0)
        self.config(menu=menubar)
        
        crew_menu = tk.Menu(menubar, tearoff=0, bg=self.black, fg=self.matrix_green,
                          activebackground=self.dark_green, activeforeground=self.matrix_green)
        crew_menu.add_command(label="RESET CREW", command=self.reset_crew)
        crew_menu.add_command(label="LIST CREW", command=self.list_crew)
        menubar.add_cascade(label="CREW", menu=crew_menu)
        
        # Add Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0, bg=self.black, fg=self.matrix_green,
                           activebackground=self.dark_green, activeforeground=self.matrix_green)
        tools_menu.add_command(label="LIST TOOLS", command=self.list_tools)
        menubar.add_cascade(label="TOOLS", menu=tools_menu)
        
        # Add Model info menu
        model_menu = tk.Menu(menubar, tearoff=0, bg=self.black, fg=self.matrix_green,
                           activebackground=self.dark_green, activeforeground=self.matrix_green)
        model_menu.add_command(label="MODEL INFO", command=self.show_model_info)
        menubar.add_cascade(label="MODEL", menu=model_menu)
        
        # Boot sequence - make sure to run this AFTER UI setup is complete
        self.after(500, self.boot_sequence)
        
        # Start matrix rain effect after a short delay
        self.after(1000, self.matrix_canvas.start_animation)
        
        # Focus on input entry after initialization
        self.after(2000, lambda: self.input_entry.focus_set())
    
    def boot_sequence(self):
        """Display Matrix-style boot sequence"""
        welcome_text = """



 ██████╗██╗     ███████╗███╗   ███╗███╗   ███╗
██╔════╝██║     ██╔════╝████╗ ████║████╗ ████║
██║     ██║     █████╗  ██╔████╔██║██╔████╔██║
██║     ██║     ██╔══╝  ██║╚██╔╝██║██║╚██╔╝██║
╚██████╗███████╗███████╗██║ ╚═╝ ██║██║ ╚═╝ ██║
 ╚═════╝╚══════╝╚══════╝╚═╝     ╚═╝╚═╝     ╚═╝

            CLEMM-09 QUANTUM INTERFACE SYSTEM
            MISSION: EUROPA(JUPITER II) EXPLORATION
        
            INITIALIZING NEURAL INTERFACE...
            QUANTUM ENCRYPTION: ACTIVE
            QUANTUM TUNNELING: STABLE
        
            ACCESSING CREWNET...
        
            CONNECTING...
        """
        
         # Clear output text area first
        self.output_text.configure(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.configure(state='disabled')
        self.output_text.typewrite(welcome_text, delay=5, callback=lambda: self.append_output(
            "SYSTEM READY. TYPE 'HELP' FOR AVAILABLE COMMANDS."))

    def cursor_blink(self):
        """Create blinking cursor effect in input field"""
        if self.cursor_visible:
            self.input_entry.config(insertbackground=self.matrix_green)
        else:
            self.input_entry.config(insertbackground=self.black)
        
        self.cursor_visible = not self.cursor_visible
        self.after(500, self.cursor_blink)
    
    def initialize_system(self):
        """Initialize the system with Matrix-style messages"""
        #loading_messages = [
         #   "DECRYPTING QUANTUM DATABASE...",
          #  "ESTABLISHING NEURAL LINK...",
           # "CALCULATING QUANTUM PATHWAYS...",
            #"SYNCHRONIZING TIMELINES...",
            #"LOADING AI CREW PROFILES..."
        #]
        # Commented out for demonstration they should work fine inside a working framework.
        # Fix: Add delays between messages for better effect
        for msg in loading_messages:
            self.append_output(msg)
            time.sleep(0.5)
        
        self.append_output("INITIALIZATION COMPLETE. SYSTEM READY.")
        self.system_status.config(text="READY FOR COMMANDS")
    
    def append_output(self, text):
        """Add text to output directly"""
        self.output_text.configure(state='normal')
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)
        self.output_text.configure(state='disabled')
       # if not text:
        #    return
        #self.output_text.configure(state='normal') 
        #def animation_complete():
        #    self.output_text.see(tk.END)
        #    self.output_text.update_idletasks()   
        #self.output_text.typewrite(text, delay=2, callback=animation_complete)
    
    def process_command_event(self, event):
        """Process command when Enter is pressed"""
        self.process_command()
    
    def process_command(self):
        """Process entered command with Matrix-style feedback"""
        command = self.input_entry.get().strip()
        if not command:
            return
        
        # Display command with green color
        self.append_output(f"> {command}")
        self.input_entry.delete(0, tk.END)
        
        # Process with some visual effects
        self.system_status.config(text="PROCESSING...")
        self.after(200, lambda: self.execute_command(command))
    
    def execute_command(self, command):
        """Execute the command with Matrix flair"""
        command_lower = command.lower()
        print(f"Executing command: {command_lower}")  # Debug print
        
        if command_lower == "exit":
            self.append_output("DISCONNECTING FROM MATRIX...")
            if self.model.get("type") == "server":
                self.append_output("Terminating server process...")
                self.model["process"].terminate()  
            self.after(1000, self.quit)
        
        elif command_lower == "help":
            self.output_text.configure(state='normal')
            help_text = """
AVAILABLE COMMANDS:
===================
HELP       - ACCESS THIS INFORMATION NODE
EXIT       - TERMINATE NEURAL CONNECTION
STATUS     - DISPLAY SYSTEM DIAGNOSTICS
DESTINATION - REVEAL CURRENT MISSION COORDINATES
MODEL_INFO - DISPLAY ACTIVE MODEL CONFIGURATION
ASK [QUERY] - INTERROGATE CREW KNOWLEDGE BASE
CREW       - LIST AVAILABLE CREW MEMBERS
TOOLS      - LIST AVAILABLE SPECIALIZED TOOLS
USE [NAME] - SWITCH ACTIVE CREW MEMBER
RESET      - PURGE CONVERSATION MEMORY
RUN_TOOL [TOOL_NAME] - EXECUTE SPECIALIZED TOOLS
RUN_CODE   - EXECUTE LAST GENERATED CODE SEQUENCE
"""
            #self.output_text.insert(tk.END, help_text + "\n")
            #self.output_text.see(tk.END)
            #self.output_text.configure(state='disabled')
            self.output_text.configure(state='normal')
            self.output_text.typewrite(help_text, delay=1, 
                                      callback=lambda: self.output_text.see(tk.END))

        
        elif command_lower == "status":
            model_type = "GGUF"
            status_text = f"""
╔════════════════════════════════════════╗
║ SYSTEM STATUS: ALL SYSTEMS OPERATIONAL ║
╠════════════════════════════════════════╣
║ QUANTUM CORE................ ONLINE    ║
║ NEURAL INTERFACE............ ACTIVE    ║
║ CREW CONNECTION............. {"STABLE" if self.crew else "OFFLINE"}    ║
║ ENCRYPTION PROTOCOLS........ SECURE    ║
║ LIFE SUPPORT................ NOMINAL   ║
║ MODEL TYPE....................... {model_type} ║
║ TOOLS............................ {len(self.available_tools) if self.available_tools else "N/A"}    ║
╚════════════════════════════════════════╝
  Active Crew: {self.current_crew.upper() if self.current_crew else "NONE"}
"""
            #self.output_text.configure(state='normal')
            #self.output_text.delete(1.0, tk.END)
            #self.output_text.configure(state='disabled')
            self.output_text.configure(state='normal')
            self.output_text.typewrite(status_text, delay=1, 
                              callback=lambda: self.output_text.see(tk.END))
            

        
        elif command_lower == "destination":
            dest_text = """
TARGET: EUROPA (JUPITER II)
MISSION: SUBSURFACE EXPLORATION
ETA: 267 DAYS 14 HOURS
STATUS: ON COURSE
"""         
            self.output_text.configure(state='normal')
            self.output_text.typewrite(dest_text, delay=1, 
                                      callback=lambda: self.output_text.see(tk.END))
            #self.append_output(dest_text)
        
        elif command_lower in ["crew", "list crew"]:
            self.list_crew()
        
        elif command_lower in ["tools", "list tools"]:
            self.list_tools()
        
        elif command_lower in ["model_info", "model info"]:
            self.show_model_info()
        
        elif command_lower.startswith("use "):
            crew_name = command[4:].strip()
            if self.crew and crew_name in self.crew:
                self.current_crew = crew_name
                self.crew[crew_name].reset()
                self.last_code_response = ""
                self.append_output(f"SWITCHING NEURAL LINK: {crew_name.upper()}")
                self.crew_status.config(text=f"ACTIVE: {crew_name.upper()}")
            else:
                self.append_output(f"ERROR: CREW MEMBER '{crew_name.upper()}' NOT FOUND IN DATABASE")
        
        elif command_lower == "reset":
            if self.crew and self.current_crew in self.crew:
                self.crew[self.current_crew].reset()
                self.last_code_response = ""
                self.append_output(f"MEMORY PURGE COMPLETE: {self.current_crew.upper()}")
            else:
                self.append_output("ERROR: NO CREW MEMBER ACTIVE")
        
        elif command_lower.startswith("ask "):
            query = command[4:].strip()
            if not query:
                self.append_output("ERROR: QUERY PARAMETER REQUIRED")
                return
            
            if self.crew and self.current_crew in self.crew:
                self.append_output(f"PROCESSING QUERY THROUGH {self.current_crew.upper()}...")
                threading.Thread(target=self.process_ask, args=(query,), daemon=True).start()
            else:
                self.append_output("ERROR: NO ACTIVE CREW MEMBER")
        
        elif command_lower.startswith("run_tool"):
            parts = command.split(maxsplit=1)
            if len(parts) < 2:
                self.append_output("ERROR: TOOL IDENTIFIER REQUIRED")
                return
            
            tool_name = parts[1].strip()
            self.append_output(f"EXECUTING TOOL: '{tool_name.upper()}'")
            self.system_status.config(text="RUNNING TOOL...")
            
            # Run in a separate thread to prevent UI freezing
            threading.Thread(target=self.execute_tool, args=(tool_name,), daemon=True).start()
        
        elif command_lower == "run_code":
            if self.current_crew == "code_expert" and self.last_code_response:
                self.append_output("\n⚠ SECURITY WARNING ⚠")
                self.append_output("UNAUTHORIZED CODE EXECUTION DETECTED")
                self.append_output("REVIEW BEFORE PROCEEDING:\n")
                self.append_output(self.last_code_response)
                
                def show_confirm_dialog():
                    confirm = messagebox.askyesno(
                        "EXECUTE CODE?", 
                        "EXECUTE POTENTIALLY DANGEROUS CODE SEQUENCE?",
                        icon="warning"
                    )
                    if confirm:
                        try:
                            self.append_output("\n--- EXECUTING CODE SEQUENCE ---")
                            process = subprocess.run(
                                ['python', '-c', self.last_code_response],
                                capture_output=True, text=True, check=False
                            )
                            if process.returncode == 0:
                                self.append_output("--- EXECUTION SUCCESSFUL ---")
                                self.append_output(process.stdout)
                            else:
                                self.append_output("--- EXECUTION ERROR ---")
                                self.append_output(process.stderr)
                        except Exception as e:
                            self.append_output(f"FATAL ERROR: {e}")
                    else:
                        self.append_output("CODE EXECUTION ABORTED")
                
                self.after(500, show_confirm_dialog)
            else:
                self.append_output("ERROR: NO CODE SEQUENCE AVAILABLE")
        
        else:
            self.append_output("COMMAND NOT RECOGNIZED")
            self.append_output("TYPE 'HELP' FOR COMMAND LIST")
        
        self.system_status.config(text="READY FOR COMMANDS")
    
    def execute_tool(self, tool_name):
        """Execute a tool in a separate thread"""
        try:
            result = run_tool(tool_name, crew_instance=self.crew)
            self.append_output(f"TOOL EXECUTION COMPLETE")
            self.append_output(f"RESULT: {result}")
            
            # If there's an active crew, send the result back for processing
           # if self.crew and self.current_crew in self.crew:
            #    feedback_response = self.crew[self.current_crew].chat(f"Tool execution result: {result}")
             #   if not isinstance(feedback_response, str) or not feedback_response.lower().startswith("run_tool"):
              #      self.append_output(f"CREW ANALYSIS: {feedback_response}")
            
        except Exception as e:
            self.append_output(f"ERROR IN TOOL EXECUTION: {e}")
        
        self.system_status.config(text="READY FOR COMMANDS")

    def process_ask(self, query):
        """Process an ask command with animation"""
        try:
            self.system_status.config(text="PROCESSING QUERY...")
            response = self.crew[self.current_crew].chat(query)
            
            header = f"\n[{self.current_crew.upper()} RESPONSE]:\n"
            self.append_output(header + "═" * (len(header) - 3))
            self.append_output(response)
            
            # Store code responses for potential execution
            if self.current_crew == "code_expert":
                self.last_code_response = response
                
        except Exception as e:
            self.append_output(f"ERROR IN NEURAL INTERFACE: {e}")
        finally:
            self.system_status.config(text="READY FOR COMMANDS") 
                
    def reset_crew(self):
        """Reset current crew member"""
        if self.crew and self.current_crew in self.crew:
            self.crew[self.current_crew].reset()
            self.last_code_response = ""
            self.append_output(f"NEURAL LINK RESET: {self.current_crew.upper()}")
        else:
            self.append_output("ERROR: NO ACTIVE CREW MEMBER")
    
    def list_crew(self):
        """List available crew members"""
        if self.crew and isinstance(self.crew, dict) and len(self.crew) > 0:
            crew_list = [f"[{i}] {crew_name.upper()} - STATUS: {'ACTIVE' if crew_name == self.current_crew else 'STANDBY'}"
                     for i, crew_name in enumerate(self.crew.keys(), 1)]
            show_crew = "CREW MANIFEST:\n══════════════\n" + f"Active Crew: {self.current_crew.upper() if self.current_crew else 'NONE'}\n" + "\n".join(crew_list)
            self.append_output(show_crew)
        else:
            self.append_output("ERROR: CREW DATABASE EMPTY")
    

    def list_tools(self):
        """Tool information"""
        tools_list = list_tools()
        show_tools = "\nTools List: " + ", ".join(tools_list)
        self.append_output(show_tools)


    
    def show_model_info(self):
        """Display model information"""
        model_type = "GGUF"  # Fixed to GGUF as model_choice is removed
        model_info = f"""
    MODEL INFORMATION:
    ══════════════════
    TYPE: {model_type}
    MAX TOKENS: {self.max_tokens}
    BACKEND: LLAMA.CPP
    STATUS: {'LOADED' if self.model is not None else 'NOT LOADED'}
    """
        self.append_output(model_info)


def launch_matrix_ui(model, crew_instance, max_tokens):
    model_name = getattr(model, 'model_path', 'Unknown GGUF Model')
    if isinstance(model_name, str) and '/' in model_name:
        import os
        model_name = os.path.basename(model_name)
    #tokenizer_name = "N/A (GGUF)"
    available_tools = list_tools() if 'list_tools' in globals() else []
    app = ClemmMatrixUI(
        crew_instance=crew_instance,
        model=model,
        max_tokens=max_tokens,
        model_name=model_name,
        #tokenizer_name=tokenizer_name,
        available_tools=available_tools
    )
    app.mainloop()

if __name__ == "__main__":
    # If you run this file directly without passing a preloaded crew,
    # the UI will initialize the system as before.
    app = ClemmMatrixUI()
    app.mainloop()
