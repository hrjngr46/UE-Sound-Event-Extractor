import json
import os
import sys
import tkinter as tk
from tkinter import messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
import csv

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def parse_json(json_data):
    anim_seq = next((entry for entry in json_data if entry.get("Type") == "AnimSequence"), None)
    if not anim_seq:
        raise ValueError("AnimSequence not found in JSON")

    props = anim_seq.get("Properties", {})
    notifies = props.get("Notifies", [])
    num_frames = props.get("NumFrames")
    seq_length = props.get("SequenceLength")

    if not num_frames or not seq_length:
        raise ValueError("Insufficient animation data")

    fps = round(num_frames / seq_length, 4)

    sound_entries = {
        f"AnimNotify_WeaponSound'{entry.get('Outer')}:{entry.get('Name')}'": entry
        for entry in json_data
        if entry.get("Type") == "AnimNotify_WeaponSound"
    }

    result = []
    for notify in notifies:
        if notify.get("NotifyName") != "WeaponSound":
            continue

        time_sec = notify.get("Time", notify.get("LinkValue", 0))
        frame = round(time_sec * fps)
        object_name = notify.get("Notify", {}).get("ObjectName", "")
        sound_entry = sound_entries.get(object_name)

        sound_name = "Unknown"
        if sound_entry:
            props = sound_entry.get("Properties", {})
            raw_name = (
                props.get("Event_FP", {}).get("ObjectName")
                or props.get("Event_TP", {}).get("ObjectName")
                or "Unknown"
            )

            if isinstance(raw_name, str) and raw_name.startswith("AkAudioEvent'"):
                sound_name = raw_name.replace("AkAudioEvent'", "").strip("'")
            else:
                sound_name = raw_name

        result.append({
            "Time (sec)": round(time_sec, 4),
            "Frame": frame,
            "Sound": sound_name
        })

    return result

def write_csv(data, output_path):
    with open(output_path, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Time (sec)", "Frame", "Sound"],
            delimiter='\t',
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL
        )
        writer.writeheader()
        writer.writerows(data)

def process_files(filepaths):
    success_count = 0
    for filepath in filepaths:
        try:
            if not filepath.lower().endswith('.json'):
                continue

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            result = parse_json(data)
            if not result:
                continue

            output_csv = os.path.splitext(filepath)[0] + "_sounds.csv"
            write_csv(result, output_csv)
            success_count += 1

        except Exception as e:
            print(f"Error processing {filepath}: {str(e)}")

    return success_count

class DragDropWindow(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("UE Sound Event Extractor")
        self.geometry("550x250")
        self.configure(bg="#f0f0f0")

        try:
            self.iconbitmap(resource_path("app.ico"))
        except:
            pass

        self.setup_ui()

    def setup_ui(self):
        main_frame = tk.Frame(self, bg="#f0f0f0", padx=20, pady=20)
        main_frame.pack(expand=True, fill="both")

        self.drop_label = tk.Label(
            main_frame,
            text="Drag & Drop JSON Files Here\n(Supports multiple files)",
            bg="white",
            fg="#333",
            font=("Arial", 12),
            relief="groove",
            borderwidth=2,
            padx=50,
            pady=60,
            cursor="hand2"
        )
        self.drop_label.pack(expand=True, fill="both")

        self.status_label = tk.Label(
            main_frame,
            text="Ready to process files",
            bg="#e0e0e0",
            fg="#555",
            font=("Arial", 10)
        )
        self.status_label.pack(fill="x", pady=(10, 0))

        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        filepaths = [f for f in self.tk.splitlist(event.data) if f.lower().endswith('.json')]
        if not filepaths:
            self.show_status("No JSON files found", "red")
            return

        self.show_status(f"Processing {len(filepaths)} files...", "blue")
        self.update()

        success_count = process_files(filepaths)

        if success_count > 0:
            self.show_status(f"Success: {success_count} files processed", "green")
            messagebox.showinfo("Complete", f"Processed {success_count} files")
        else:
            self.show_status("No valid files processed", "orange")

    def show_status(self, text, color):
        self.status_label.config(text=text, fg=color)

if __name__ == "__main__":
    app = DragDropWindow()
    app.mainloop()
