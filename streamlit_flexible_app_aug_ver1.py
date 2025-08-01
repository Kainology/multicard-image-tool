import streamlit as st
import pandas as pd
from PIL import Image
import requests
from io import BytesIO
import zipfile
import os

def load_image_from_url(url):
    response = requests.get(url)
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGBA")

def resize_card(img, width=210, height=336):
    return img.resize((width, height), Image.LANCZOS)

def merge_images(urls, output_name, group_size):
    output_width, output_height = 410, 336
    canvas = Image.new("RGBA", (output_width, output_height), (0, 0, 0, 0))

    if group_size == 2:
        positions = [0, 200]
    elif group_size == 3:
        positions = [0, 95, 200]
    elif group_size == 4:
        positions = [0, 60, 130, 200]
    else:
        raise ValueError("Chỉ hỗ trợ nhóm 2, 3 hoặc 4 ảnh")

    # Dán ảnh từ phải qua trái (để A ở trên cùng)
    for i in reversed(range(group_size)):
        img = resize_card(load_image_from_url(urls[i]))
        canvas.paste(img, (positions[i], 0), img)

    filename = f"{output_name}.png"
    canvas.save(filename)
    return filename

st.title("🧩 Tool Ghép Ảnh MULTICARD (Tự động nhóm, download từng ảnh hoặc tất cả)")

uploaded_file = st.file_uploader("📎 Tải lên file CSV (2 cột: tên, url)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if df.shape[1] < 2:
        st.error("❌ File CSV phải có ít nhất 2 cột: tên và url")
    else:
        result_files = []
        error_groups = []

        # Nhóm theo 'tên'
        grouped = df.groupby(df.columns[0])

        for name, group in grouped:
            urls = [u.strip() for u in group.iloc[:, 1].tolist()]
            group_size = len(urls)
            if group_size not in [2, 3, 4]:
                error_groups.append((name, group_size))
                continue
            try:
                result_file = merge_images(urls, str(name), group_size)
                result_files.append(result_file)
                
                # Đọc file ảnh vào bytes
                with open(result_file, "rb") as f:
                    image_bytes = f.read()
                
                # Hiển thị ảnh đúng kích thước gốc
                st.image(image_bytes, caption=f"{name} ({group_size} ảnh) [Kích thước gốc]", use_column_width=False)
                
                # Nút download từng ảnh
                st.download_button(
                    label="📥 Tải ảnh này",
                    data=image_bytes,
                    file_name=f"{name}.png",
                    mime="image/png"
                )
            except Exception as e:
                st.error(f"Lỗi khi xử lý nhóm {name}: {e}")

        if error_groups:
            error_text = ", ".join([f"{n} ({sz} ảnh)" for n, sz in error_groups])
            st.warning(f"Có nhóm không hợp lệ (chỉ hỗ trợ 2, 3, 4 ảnh): {error_text}")

        # Nén kết quả
        if result_files:
            zip_filename = "merged_images.zip"
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for file in result_files:
                    zipf.write(file)
            with open(zip_filename, "rb") as f:
                st.download_button("📦 Tải tất cả ảnh dưới dạng ZIP", f, file_name=zip_filename)
            # Xóa file tạm
            for file in result_files:
                os.remove(file)
            os.remove(zip_filename)
