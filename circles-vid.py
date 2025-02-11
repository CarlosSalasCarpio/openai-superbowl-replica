import streamlit as st
import cv2
import numpy as np
from PIL import Image
import tempfile
import os
import time

st.title("ChatGPT Super Bowl Ad Creator")
st.write(
    "Upload an MP4 video, adjust the dot size and color inversion, and generate a stunning halftone animation.\n\n"
    "Note: If you modify the slider or checkbox, click 'Generate Frames' to update the animation."
)

# Upload video
uploaded_video = st.file_uploader("Choose an MP4 video", type=["mp4"])

# Halftone effect controls
cell_size = st.slider("Dot Size (Cell Size)", min_value=4, max_value=50, value=10, step=1)
inversion = st.checkbox("Invert Colors (White background with black dots)", value=False)

# Define a maximum file size (50 MB in this example)
max_file_size = 50 * 1024 * 1024  # 50 MB in bytes

# Using session_state to store processed frames
if "frames" not in st.session_state:
    st.session_state.frames = None

if uploaded_video is not None:
    if uploaded_video.size > max_file_size:
        st.error("El archivo excede el tamaño máximo permitido de 50 MB.")
    else:
        if st.button("Generate Frames"):
            # Save the uploaded video to a temporary file for OpenCV processing
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tfile.write(uploaded_video.read())
            tfile.flush()

            cap = cv2.VideoCapture(tfile.name)
            if not cap.isOpened():
                st.error("Error opening the video.")
            else:
                fps = cap.get(cv2.CAP_PROP_FPS)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                # Limitamos a los primeros 10 segundos para evitar sobrecarga
                max_frames = int(min(total_frames, fps * 10))
                # Muestreamos aproximadamente 10 frames por segundo
                sample_interval = max(int(round(fps / 10)), 1)
                st.write(
                    f"FPS: {fps:.2f}, Total frames: {total_frames}. Processing up to {max_frames} frames, "
                    f"sampling every {sample_interval} frame(s)."
                )

                processed_frames = []
                frame_idx = 0
                with st.spinner("Extracting and processing frames..."):
                    while frame_idx < max_frames:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        if frame_idx % sample_interval == 0:
                            h, w, _ = frame.shape
                            # Seleccionar colores según la inversión
                            bg_color = 255 if inversion else 0
                            dot_color = 0 if inversion else 255
                            # Crear imagen en escala de grises con el fondo indicado
                            dotted = np.full((h, w), bg_color, dtype=np.uint8)
                            # Convertir el frame a escala de grises
                            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                            # Procesar la imagen en una cuadrícula definida por cell_size
                            for y in range(0, h, cell_size):
                                for x in range(0, w, cell_size):
                                    cell = gray[y:min(y + cell_size, h), x:min(x + cell_size, w)]
                                    avg_brightness = np.mean(cell) / 255.0
                                    # Con halftone:
                                    #   • Si se invierte, las zonas oscuras generan puntos grandes.
                                    #   • Si no se invierte, las zonas claras generan puntos grandes.
                                    if inversion:
                                        radius = (1 - avg_brightness) * (cell_size / 2)
                                    else:
                                        radius = avg_brightness * (cell_size / 2)
                                    # Centro de la celda
                                    cell_w = min(cell_size, w - x)
                                    cell_h = min(cell_size, h - y)
                                    cx = int(x + cell_w / 2)
                                    cy = int(y + cell_h / 2)
                                    if radius > 0:
                                        cv2.circle(dotted, (cx, cy), int(radius), dot_color, thickness=-1)
                            processed_frames.append(dotted)
                        frame_idx += 1
                    cap.release()
                os.remove(tfile.name)

                if not processed_frames:
                    st.error("No frames were processed.")
                else:
                    # Convert each processed frame (NumPy array) to a PIL Image
                    pil_frames = [Image.fromarray(frame) for frame in processed_frames]
                    st.session_state.frames = pil_frames
                    st.success("Frames successfully processed!")

        if st.session_state.frames is not None:
            if st.button("Play Animation"):
                placeholder = st.empty()
                # Bucle infinito para reproducir la animación en ciclo
                while True:
                    for idx, frame in enumerate(st.session_state.frames):
                        placeholder.image(frame, caption=f"Frame {idx+1}", use_container_width=True)
                        time.sleep(0.1)