# 用法记录

## 1.宽高比调整
// scale=720:1280:force_original_aspect_ratio=decrease部分将视频缩放到指定的宽高比，并保持原始宽高比。  
// pad=720:1280:(ow-iw)/2:(oh-ih)/2部分将视频在垂直方向上进行填充，以适应新的宽高比。填充的部分将根据原始视频的宽高比在视频的顶部和底部均匀分布。  
**ffmpeg -i input.mp4 -vf "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2" output.mp4**  