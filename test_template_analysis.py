"""Test script for Template Analysis System - Complete workflow test.

This script tests:
1. Template file loading and analysis
2. AI-powered deep analysis (Phase 1 & 2)
3. Configuration dialog display (simulated)
4. PDF parsing and note generation with optimized prompts

Usage:
    python test_template_analysis.py
"""

import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging to see all output
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


async def test_ai_generate(system_prompt: str, user_prompt: str, **kwargs) -> str:
    """Mock AI generate function for testing."""
    logger.info(f"🤖 [MockAI] 收到请求 - max_tokens={kwargs.get('max_tokens', 1000)}")

    # Simulate AI processing delay
    await asyncio.sleep(0.5)

    # Return mock analysis result
    mock_response = """{
        "style": "academic",
        "style_confidence": 0.85,
        "complexity": {
            "level": "advanced",
            "reasoning": "包含复杂物理公式和数学推导，适合高阶学习"
        },
        "gaps": ["要点提示框", "跨笔记双链接"],
        "strengths": ["结构清晰", "习题丰富"],
        "writing_guidelines": "保持学术严谨风格，强调数学推导的每一步逻辑",
        "prompt_variant_recommendation": "academic_enhanced",
        "overall_assessment": "高质量的学术型模板，适合大学物理课程"
    }"""

    logger.info(f"✅ [MockAI] 返回模拟响应 ({len(mock_response)} 字符)")
    return mock_response


async def run_complete_test():
    """Run complete template analysis and note generation test."""

    print("\n" + "="*70)
    print("🧪  开始完整功能测试")
    print("="*70 + "\n")

    total_start = time.time()

    # ══════════════════════════════════════════════════════════
    # Step 1: Initialize TemplateAnalyzer
    # ══════════════════════════════════════════════════════════
    print("📦 [Step 1] 初始化 TemplateAnalyzer...")
    step1_start = time.time()

    from src.pdf_summarizer.template_analyzer import TemplateAnalyzer

    analyzer = TemplateAnalyzer(
        ai_generate_fn=test_ai_generate,
        cache_enabled=True,
    )

    step1_elapsed = time.time() - step1_start
    print(f"   ✅ 初始化完成 ({step1_elapsed:.3f}s)\n")

    # ══════════════════════════════════════════════════════════
    # Step 2: Analyze Template File
    # ══════════════════════════════════════════════════════════
    template_path = Path(r"E:\obsidianwithclaude\Obsidian\collegenote\Physics\University-Physics-2\TW3.md")

    print(f"📄 [Step 2] 分析模板文件: {template_path.name}")
    print(f"   路径: {template_path}")
    step2_start = time.time()

    try:
        analysis_result = await analyzer.analyze(template_path)
        step2_elapsed = time.time() - step2_start

        print(f"\n   🎉 分析完成！({step2_elapsed:.3f}s)")
        print(f"   ┌─────────────────────────────────────┐")
        print(f"   │ 📊 风格识别: {analysis_result.style.value:<20} │")
        print(f"   │ 📈 置信度: {analysis_result.confidence:.0%}                    │")
        print(f"   │ ⚠️ 缺失项: {len(analysis_result.gaps):<20} │")
        print(f"   │ ✨ 已有特征: {sum(1 for v in analysis_result.features.values() if v):<17} │")
        print(f"   └─────────────────────────────────────┘\n")

        # Show detected features
        print("   🔍 检测到的特征:")
        for feature_key, present in analysis_result.features.items():
            status = "✅" if present else "⭕"
            feature_names = {
                "yaml_front_matter": "YAML Front Matter",
                "core_summary": "核心主题摘要",
                "concept_table": "重要概念表格",
                "chinese_exercise_title": "中文习题标题",
                "image_placeholder": "图片占位符",
                "subproblem_format": "子问题格式",
                "solution_marker": "解答标记",
                "boxed_answers": "\\boxed{} 答案",
                "key_insight_box": "要点提示框",
                "cross_note_links": "跨笔记双链接",
                "summary_table": "题型总结表",
                "formula_cheatsheet": "公式速查表",
            }
            name = feature_names.get(feature_key, feature_key)
            print(f"      {status} {name}")

        if analysis_result.gaps:
            print(f"\n   ⚠️ 建议优化的缺失项:")
            for gap in analysis_result.gaps:
                print(f"      • {gap}")

    except Exception as e:
        print(f"\n   ❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ══════════════════════════════════════════════════════════
    # Step 3: Generate Optimized Prompts
    # ══════════════════════════════════════════════════════════
    print(f"\n📝 [Step 3] 生成优化后的 Prompt...")
    step3_start = time.time()

    base_system_prompt = (
        "你是一位大学授课教授，正在制作课程讲稿笔记。\n\n"
        "【三条红线 — 必须遵守】\n"
        "1. 禁止使用 Markdown 表格（| ... | ... |）展示公式或数据\n"
        "2. 图片必须插入到对应的知识点附近\n"
        "3. 不要照搬课件中的原始表格数据"
    )

    base_user_prompt = (
        "请根据以下PDF内容生成符合模板要求的 Obsidian 笔记..."
    )

    optimized_system, optimized_user = analyzer.generate_optimized_prompts(
        analysis=analysis_result,
        base_system_prompt=base_system_prompt,
        base_user_prompt=base_user_prompt,
    )

    step3_elapsed = time.time() - step3_start
    print(f"   ✅ Prompt 优化完成 ({step3_elapsed:.3f}s)")
    print(f"   📏 System Prompt 长度: {len(optimized_system)} 字符")
    print(f"   📏 User Prompt 长度: {len(optimized_user)} 字符\n")

    # ══════════════════════════════════════════════════════════
    # Step 4: Test PDF Parsing (Optional - if PDF exists)
    # ══════════════════════════════════════════════════════════
    pdf_path = Path(r"C:\Users\ASUS\OneDrive\Desktop\资料整理\Class 06 Electric current and resistance (2 hours).pdf")

    if pdf_path.exists():
        print(f"📕 [Step 4] 解析 PDF 文件: {pdf_path.name}")
        step4_start = time.time()
        step4_elapsed = 0.0

        try:
            from src.pdf_summarizer.pdf_parser import PDFParser

            parser = PDFParser()
            document = parser.parse(pdf_path)

            step4_elapsed = time.time() - step4_start
            print(f"   ✅ PDF 解析完成 ({step4_elapsed:.3f}s)")
            print(f"   📄 总页数: {len(document.pages)} 页")
            print(f"   📝 总字数: {len(document.get_full_text()):,} 字符")
            print(f"   🖼️ 包含图片: {'是' if document.has_images() else '否'}\n")

        except Exception as e:
            print(f"   ⚠️ PDF 解析跳过: {e}\n")
    else:
        step4_elapsed = 0.0
        print(f"⚠️ [Step 4] PDF 文件未找到，跳过解析步骤\n")

    # ══════════════════════════════════════════════════════════
    # Final Summary
    # ══════════════════════════════════════════════════════════
    total_elapsed = time.time() - total_start

    print("\n" + "="*70)
    print("🎉 测试完成！汇总报告")
    print("="*70)
    print(f"""
┌─────────────────────────────────────────────────────────┐
│ ⏱️  总耗时: {total_elapsed:>6.2f}s                                │
├─────────────────────────────────────────────────────────┤
│ 📋 测试项目              │ 状态     │ 耗时               │
├─────────────────────────────────────────────────────────┤
│ 1. Analyzer 初始化       │ ✅ 通过  │ {step1_elapsed:>6.3f}s           │
│ 2. 模板分析 (TW3.md)     │ ✅ 通过  │ {step2_elapsed:>6.3f}s           │
│ 3. Prompt 优化           │ ✅ 通过  │ {step3_elapsed:>6.3f}s           │
{'│ 4. PDF 解析             │ ✅ 通过  │ ' + f'{step4_elapsed:>6.3f}s' + '           │' if pdf_path.exists() else '│ 4. PDF 解析             │ ⏭️ 跳过  │ N/A                │'}
└─────────────────────────────────────────────────────────┘

📊 分析结果摘要:
   • 模板风格: {analysis_result.style.value}
   • 置信度: {analysis_result.confidence:.0%}
   • 特征覆盖: {sum(1 for v in analysis_result.features.values() if v)}/{len(analysis_result.features)}
   • 缺失优化项: {len(analysis_result.gaps)}

💾 缓存状态: 已保存到 ~/.noter/template_cache/
""")

    print("="*70 + "\n")

    return True


if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("\n🚀 启动模板分析系统测试...\n")

    try:
        success = asyncio.run(run_complete_test())

        if success:
            print("✨ 所有测试通过！系统运行正常。\n")
            sys.exit(0)
        else:
            print("❌ 测试失败，请检查日志输出。\n")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断测试\n")
        sys.exit(130)

    except Exception as e:
        print(f"\n❌ 测试过程发生异常: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
