"""Template Analyzer - AI-powered template analysis and configuration generation.

This module provides intelligent analysis of Obsidian note templates,
including structure detection, style identification, gap detection,
and personalized prompt optimization.

Features:
- 6-dimensional template analysis (A-F)
- Rule-based fast scan + AI deep analysis
- Hash-based caching to avoid redundant API calls
- Configurable suggestions with user customization support
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TemplateStyle(Enum):
    """Detected template style categories."""
    ACADEMIC = "academic"           # 学术严谨型
    EXAM_ORIENTED = "exam_oriented" # 备考导向型
    CASUAL = "casual"               # 轻松学习型
    MIXED = "mixed"                 # 混合型
    UNKNOWN = "unknown"             # 无法确定


@dataclass
class TemplateAnalysisResult:
    """Complete template analysis result.
    
    Attributes:
        template_path: Path to the analyzed template file
        template_hash: SHA256 hash of template content for caching
        style: Detected style category
        structure: Structural information (headings, sections, etc.)
        features: Detected special features (boxed, links, etc.)
        gaps: Missing elements compared to v2.0 standard
        complexity: Complexity assessment
        ai_suggestions: AI-generated writing guidelines
        prompt_variant: Recommended prompt variant name
        confidence: Analysis confidence score (0.0-1.0)
        analyzed_at: Timestamp of analysis
        user_modifications: User's custom modifications to suggestions
    """
    template_path: Path
    template_hash: str
    style: TemplateStyle
    structure: Dict[str, Any] = field(default_factory=dict)
    features: Dict[str, bool] = field(default_factory=dict)
    gaps: List[str] = field(default_factory=list)
    complexity: Dict[str, Any] = field(default_factory=dict)
    ai_suggestions: str = ""
    prompt_variant: str = "default"
    confidence: float = 0.0
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    user_modifications: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "template_path": str(self.template_path),
            "template_hash": self.template_hash,
            "style": self.style.value,
            "structure": self.structure,
            "features": self.features,
            "gaps": self.gaps,
            "complexity": self.complexity,
            "ai_suggestions": self.ai_suggestions,
            "prompt_variant": self.prompt_variant,
            "confidence": self.confidence,
            "analyzed_at": self.analyzed_at,
            "user_modifications": self.user_modifications,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateAnalysisResult':
        """Create instance from dictionary (for cache loading)."""
        return cls(
            template_path=Path(data["template_path"]),
            template_hash=data["template_hash"],
            style=TemplateStyle(data["style"]),
            structure=data.get("structure", {}),
            features=data.get("features", {}),
            gaps=data.get("gaps", []),
            complexity=data.get("complexity", {}),
            ai_suggestions=data.get("ai_suggestions", ""),
            prompt_variant=data.get("prompt_variant", "default"),
            confidence=data.get("confidence", 0.0),
            analyzed_at=data.get("analyzed_at", datetime.now().isoformat()),
            user_modifications=data.get("user_modifications", {}),
        )


class TemplateAnalyzer:
    """Intelligent template analyzer with rule-based scanning and AI deep analysis.
    
    This class implements a two-phase analysis approach:
    Phase 1: Fast rule-based scan (<100ms) for basic structure extraction
    Phase 2: AI-powered deep analysis for style detection and gap analysis
    
    Usage:
        analyzer = TemplateAnalyzer(ai_generate_fn=your_ai_function)
        
        # Analyze a template (uses cache if available)
        result = analyzer.analyze(template_path)
        
        # Get optimized prompts based on analysis
        system_prompt, user_prompt = analyzer.generate_prompts(result)
    """
    
    CACHE_DIR = Path.home() / ".noter" / "template_cache"
    
    # Standard v2.0 feature checklist for gap detection
    V2_STANDARD_FEATURES = [
        ("yaml_front_matter", "YAML Front Matter (tags, created, week, source)"),
        ("core_summary", "核心主题摘要 (blockquote after H1)"),
        ("concept_table", "重要概念总览表格 (5-8 concepts)"),
        ("chinese_exercise_title", "中文习题标题 (习题 X —— 名称)"),
        ("image_placeholder", "图片占位符 (![[...]])"),
        ("subproblem_format", "子问题格式 (### a. b. c.)"),
        ("solution_marker", "解答标记 (**解：**)"),
        ("boxed_answers", "最终答案 boxed 包装"),
        ("key_insight_box", "要点提示框 (> **要点**)"),
        ("cross_note_links", "跨笔记双链接 ([[TWn#...]], ≥5个)"),
        ("summary_table", "题型总结与要点表格"),
        ("formula_cheatsheet", "核心公式速查表格"),
    ]
    
    def __init__(self, ai_generate_fn=None, cache_enabled: bool = True):
        """Initialize the template analyzer.
        
        Args:
            ai_generate_fn: Async function for AI API calls (signature: async fn(system_prompt, user_prompt) -> str)
            cache_enabled: Whether to use caching (default: True)
        """
        self._ai_generate = ai_generate_fn
        self._cache_enabled = cache_enabled
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of template content for caching."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def get_cache_path(self, template_hash: str) -> Path:
        """Get cache file path for a given template hash."""
        return self.CACHE_DIR / f"{template_hash}.analysis.json"
    
    def load_from_cache(self, template_hash: str) -> Optional[TemplateAnalysisResult]:
        """Load analysis result from cache if exists and is valid."""
        if not self._cache_enabled:
            return None
            
        cache_path = self.get_cache_path(template_hash)
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            result = TemplateAnalysisResult.from_dict(data)
            logger.info(f"Loaded cached analysis for hash {template_hash[:12]}...")
            return result
            
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None
    
    def save_to_cache(self, result: TemplateAnalysisResult):
        """Save analysis result to cache."""
        if not self._cache_enabled:
            return
            
        cache_path = self.get_cache_path(result.template_hash)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Saved analysis to cache: {cache_path.name}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def _rule_based_scan(self, content: str) -> Dict[str, Any]:
        """Phase 1: Fast rule-based structural analysis (<100ms).
        
        Extracts:
        - Heading hierarchy and depth
        - Section/Exercise counts
        - Special markers detection (\boxed{}, > blocks, [[]] links, etc.)
        - Basic statistics (line count, word count, etc.)
        """
        lines = content.split('\n')
        
        structure = {
            "heading_count": 0,
            "max_heading_level": 0,
            "sections": [],
            "exercise_count": 0,
            "has_yaml": False,
            "has_tables": False,
            "has_images": False,
            "line_count": len(lines),
            "word_count": len(content.split()),
        }
        
        features = {
            "yaml_front_matter": False,
            "core_summary": False,
            "concept_table": False,
            "chinese_exercise_title": False,
            "image_placeholder": False,
            "subproblem_format": False,
            "solution_marker": False,
            "boxed_answers": False,
            "key_insight_box": False,
            "cross_note_links": False,
            "summary_table": False,
            "formula_cheatsheet": False,
        }
        
        current_section = None
        in_yaml = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Detect YAML front matter
            if stripped == "---":
                if not structure["has_yaml"] and i == 0:
                    in_yaml = True
                    structure["has_yaml"] = True
                    features["yaml_front_matter"] = True
                elif in_yaml:
                    in_yaml = False
                continue
            
            if in_yaml:
                continue
            
            # Detect headings
            if stripped.startswith("#"):
                level = len(stripped) - len(stripped.lstrip('#'))
                structure["heading_count"] += 1
                structure["max_heading_level"] = max(structure["max_heading_level"], level)
                
                title = stripped.lstrip('#').strip()
                
                # Detect section type
                if any(kw in title.lower() for kw in ["习题", "exercise", "练习", "问题"]):
                    structure["exercise_count"] += 1
                    if "——" in title or "--" in title or "：" in title:
                        features["chinese_exercise_title"] = True
                
                if any(kw in title.lower() for kw in ["重要概念", "概念总览", "concept"]):
                    features["concept_table"] = True
                    
                if any(kw in title.lower() for kw in ["总结", "summary", "题型", "速查"]):
                    if "公式" in title or "cheat" in title.lower():
                        features["formula_cheatsheet"] = True
                    else:
                        features["summary_table"] = True
                
                current_section = {"level": level, "title": title, "line": i}
                structure["sections"].append(current_section)
            
            # Detect tables
            if "|" in stripped and "|--" in stripped:
                structure["has_tables"] = True
            
            # Detect images
            if "![[{" in stripped or "! [[" in stripped:
                structure["has_images"] = True
                features["image_placeholder"] = True
            
            # Detect subproblem format
            if re.match(r'^###\s*[a-zA-Z]\.', stripped):
                features["subproblem_format"] = True
            
            # Detect solution marker
            if "**解**" in stripped or "**解：**" in stripped:
                features["solution_marker"] = True
            
            # Detect \boxed{}
            if "\\boxed{" in stripped:
                features["boxed_answers"] = True
            
            # Detect key insight box
            if stripped.startswith(">") and ("**要点**" in stripped or "**关键**" in stripped):
                features["key_insight_box"] = True
            
            # Detect cross-note links
            if "[[TW" in stripped:
                features["cross_note_links"] = True
            
            # Detect core summary blockquote
            if stripped.startswith(">") and ("**核心主题**" in stripped or "**核心**" in stripped):
                features["core_summary"] = True
        
        return {
            "structure": structure,
            "features": features,
        }
    
    async def _ai_deep_analysis(
        self, 
        content: str, 
        rule_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Phase 2: AI-powered deep analysis for style and gaps.
        
        This method calls the AI to:
        1. Identify template style (academic/exam/casual/mixed)
        2. Assess complexity level
        3. Generate personalized writing guidelines
        4. Recommend optimal prompt variant
        """
        if not self._ai_generate:
            logger.warning("No AI function provided, skipping deep analysis")
            return {}
        
        # Build analysis prompt
        structure_info = json.dumps(rule_result["structure"], ensure_ascii=False, indent=2)
        features_info = json.dumps(rule_result["features"], ensure_ascii=False, indent=2)
        
        system_prompt = (
            "你是一位专业的文档模板分析师和教学设计专家。"
            "你的任务是深入分析给定的 Obsidian 笔记模板，"
            "识别其风格特征、复杂度，并生成个性化的写作优化建议。"
        )
        
        user_prompt = f"""请分析以下 Obsidian 笔记模板，并提供详细的评估报告。

## 模板内容
```markdown
{content[:3000]}  # 截取前3000字符避免token过多
```
{f"... (共 {rule_result['structure']['word_count']} 字)" if rule_result['structure']['word_count'] > 3000 else ""}

## 规则引擎初步扫描结果

### 结构信息
```json
{structure_info}
```

### 特征检测
```json
{features_info}
```

## 分析要求

请以 JSON 格式返回以下信息（不要添加其他文字）：
{{
    "style": "academic|exam_oriented|casual|mixed|unknown",
    "style_confidence": 0.0-1.0,
    "complexity": {{
        "level": "basic|intermediate|advanced",
        "reasoning": "判断依据（1-2句话）"
    }},
    "gaps": ["缺失项1", "缺失项2", ...],
    "strengths": ["优点1", "优点2", ...],
    "writing_guidelines": "针对此模板的个性化写作指导（3-5条具体建议）",
    "prompt_variant_recommendation": "default|academic_enhanced|exam_focused|concise",
    "overall_assessment": "整体评价（2-3句话）"
}}

## 判断标准

**风格分类**：
- academic: 强调推导严谨性、数学形式化、理论深度
- exam_oriented: 注重考点归纳、题型总结、应试技巧
- casual: 口语化表达、直觉理解、类比丰富
- mixed: 以上特征的混合

**复杂度等级**：
- basic: 简单结构（<3层标题，<5节），适合入门内容
- intermediate: 中等结构（3-4层标题，5-10节），标准课程笔记
- advanced: 复杂结构（>4层标题，>10节），高阶或综合性内容

**gap检测标准**（对比 v2.0 Obsidian 优化标准）：
- YAML Front Matter（元数据管理）
- 核心主题摘要（快速理解）
- 重要概念表格（知识框架）
- 中文习题标题（规范化）
- 图片引用（可视化）
- 子问题格式（结构化）
- 解答标记（清晰度）
- \\boxed{{}}答案（突出重点）
- 要点提示框（教学价值）
- 跨笔记链接（知识网络）
- 题型总结表（复习效率）
- 公式速查表（快速查阅）
"""

        try:
            response = await self._ai_generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                use_cache=True,
                max_tokens=2000,
            )
            
            # Parse JSON response
            if response:
                # Extract JSON from response (handle potential markdown code blocks)
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    return json.loads(json_match.group())
                    
        except Exception as e:
            logger.error(f"AI deep analysis failed: {e}")
        
        return {}
    
    async def analyze(
        self,
        template_path: Path,
        force_refresh: bool = False
    ) -> TemplateAnalysisResult:
        """Analyze a template file using two-phase approach.

        Args:
            template_path: Path to the .md template file
            force_refresh: Force re-analysis even if cached result exists

        Returns:
            TemplateAnalysisResult with complete analysis data
        """
        import time

        total_start = time.time()

        # Read template content
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        logger.info(f"📂 [TemplateAnalyzer] 开始分析文件: {template_path.name}")

        content = template_path.read_text(encoding='utf-8')
        template_hash = self.compute_hash(content)

        logger.info(f"   📊 文件大小: {len(content):,} 字符 | Hash: {template_hash[:16]}...")

        # Check cache first (unless force refresh)
        if not force_refresh:
            logger.info(f"🔍 [TemplateAnalyzer] 检查缓存...")
            cached = self.load_from_cache(template_hash)
            if cached:
                elapsed = time.time() - total_start
                logger.info(f"✅ [TemplateAnalyzer] 缓存命中！使用已有结果 ({elapsed:.3f}s)")
                return cached

            logger.info(f"⏭️  [TemplateAnalyzer] 缓存未命中，开始完整分析...")

        # Phase 1: Rule-based fast scan
        phase1_start = time.time()
        logger.info(f"⏳ [TemplateAnalyzer Phase 1] 启动规则引擎扫描...")
        rule_result = self._rule_based_scan(content)
        phase1_elapsed = time.time() - phase1_start

        detected_features = sum(1 for v in rule_result["features"].values() if v)
        logger.info(
            f"✅ [TemplateAnalyzer Phase 1] 规则扫描完成 ({phase1_elapsed:.3f}s)\n"
            f"   📐 标题层级: {rule_result['structure'].get('max_heading_level', 0)} 层\n"
            f"   📑 章节数量: {len(rule_result['structure'].get('sections', []))} 节\n"
            f"   ✏️ 习题数量: {rule_result['structure'].get('exercise_count', 0)} 道\n"
            f"   ✨ 特征检测: {detected_features}/{len(rule_result['features'])} 项"
        )
        
        # Initialize result with rule-based findings
        result = TemplateAnalysisResult(
            template_path=template_path,
            template_hash=template_hash,
            style=TemplateStyle.UNKNOWN,
            structure=rule_result["structure"],
            features=rule_result["features"],
            confidence=0.3,  # Low confidence from rules only
        )
        
        # Detect gaps based on v2.0 standard
        for feature_key, feature_name in self.V2_STANDARD_FEATURES:
            if not result.features.get(feature_key, False):
                result.gaps.append(feature_name)

        logger.info(f"⚠️  [TemplateAnalyzer] 检测到 {len(result.gaps)} 个缺失项（v2.0 标准）")

        # Phase 2: AI deep analysis (if AI function available)
        if self._ai_generate:
            phase2_start = time.time()
            logger.info(f"⏳ [TemplateAnalyzer Phase 2] 启动 AI 深度分析...")
            ai_result = await self._ai_deep_analysis(content, rule_result)
            phase2_elapsed = time.time() - phase2_start

            if ai_result:
                # Update result with AI findings
                result.style = TemplateStyle(ai_result.get("style", "unknown"))
                result.confidence = ai_result.get("style_confidence", 0.7)
                result.complexity = ai_result.get("complexity", {})
                result.ai_suggestions = ai_result.get("writing_guidelines", "")
                result.prompt_variant = ai_result.get("prompt_variant_recommendation", "default")

                # Merge AI-detected gaps with rule-based gaps
                ai_gaps = ai_result.get("gaps", [])
                for gap in ai_gaps:
                    if gap not in result.gaps:
                        result.gaps.append(gap)

                logger.info(
                    f"✅ [TemplateAnalyzer Phase 2] AI 分析完成 ({phase2_elapsed:.3f}s)\n"
                    f"   🎯 风格识别: {result.style.value}\n"
                    f"   📈 置信度: {result.confidence:.2%}\n"
                    f"   📐 复杂度: {result.complexity.get('level', 'N/A')}\n"
                    f"   💡 推荐变体: {result.prompt_variant}"
                )
            else:
                logger.warning(f"⚠️  [TemplateAnalyzer Phase 2] AI 返回空结果，使用规则引擎结果")
        else:
            logger.info(f"ℹ️  [TemplateAnalyzer] 未配置 AI 函数，跳过 Phase 2")

        # Save to cache
        cache_start = time.time()
        self.save_to_cache(result)
        cache_elapsed = time.time() - cache_start

        total_elapsed = time.time() - total_start
        logger.info(
            f"\n{'═'*60}\n"
            f"🎉 [TemplateAnalyzer] 全部分析完成！\n"
            f"   ⏱️ 总耗时: {total_elapsed:.3f}s (Phase1: {phase1_elapsed:.3f}s + Phase2: {(phase2_elapsed if self._ai_generate else 0):.3f}s + Cache: {cache_elapsed:.3f}s)\n"
            f"   📊 最终结果:\n"
            f"      - 风格: {result.style.value}\n"
            f"      - 置信度: {result.confidence:.2%}\n"
            f"      - 缺失项: {len(result.gaps)} 个\n"
            f"      - 已缓存: ✅\n"
            f"{'═'*60}"
        )
        
        logger.info(
            f"Analysis complete: style={result.style.value}, "
            f"confidence={result.confidence:.2f}, gaps={len(result.gaps)}"
        )
        
        return result
    
    def generate_optimized_prompts(
        self, 
        analysis: TemplateAnalysisResult,
        base_system_prompt: str,
        base_user_prompt: str
    ) -> Tuple[str, str]:
        """Generate optimized prompts based on template analysis.
        
        Combines:
        - Base prompts from config (v2.0 standard)
        - Prompt variant selection (A: preset variants)
        - AI-generated writing guidelines (B: personalized tweaks)
        - User modifications (custom overrides)
        
        Args:
            analysis: Completed template analysis result
            base_system_prompt: Original system prompt from config
            base_user_prompt: Original user prompt from config
            
        Returns:
            Tuple of (optimized_system_prompt, optimized_user_prompt)
        """
        # Part A: Select prompt variant based on style
        variant_additions = self._get_prompt_variant(analysis.prompt_variant)
        
        # Part B: Add AI-generated guidelines
        guideline_section = ""
        if analysis.ai_suggestions:
            guideline_section = f"""
【基于模板「{analysis.template_path.stem}」的个性化写作指导】

{analysis.ai_suggestions}

请严格遵循以上指导原则，同时符合下方的通用格式要求。
"""
        
        # Apply user modifications (if any)
        user_overrides = analysis.user_modifications
        if user_overrides:
            guideline_section = self._apply_user_modifications(guideline_section, user_overrides)
        
        # Combine all parts
        optimized_system = base_system_prompt
        optimized_user = variant_additions + guideline_section + base_user_prompt
        
        return optimized_system, optimized_user
    
    def _get_prompt_variant(self, variant_name: str) -> str:
        """Get additional prompt text for a specific variant.
        
        Args:
            variant_name: Variant identifier (default/academic_enhanced/exam_focused/concise)
            
        Returns:
            Additional prompt text to prepend to base prompt
        """
        variants = {
            "default": "",
            "academic_enhanced": """
【学术增强模式已启用】

额外的学术规范要求：
- 所有物理量首次出现时必须给出严格的数学定义
- 推导过程必须包含"由...可得"、"这意味着"等逻辑连接词
- 关键定理/定律必须标注来源或命名者（如：**高斯定律（Gauss's Law）**）
- 使用"注"、"证明"、"推论"等学术标记
- 公式后必须附上物理意义阐释（1-2句）

""",
            "exam_focused": """
【备考聚焦模式已启用】

额外的备考优化要求：
- 每个知识点必须标注"考查频率"（高频/中频/低频）
- 习题必须归类到"题型"（计算题/证明题/概念题/综合题）
- 常见错误模式用 ⚠️ 标记
- 关键结论用 ✅ 必背 标记
- 提供记忆口诀或联想技巧（如适用）

""",
            "concise": """
【精简模式已启用】

精简化要求：
- 删除冗余的过渡语句，直接进入核心内容
- 概念定义不超过2句话
- 只保留最关键的推导步骤（省略显然的代数运算）
- 要点提示框合并为每节1个（而非每题1个）

""",
        }
        
        return variants.get(variant_name, "")
    
    def _apply_user_modifications(
        self, 
        base_text: str, 
        modifications: Dict[str, Any]
    ) -> str:
        """Apply user custom modifications to generated guidelines.
        
        Supports:
        - Adding new rules
        - Removing/disabling existing rules
        - Modifying rule text
        - Reordering priority
        
        Args:
            base_text: Original guideline text
            modifications: User modification dict
            
        Returns:
            Modified guideline text
        """
        modified_text = base_text
        
        # Handle additions
        additions = modifications.get("additions", [])
        if additions:
            modified_text += "\n\n【用户自定义补充】\n"
            for addition in additions:
                modified_text += f"- {addition}\n"
        
        # Handle removals (comment out rather than delete for traceability)
        removals = modifications.get("removals", [])
        for item in removals:
            modified_text = modified_text.replace(item, f"<!-- 用户禁用: {item} -->")
        
        # Handle replacements
        replacements = modifications.get("replacements", {})
        for old, new in replacements.items():
            modified_text = modified_text.replace(old, new)
        
        return modified_text


# Import regex here to avoid circular dependency at module level
import re
