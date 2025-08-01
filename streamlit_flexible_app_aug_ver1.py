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

    # Xác định vị trí từng ảnh
    if group_size == 2:
        positions = [0, 200]
    elif group_size == 3:
        positions = [0, 95, 200]
    elif group_size == 4:
        positions = [0, 60, 130, 200]
    else:
        raise ValueError("Chỉ hỗ trợ nhóm 2, 3 hoặc 4 ảnh")

    # Dán ảnh từ phải qua trái
    for i in reversed(range(group_size)):
        img = resize_card(load_image_from_url(urls[i]))
        canvas.paste(img, (positions[i], 0), img)

    filename = f"{output_name}.png"
    canvas.save(filename)
    return filename

st.title("🧩 Tool Ghép Ảnh MULTICARD (2 - 3 - 4 ảnh)")

# B1: Chọn số lượng ảnh mỗi nhóm
group_size = st.selectbox("🔢 Chọn số ảnh trong mỗi nhóm:", [2, 3, 4])

# B2: Upload CSV
uploaded_file = st.file_uploader("📎 Tải lên file CSV (2 cột: tên, url)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if len(df) % group_size != 0:
        st.error(f"❌ Số dòng phải chia hết cho {group_size}.")
    elif df.shape[1] < 2:
        st.error("❌ File CSV phải có ít nhất 2 cột: tên và url")
    else:
        result_files = []
        for i in range(0, len(df), group_size):
            group = df.iloc[i:i+group_size]
            name = str(group.iloc[0, 0])
            urls = [u.strip() for u in group.iloc[:, 1].tolist()]
            try:
                result_file = merge_images(urls, name, group_size)
                result_files.append(result_file)

                # ✅ Hiển thị ảnh với kích thước thật
                st.image(Image.open(result_file), caption=name)

                # ✅ Tải riêng từng ảnh
                with open(result_file, "rb") as img_file:
                    st.download_button("📥 Tải ảnh này", img_file, file_name=result_file, mime="image/png")

            except Exception as e:
                st.error(f"Lỗi khi xử lý nhóm {name}: {e}")

        # ✅ Nén ZIP nếu có nhiều ảnh
        if result_files:
            zip_filename = f"merged_images_{group_size}cards.zip"
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for file in result_files:
                    zipf.write(file)

            with open(zip_filename, "rb") as f:
                st.download_button("📦 Tải tất cả ảnh dưới dạng ZIP", f, file_name=zip_filename)

            # Cleanup (tùy chọn)
            for file in result_files:
                os.remove(file)
            os.remove(zip_filename)
