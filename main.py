import zipfile
import os

zip_path = 'archiveNew.zip'

# Giải nén file zip
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall('.')  # Thư mục hiện tại

# Xóa file zip sau khi giải nén
os.remove(zip_path)
print("Giải nén thành công và đã xóa archiveNew.zip.")