@echo off
setlocal
call D:\DEPTHWIZARD\backend\.venv\Scripts\activate.bat
python -m training.train_aerial_depth ^
  --data data\aerial_patches ^
  --model depth-anything\Depth-Anything-V2-Small-hf ^
  --output runs\aerial-depth ^
  --epochs 10 ^
  --batch-size 2 ^
  --lr 1e-5 ^
  --device cuda
endlocal
