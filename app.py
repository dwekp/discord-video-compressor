import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class DiscordCompressorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Discord Video Compressor (20MB)")
        self.root.geometry("480x280")
        self.root.resizable(False, False)

        # Estilo
        self.bg_color = "#2f3136"
        self.text_color = "#ffffff"
        self.accent_color = "#5865f2"
        
        self.root.configure(bg=self.bg_color)

        # Título
        lbl_title = tk.Label(
            root, text="Compressor para Discord", font=("Segoe UI", 16, "bold"),
            bg=self.bg_color, fg=self.text_color
        )
        lbl_title.pack(pady=15)

        # Botón para seleccionar archivo
        self.btn_select = tk.Button(
            root, text="Seleccionar Clip", font=("Segoe UI", 11, "bold"),
            bg=self.accent_color, fg="white", activebackground="#4752c4",
            activeforeground="white", relief="flat", padx=15, pady=8,
            command=self.select_file
        )
        self.btn_select.pack(pady=10)

        # Etiqueta de estado
        self.lbl_status = tk.Label(
            root, text="Selecciona un vídeo para reducirlo a <20MB",
            font=("Segoe UI", 9), bg=self.bg_color, fg="#b9bbbe"
        )
        self.lbl_status.pack(pady=10)

        # Barra de progreso
        self.progress = ttk.Progressbar(root, orient="horizontal", length=380, mode="indeterminate")
        self.progress.pack(pady=10)

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Selecciona el video",
            filetypes=[("Archivos de Video", "*.mp4 *.mov *.avi *.mkv *.webm")]
        )
        if file_path:
            self.btn_select.config(state="disabled")
            self.progress.start(10)
            threading.Thread(target=self.process_video, args=(file_path,), daemon=True).start()

    def process_video(self, file_path):
        try:
            self.update_status("Obteniendo duración del vídeo...")
            
            # Obtener duración con ffprobe
            cmd_probe = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                file_path
            ]
            duration_str = subprocess.check_output(cmd_probe, text=True).strip()
            duration = float(duration_str)

            # Cálculo de bitrate objetivo (20 MB)
            target_mb = 20
            audio_bitrate_kbps = 128
            target_size_bits = (target_mb * 0.95) * 8 * 1024 * 1024
            total_bitrate_bps = target_size_bits / duration
            video_bitrate_bps = total_bitrate_bps - (audio_bitrate_kbps * 1000)

            if video_bitrate_bps < 100000:
                raise Exception("El vídeo es demasiado largo para comprimirlo a 20MB con buena calidad.")

            video_bitrate_k = f"{int(video_bitrate_bps / 1000)}k"
            
            dir_name, full_name = os.path.split(file_path)
            base_name, _ = os.path.splitext(full_name)
            output_path = os.path.join(dir_name, f"{base_name}_discord.mp4")

            self.update_status(f"Comprimiendo vídeo a {video_bitrate_k}...")

            # Pasada 1
            pass1_cmd = [
                "ffmpeg", "-y", "-i", file_path,
                "-c:v", "libx264", "-b:v", video_bitrate_k,
                "-pass", "1", "-an", "-f", "null",
                "NUL" if os.name == "nt" else "/dev/null"
            ]
            subprocess.run(pass1_cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)

            # Pasada 2
            pass2_cmd = [
                "ffmpeg", "-y", "-i", file_path,
                "-c:v", "libx264", "-b:v", video_bitrate_k,
                "-pass", "2", "-c:a", "aac", "-b:a", f"{audio_bitrate_kbps}k",
                output_path
            ]
            subprocess.run(pass2_cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)

            # Limpieza
            for log_file in ["ffmpeg2pass-0.log", "ffmpeg2pass-0.log.mbtree"]:
                if os.path.exists(log_file):
                    os.remove(log_file)

            self.update_status("¡Finalizado con éxito!")
            messagebox.showinfo("Completado", f"Vídeo guardado como:\n{output_path}")

        except Exception as e:
            self.update_status("Error en el proceso.")
            messagebox.showerror("Error", str(e))
        finally:
            self.progress.stop()
            self.btn_select.config(state="normal")

    def update_status(self, text):
        self.lbl_status.config(text=text)

if __name__ == "__main__":
    root = tk.Tk()
    app = DiscordCompressorApp(root)
    root.mainloop()