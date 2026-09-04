import sys
import threading
import urllib.request
from pathlib import Path
import tkinter.messagebox as messagebox

import customtkinter as ctk
from llama_cpp import Llama


# --------------------------------------------------
# PyInstaller native splash
# --------------------------------------------------

try:
    import pyi_splash
except ImportError:
    pyi_splash = None


# --------------------------------------------------
# Configuration
# --------------------------------------------------

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent


MODEL_DIR = BASE_DIR / "models"

MODEL_NAME = "qwen2.5-0.5b-instruct-q4_k_m.gguf"

MODEL_PATH = MODEL_DIR / MODEL_NAME

MODEL_URL = (
    "https://huggingface.co/Qwen/"
    "Qwen2.5-0.5B-Instruct-GGUF/resolve/main/"
    "qwen2.5-0.5b-instruct-q4_k_m.gguf?download=true"
)


# --------------------------------------------------
# Global model
# --------------------------------------------------

llm = None


# --------------------------------------------------
# Appearance
# --------------------------------------------------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# --------------------------------------------------
# Main window
# --------------------------------------------------

if pyi_splash:
    try:
        pyi_splash.update_text("Starting Offline AI...")
    except Exception:
        pass


app = ctk.CTk()

app.title("Offline AI")
app.geometry("850x650")
app.minsize(650, 500)


# --------------------------------------------------
# Header
# --------------------------------------------------

header = ctk.CTkLabel(
    app,
    text="Offline AI",
    font=ctk.CTkFont(
        size=28,
        weight="bold",
    ),
)

header.pack(
    pady=(20, 5),
)


status_label = ctk.CTkLabel(
    app,
    text="Starting...",
    text_color="gray",
)

status_label.pack(
    pady=(0, 10),
)


# --------------------------------------------------
# Chat textbox
# --------------------------------------------------

chatbox = ctk.CTkTextbox(
    app,
    wrap="word",
    font=ctk.CTkFont(
        size=14,
    ),
)

chatbox.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=10,
)

chatbox.configure(
    state="disabled",
)


# --------------------------------------------------
# Input frame
# --------------------------------------------------

input_frame = ctk.CTkFrame(app)

input_frame.pack(
    fill="x",
    padx=20,
    pady=(0, 20),
)


prompt_entry = ctk.CTkEntry(
    input_frame,
    placeholder_text="Ask something...",
    height=42,
)

prompt_entry.pack(
    side="left",
    fill="x",
    expand=True,
    padx=(10, 5),
    pady=10,
)


send_button = ctk.CTkButton(
    input_frame,
    text="Send",
    width=100,
)

send_button.pack(
    side="right",
    padx=(5, 10),
    pady=10,
)


# --------------------------------------------------
# Conversation history
# --------------------------------------------------

conversation = [
    {
        "role": "system",
        "content": (
            "You are a helpful offline AI assistant. "
            "Give clear and concise answers. "
            "If you do not know something, say you do not know."
        ),
    }
]


# --------------------------------------------------
# Chat helper
# --------------------------------------------------

def add_message(role, text):

    chatbox.configure(
        state="normal"
    )

    if role == "user":

        chatbox.insert(
            "end",
            f"\nYou:\n{text}\n"
        )

    else:

        chatbox.insert(
            "end",
            f"\nAI:\n{text}\n"
        )

    chatbox.configure(
        state="disabled"
    )

    chatbox.see(
        "end"
    )


# --------------------------------------------------
# Download model
# --------------------------------------------------

def download_model():

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    download_window = ctk.CTkToplevel(app)

    download_window.title(
        "Downloading AI Model"
    )

    download_window.geometry(
        "500x240"
    )

    download_window.resizable(
        False,
        False
    )

    download_window.transient(app)
    download_window.grab_set()


    title = ctk.CTkLabel(
        download_window,
        text="Downloading Qwen2.5-0.5B",
        font=ctk.CTkFont(
            size=20,
            weight="bold"
        ),
    )

    title.pack(
        pady=(25, 10)
    )


    info = ctk.CTkLabel(
        download_window,
        text="Preparing download..."
    )

    info.pack(
        pady=5
    )


    progress = ctk.CTkProgressBar(
        download_window,
        width=420
    )

    progress.pack(
        pady=15
    )

    progress.set(0)


    percent_label = ctk.CTkLabel(
        download_window,
        text="0%"
    )

    percent_label.pack()


    note = ctk.CTkLabel(
        download_window,
        text="This may take a few minutes depending on your connection.",
        text_color="gray",
    )

    note.pack(
        pady=(5, 0)
    )


    temp_path = MODEL_PATH.with_suffix(
        ".download"
    )


    # --------------------------------------------------
    # Progress callback
    # --------------------------------------------------

    def progress_hook(
        block_number,
        block_size,
        total_size,
    ):

        downloaded = (
            block_number
            * block_size
        )

        if total_size <= 0:
            return

        downloaded = min(
            downloaded,
            total_size
        )

        fraction = (
            downloaded
            / total_size
        )

        percent = int(
            fraction * 100
        )


        downloaded_mb = (
            downloaded
            / 1024
            / 1024
        )

        total_mb = (
            total_size
            / 1024
            / 1024
        )


        def update_gui():

            progress.set(
                fraction
            )

            percent_label.configure(
                text=f"{percent}%"
            )

            info.configure(
                text=(
                    f"{downloaded_mb:.1f} MB "
                    f"/ {total_mb:.1f} MB"
                )
            )


        app.after(
            0,
            update_gui
        )


    # --------------------------------------------------
    # Actual download thread
    # --------------------------------------------------

    def do_download():

        try:

            urllib.request.urlretrieve(
                MODEL_URL,
                temp_path,
                progress_hook
            )


            temp_path.replace(
                MODEL_PATH
            )


            def finished():

                progress.set(1)

                percent_label.configure(
                    text="100%"
                )

                info.configure(
                    text="Download complete."
                )

                download_window.after(
                    700,
                    download_window.destroy
                )

                app.after(
                    800,
                    load_model_thread
                )


            app.after(
                0,
                finished
            )


        except Exception as error:

            if temp_path.exists():

                try:
                    temp_path.unlink()

                except Exception:
                    pass


            def failed():

                download_window.destroy()

                messagebox.showerror(
                    "Download Failed",
                    (
                        "The AI model could not be downloaded.\n\n"
                        f"{error}"
                    ),
                )

                status_label.configure(
                    text="Model download failed"
                )


            app.after(
                0,
                failed
            )


    threading.Thread(
        target=do_download,
        daemon=True
    ).start()


# --------------------------------------------------
# Check whether model exists
# --------------------------------------------------

def check_model():

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    if MODEL_PATH.exists():

        load_model_thread()

        return


    answer = messagebox.askyesno(
        "AI Model Required",
        (
            "Offline AI requires the Qwen2.5-0.5B model.\n\n"
            "Download size: approximately 491 MB.\n\n"
            "The model will be saved in:\n\n"
            f"{MODEL_DIR}\n\n"
            "Download it now?"
        ),
    )


    if answer:

        download_model()

    else:

        status_label.configure(
            text="Model not installed"
        )

        messagebox.showinfo(
            "Offline AI",
            (
                "The model is required before "
                "Offline AI can run."
            ),
        )


# --------------------------------------------------
# Load model in background
# --------------------------------------------------

def load_model_thread():

    status_label.configure(
        text="Loading AI model..."
    )

    send_button.configure(
        state="disabled"
    )

    prompt_entry.configure(
        state="disabled"
    )


    threading.Thread(
        target=load_model,
        daemon=True
    ).start()


# --------------------------------------------------
# Load Qwen
# --------------------------------------------------

def load_model():

    global llm

    try:

        llm = Llama(
            model_path=str(MODEL_PATH),
            n_ctx=2048,
            n_threads=4,
            verbose=False,
        )


        def ready():

            status_label.configure(
                text="Ready • Offline"
            )

            send_button.configure(
                state="normal"
            )

            prompt_entry.configure(
                state="normal"
            )

            prompt_entry.focus()


            add_message(
                "assistant",
                "Hello! I'm ready."
            )


        app.after(
            0,
            ready
        )


    except Exception as error:

        def failed():

            status_label.configure(
                text="Failed to load model"
            )

            messagebox.showerror(
                "Model Error",
                (
                    "The AI model could not be loaded.\n\n"
                    f"{error}"
                ),
            )


        app.after(
            0,
            failed
        )


# --------------------------------------------------
# Generate AI response
# --------------------------------------------------

def generate_response():

    global conversation

    try:

        response = llm.create_chat_completion(
            messages=conversation,
            max_tokens=300,
            temperature=0.3,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1,
        )


        answer = (
            response["choices"][0]
            ["message"]["content"]
            .strip()
        )


        conversation.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )


        def update_gui():

            add_message(
                "assistant",
                answer
            )

            status_label.configure(
                text="Ready • Offline"
            )

            send_button.configure(
                state="normal"
            )

            prompt_entry.configure(
                state="normal"
            )

            prompt_entry.focus()


        app.after(
            0,
            update_gui
        )


    except Exception as error:

        def failed():

            add_message(
                "assistant",
                f"Error: {error}"
            )

            status_label.configure(
                text="Ready • Offline"
            )

            send_button.configure(
                state="normal"
            )

            prompt_entry.configure(
                state="normal"
            )


        app.after(
            0,
            failed
        )


# --------------------------------------------------
# Send message
# --------------------------------------------------

def send(event=None):

    if llm is None:
        return


    question = (
        prompt_entry
        .get()
        .strip()
    )


    if not question:
        return


    prompt_entry.delete(
        0,
        "end"
    )


    add_message(
        "user",
        question
    )


    conversation.append(
        {
            "role": "user",
            "content": question,
        }
    )


    status_label.configure(
        text="Thinking..."
    )


    send_button.configure(
        state="disabled"
    )

    prompt_entry.configure(
        state="disabled"
    )


    threading.Thread(
        target=generate_response,
        daemon=True
    ).start()


# --------------------------------------------------
# Button / Enter bindings
# --------------------------------------------------

send_button.configure(
    command=send
)

prompt_entry.bind(
    "<Return>",
    send
)


# --------------------------------------------------
# Make sure main window is ready
# --------------------------------------------------

app.update_idletasks()


# --------------------------------------------------
# Close PyInstaller native splash
# --------------------------------------------------

if pyi_splash:

    try:

        pyi_splash.update_text(
            "Opening Offline AI..."
        )

        pyi_splash.close()

    except Exception:
        pass


# --------------------------------------------------
# Start model check
# --------------------------------------------------

app.after(
    300,
    check_model
)


# --------------------------------------------------
# Run
# --------------------------------------------------

app.mainloop()
