"""
PDF Summarizer - PDF课件智能总结工具

批量处理PDF课件，调用AI大模型提取重点知识，生成结构化Word备考笔记。
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from pdf_summarizer.cli import app

__all__ = ["app", "__version__"]
