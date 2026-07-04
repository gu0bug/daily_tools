# Paul Graham Essays Bilingual EPUB Generator

这是一个自动获取 [Paul Graham 文集中英对照网](https://pg.imwsl.com/) 上所有双语文章，并将其打包制作成精美中英对照电子书 EPUB 的工具。

## 功能特点

- **双语对照排版**：生成段落级的中英对照排版，英文在上（使用 Serif 衬线字体），中文在下（使用 Sans-serif 避头尾排版且有优雅的 `0.85` 不透明度，完美适配电子书阅读器的日间与夜间/深色模式）。
- **零外部依赖**：仅使用 Python 标准库（如 `urllib`, `zipfile`, `json`, `html` 等）开发，无需安装任何第三方依赖包，有 Python 运行环境即可直接使用。
- **离线与容灾**：支持从远程直接抓取最新文章。
- **年代顺序**：将文章自动整理为按发表时间升序排列（从早到晚），符合阅读文集的习惯。
- **精美封面**：内置了一张精心设计的高清书籍封面。

## 目录结构

- `builder.py`：构建脚本，运行它以抓取数据并打包成 EPUB 电子书。
- `cover.png`：高清书籍封面。
- `paul_graham_essays_bilingual.epub`：已生成好的中英对照电子书文件。

## 使用说明

1. 确保已安装 Python 3 环境。
2. 在当前目录下，运行以下命令即可重新抓取并生成电子书：
   ```bash
   python builder.py
   ```
3. 运行完成后，在当前目录下会生成 `paul_graham_essays_bilingual.epub` 文件。你可以将它导入到掌阅、Kindle、Apple Books 等任意支持 EPUB 格式的阅读器中阅读。
