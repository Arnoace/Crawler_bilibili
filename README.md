# Bilibili 课程目录提取与清洗工具

一个用于自动获取 Bilibili 课程目录、清洗短视频并最终处理数据的自动化工具脚本集。

---

## 🛠️ 环境准备

在运行脚本之前，请确保已激活你的虚拟环境并安装了必要的依赖。

```bash
# 激活虚拟环境（以 Windows PowerShell 为例）
.\backend\venv\Scripts\Activate.ps1

# 安装依赖（根据你的实际项目需求安装，如 requests 等）
# pip install -r requirements.txt

## 🚀 使用指南

请严格按照以下步骤顺序操作：

### 📊 整体数据流向示意

```text
[B站网页端] ➔ (User-Agent/Cookie) ➔ b_homepage_tools.py ➔ [原始目录数据]
                                                                │
   ┌────────────────────────────────────────────────────────────┘
   ▼
clean_homepage.py ➔ (筛除 <30分钟 视频) ➔ [清洗后的精简数据]
                                                 │
   ┌─────────────────────────────────────────────┘
   ▼
b_tools.py ➔ [最终处理/分析/导出结果]

### 难度评级脚本使用流程
  cd difficulty_rating
  python difficulty_rating.py       #
  生成评级表
  python import_to_crawledData.py   # 导入到crawledData(数据文件夹)
