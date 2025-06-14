import streamlit as st
import pandas as pd
from PIL import Image
import requests
from io import BytesIO
import zipfile
import os

def load_image_from_url(url):
    response = requests.get(url)
    return Image.open(BytesIO(response.content)).convert("RGBA")

def resize_card(img, width=210, height=336):
    return img.resize((width, height), Image.LANCZOS)

def merge_four_images(urls, output_name):
    card_width, card_height = 210, 336
    output_width, output_height = 410, 336

    x_A = 0
    x_B = x_A + 60
    x_C = x_B + 70
    x_D = x_C + 70

    img_A = resize_card(load_image_from_url(urls[0]))
    img_B = resize_card(load_image_from_url(urls[1]))
    img_C = resize_card(load_image_from_url(urls[2]))
    img_D = resize_card(load_image_from_url(urls[3]))

    canvas = Image.new("RGBA", (output_width, output_height), (0, 0, 0, 0))
    canvas.paste(img_D, (x_D, 0), img_D)
    canvas.paste(img_C, (x_C, 0), img_C)
    canvas.paste(img_B, (x_B, 0), img_B)
    canvas.paste(img_A, (x_A, 0), img_A)

    filename = f"{output_name}.png"
    canvas.save(filename)
    return filename

st.title("🖼️ Ghép 4 ảnh MULTICARD thành 1 ảnh 410x336")

uploaded_file = st.file_uploader("📎 Tải lên file CSV (2 cột: tên, url)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if len(df) % 4 != 0:
        st.error("❌ Số dòng trong file CSV phải chia hết cho 4.")
    elif df.shape[1] < 2:
        st.error("❌ File CSV phải có ít nhất 2 cột: tên và url")
    else:
        result_files = []
        for i in range(0, len(df), 4):
            group = df.iloc[i:i+4]
            name = str(group.iloc[0, 0])
            urls = group.iloc[:, 1].tolist()
            try:
                result_file = merge_four_images(urls, name)
                result_files.append(result_file)
                st.image(result_file, caption=name, width=300)
            except Exception as e:
                st.error(f"Lỗi khi xử lý nhóm {name}: {e}")

        # Nén kết quả
        if result_files:
            zip_filename = "merged_images_named.zip"
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for file in result_files:
                    zipf.write(file)

            with open(zip_filename, "rb") as f:
                st.download_button("📥 Tải tất cả ảnh dưới dạng ZIP", f, file_name=zip_filename)

            # Cleanup (tùy chọn)
            for file in result_files:
                os.remove(file)
            os.remove(zip_filename)
