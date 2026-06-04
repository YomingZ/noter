"""Integration Guide: Template Analysis System in Main Window.

This module demonstrates how to integrate the new template analysis
system into the main application window (gui_launcher.py).

Key Integration Points:
1. Connect template_analysis_requested signal to async handler
2. Initialize TemplateAnalyzer with AI function
3. Show TemplateConfigDialog after analysis completes
4. Pass modified analysis result to generation service

Usage:
    Copy relevant sections into your gui_launcher.py file and adapt as needed.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable, Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

from src.pdf_summarizer.template_analyzer import (
    TemplateAnalyzer,
    TemplateAnalysisResult,
)
from gui_launcher.template_config_dialog import TemplateConfigDialog


logger = logging.getLogger(__name__)


class TemplateAnalysisIntegration(QObject):
    """Helper class for integrating template analysis into main window.
    
    This class handles:
    - Async template analysis workflow
    - UI state management during analysis
    - Dialog presentation and result collection
    - Error handling and user feedback
    
    Usage in gui_launcher.py:
        # In __init__:
        self.template_integration = TemplateAnalysisIntegration(self)
        
        # Connect signals:
        self.obsidian_panel.template_analysis_requested.connect(
            self.template_integration.on_analysis_requested
        )
    """
    
    analysis_complete = pyqtSignal(object)  # Emits TemplateAnalysisResult
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent = parent
        
        # Initialize analyzer (lazy initialization)
        self._analyzer: Optional[TemplateAnalyzer] = None
        self._ai_generate_fn: Optional[Callable] = None
    
    def initialize_analyzer(self, ai_generate_fn: Callable):
        """Initialize the template analyzer with AI function.

        Args:
            ai_generate_fn: Async function for AI API calls
                           Signature: async fn(system_prompt, user_prompt, **kwargs) -> str
        """
        self._ai_generate_fn = ai_generate_fn
        self._analyzer = TemplateAnalyzer(
            ai_generate_fn=ai_generate_fn,
            cache_enabled=True,
        )
        logger.info("✅ [TemplateAnalysisIntegration] TemplateAnalyzer initialized successfully")

    def on_analysis_requested(self, template_path: str):
        """Handle template analysis request from ObsidianPanel.

        This method is connected to the template_analysis_requested signal.
        It triggers the async analysis workflow.

        Args:
            template_path: Path string to the .md template file
        """
        logger.info(f"🔍 [TemplateAnalysisIntegration] 收到分析请求: {template_path}")

        if not self._analyzer or not self._ai_generate_fn:
            logger.error("❌ [TemplateAnalysisIntegration] 分析器或 AI 函数未初始化")
            QMessageBox.warning(
                self._parent,
                "功能未就绪",
                "模板分析功能尚未初始化。请确保 AI 服务已配置正确。"
            )
            return

        logger.info(f"✅ [TemplateAnalysisIntegration] 验证通过，启动异步任务...")

        # Run async analysis in background
        asyncio.create_task(self._run_analysis_async(Path(template_path)))

    async def _run_analysis_async(self, template_path: Path):
        """Execute template analysis asynchronously.

        Workflow:
        1. Show loading indicator (optional - can add progress bar here)
        2. Call analyzer.analyze() (uses cache if available)
        3. Show TemplateConfigDialog with results
        4. Store user's modifications
        5. Emit completion signal

        Args:
            template_path: Path to analyze
        """
        import time

        phase_start = time.time()

        try:
            # ═══════════════════════════════════════
            # Phase 0: 准备阶段
            # ═══════════════════════════════════════
            logger.info(f"\n{'═'*60}")
            logger.info(f"🚀 [Analysis] 开始分析模板: {template_path.name}")
            logger.info(f"   📁 完整路径: {template_path}")
            logger.info(f"{'═'*60}\n")

            # 输出到 UI 日志（如果父窗口有 on_log 方法）
            if hasattr(self._parent, 'on_log'):
                self._parent.on_log(f"📂 [Phase 0] 加载模板文件...", "info")

            # ═══════════════════════════════════════
            # Phase 1 & 2: 分析阶段（自动处理缓存）
            # ═══════════════════════════════════════
            if hasattr(self._parent, 'on_log'):
                self._parent.on_log("⏳ [Phase 1] 规则引擎扫描中...", "info")

            logger.info("⏳ [Analysis Phase 1] 启动规则引擎扫描...")

            phase1_start = time.time()
            result = await self._analyzer.analyze(template_path)
            phase1_elapsed = time.time() - phase1_start

            logger.info(f"✅ [Analysis Phase 1&2] 分析完成 | 耗时: {phase1_elapsed:.2f}s")
            logger.info(f"   📊 检测风格: {result.style.value}")
            logger.info(f"   📈 置信度: {result.confidence:.2%}")
            logger.info(f"   ⚠️ 缺失项数量: {len(result.gaps)}")
            logger.info(f"   ✨ 已有特征数: {sum(1 for v in result.features.values() if v)}")

            if hasattr(self._parent, 'on_log'):
                self._parent.on_log(
                    f"✅ [Phase 1-2] 分析完成 ({phase1_elapsed:.2f}s)\n"
                    f"   风格: {result.style.value} | 置信度: {result.confidence:.0%} | 缺失: {len(result.gaps)}项",
                    "success"
                )

            # ═══════════════════════════════════════
            # Phase 3: 展示配置对话框
            # ═══════════════════════════════════════
            if hasattr(self._parent, 'on_log'):
                self._parent.on_log("🎨 [Phase 3] 打开配置面板...", "info")

            logger.info("🎨 [Analysis Phase 3] 创建配置对话框...")
            dialog = TemplateConfigDialog(result, parent=self._parent)

            if hasattr(self._parent, 'on_log'):
                self._parent.on_log("⏳ 等待用户确认配置...", "info")

            dialog_exec_result = dialog.exec()

            if dialog_exec_result:
                # 用户确认并做了修改
                logger.info("✅ [Analysis Phase 3] 用户点击「应用配置」")

                modified_result = dialog.get_modified_result()

                if modified_result:
                    # 存储结果到面板
                    from gui_launcher.obsidian_panel import ObsidianPanel
                    if hasattr(self._parent, 'obsidian_panel') and \
                       isinstance(self._parent.obsidian_panel, ObsidianPanel):
                        self._parent.obsidian_panel.set_analysis_result(modified_result)
                        logger.info("💾 [Analysis] 结果已存储到 ObsidianPanel")

                    # 发射信号通知其他组件
                    self.analysis_complete.emit(modified_result)

                    logger.info("📢 [Analysis] 已发射 analysis_complete 信号")

                    # 显示成功消息
                    total_elapsed = time.time() - phase_start

                    success_msg = (
                        f"✅ 模板「{template_path.stem}」分析完成！\n\n"
                        f"📊 检测到风格：{result.style.value}\n"
                        f"📈 置信度：{result.confidence:.0%}\n"
                        f"⚠️ 缺失项：{len(result.gaps)} 个（已优化）\n"
                        f"⏱️ 总耗时：{total_elapsed:.2f}s\n\n"
                        f"💡 点击「开始生成」按钮使用此配置生成笔记。"
                    )

                    QMessageBox.information(
                        self._parent,
                        "分析完成",
                        success_msg
                    )

                    logger.info(f"🎉 [Analysis] 全部流程完成！总耗时: {total_elapsed:.2f}s")

                    if hasattr(self._parent, 'on_log'):
                        self._parent.on_log(
                            f"🎉 [完成] 模板分析成功！| 总耗时: {total_elapsed:.2f}s",
                            "success"
                        )
                else:
                    logger.warning("⚠️ [Analysis] 对话框返回空结果")
                    if hasattr(self._parent, 'on_log'):
                        self._parent.on_log("⚠️ 配置结果为空", "warning")
            else:
                # 用户取消
                logger.info("❌ [Analysis Phase 3] 用户取消配置")
                if hasattr(self._parent, 'on_log'):
                    self._parent.on_log("ℹ️ [取消] 用户取消了模板配置", "info")

        except FileNotFoundError as e:
            logger.error(f"❌ [Analysis ERROR] 文件未找到: {e}")
            if hasattr(self._parent, 'on_log'):
                self._parent.on_log(f"❌ 错误：文件未找到 - {template_path}", "error")
            QMessageBox.critical(
                self._parent,
                "文件未找到",
                f"无法找到模板文件：\n{template_path}\n\n请检查文件路径是否正确。"
            )

        except Exception as e:
            logger.error(f"❌ [Analysis ERROR] 分析失败: {e}", exc_info=True)
            if hasattr(self._parent, 'on_log'):
                self._parent.on_log(f"❌ [错误] 分析过程异常: {str(e)}", "error")
                import traceback
                self._parent.on_log(traceback.format_exc(), "error")
            QMessageBox.critical(
                self._parent,
                "分析失败",
                f"模板分析过程中发生错误：\n\n{str(e)}\n\n请检查网络连接和 API 配置后重试。"
            )


# ============================================================================
# INTEGRATION EXAMPLE: How to use in gui_loader.py
# ============================================================================

"""
# Add this code to your gui_loader.py __init__ method:

from gui_launcher.template_analysis_integration import TemplateAnalysisIntegration

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # ... existing setup ...
        
        # Initialize template analysis integration
        self.template_integration = TemplateAnalysisIntegration(self)
        
        # Connect signals after obsidian_panel is created
        self.obsidian_panel.template_analysis_requested.connect(
            self.template_integration.on_analysis_requested
        )
        
        # Initialize analyzer when AI service is ready
        # (Call this when you have access to your AI client)
        self._setup_template_analyzer()
    
    def _setup_template_analyzer(self):
        \"\"\"Initialize template analyzer with AI function.\"\"\"
        # Get your AI generation function
        # This should be the same function used by AIClient.generate()
        async def ai_generate(system_prompt: str, user_prompt: str, **kwargs) -> str:
            from src.pdf_summarizer.ai_client import AIClient
            client = AIClient()
            response = await client.generate(
                system_prompt=system_prompt,
                prompt=user_prompt,
                **kwargs
            )
            return response.content
        
        # Initialize the integration
        self.template_integration.initialize_analyzer(ai_generate)


# Then, modify your 'start generation' handler to use analysis result:

async def _on_start_generation(self):
    # Get values from obsidian panel (now includes analysis result)
    template_path, course_name, vault_path, note_name, analysis_result = \
        self.obsidian_panel.get_values()
    
    # If we have an analysis result, pass it to the processing service
    if analysis_result:
        # Generate optimized prompts based on analysis
        system_prompt, user_prompt = self._generate_optimized_prompts(analysis_result)
        
        # Use optimized prompts instead of defaults
        # ... pass to processing_service ...

def _generate_optimized_prompts(self, analysis: TemplateAnalysisResult) -> tuple:
    \"\"\"Generate optimized prompts using template analysis.\"\"\"
    from src.pdf_summarizer.template_analyzer import TemplateAnalyzer
    
    analyzer = TemplateAnalyzer(cache_enabled=False)  # Don't need AI for this step
    
    # Load base prompts from config
    base_system = self._load_base_system_prompt()
    base_user = self._load_base_user_prompt()
    
    # Optimize based on analysis
    return analyzer.generate_optimized_prompts(
        analysis=analysis,
        base_system_prompt=base_system,
        base_user_prompt=base_user,
    )
"""


# ============================================================================
# ALTERNATIVE: No-Template Mode (Option C from design decisions)
# ============================================================================

async def infer_best_style_from_pdf(pdf_document, ai_generate_fn) -> dict:
    """Infer best template style from PDF content when no template is provided.
    
    This implements Option C: Let AI determine optimal style from PDF content.
    
    Args:
        pdf_document: Parsed PDF document object
        ai_generate_fn: AI generation function
        
    Returns:
        Dict with style recommendation and reasoning
    """
    full_text = pdf_document.get_full_text()
    
    system_prompt = (
        "你是一位教学设计专家。分析给定的课程内容，"
        "判断最适合的笔记风格类型。"
    )
    
    user_prompt = f"""请分析以下课程内容片段，推荐最适合的笔记模板风格：

## 课程内容预览
{full_text[:2000]}...

## 分析要求

返回 JSON 格式：
{{
    "recommended_style": "academic|exam_oriented|casual|mixed",
    "reasoning": "推荐理由（2-3句话）",
    "key_topics": ["主题1", "主题2", ...],
    "complexity": "basic|intermediate|advanced",
    "suggested_features": ["feature1", "feature2", ...]
}}

**判断依据**：
- 如果包含大量数学推导和定理证明 → academic
- 如果包含大量习题和例题 → exam_oriented
- 如果是概念介绍和直觉解释 → casual
- 如果以上混合 → mixed
"""

    try:
        response = await ai_generate_fn(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=500,
        )
        
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            return json.loads(json_match.group())
    
    except Exception as e:
        logger.warning(f"Style inference failed: {e}")
    
    # Fallback to default
    return {
        "recommended_style": "mixed",
        "reasoning": "无法自动判断，使用默认混合模式",
        "key_topics": [],
        "complexity": "intermediate",
        "suggested_features": [
            "yaml_front_matter",
            "core_summary",
            "concept_table",
            "chinese_exercise_title",
        ],
    }
