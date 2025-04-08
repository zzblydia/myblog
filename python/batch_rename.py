import os

# 指定文件夹路径（请修改为你实际的文件夹路径）
folder_path = r"Z:\\plex\\laoyan\\家比天大\\"

# 遍历文件夹中的所有文件
for filename in os.listdir(folder_path):
    # 检查文件是否以《家比天大》开头且后缀为.mp4
    if filename.startswith("《家比天大》") and filename.endswith(".mp4"):
        # 提取 "xx" 部分，去掉开头的中括号和结尾的.mp4
        new_name_part = filename[6:8]
        # 构造新文件名
        new_filename = f"家比天大_{new_name_part}.mp4"
        
        # 构造旧文件和新文件的完整路径
        old_file = os.path.join(folder_path, filename)
        new_file = os.path.join(folder_path, new_filename)
        
        # 执行重命名
        os.rename(old_file, new_file)
        print(f"已重命名: {filename} -> {new_filename}")

        # break

print("重命名完成！")