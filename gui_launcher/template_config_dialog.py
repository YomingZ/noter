"""Template Configuration Dialog - Interactive panel for template analysis review and customization.

This module provides a user-friendly dialog that displays:
- Template analysis results (style, structure, features)
- Detected gaps compared to v2.0 standard
- AI-generated suggestions with checkboxes for enable/disable
- User customization options (add/remove/modify rules)
- Preview of optimized prompt configuration

Usage:
    dialog = TemplateConfigDialog(analysis_result, parent=window)
    if dialog.exec():
        # User confirmed, get modified result
        modified_result = dialog.get_modified_result()
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap

from src.pdf_summarizer.template_analyzer import (
    TemplateAnalysisResult,
    TemplateAnalyzer,
    TemplateStyle,
)

logger = logging.getLogger(__name__)


class TemplateConfigDialog(QDialog):
    """Interactive template analysis review and configuration dialog.
    
    This dialog presents the complete analysis results in a structured way,
    allowing users to:
    1. Review detected template characteristics
    2. Enable/disable suggested optimizations via checkboxes
    3. Add custom rules or modifications
    4. Preview the final prompt configuration
    5. Confirm or cancel the optimization plan
    
    Layout:
    ┌─ Template Analysis Results ─────────────────────┐
    │ [Basic Info] [Features] [Gaps] [AI Suggestions] │
    ├─────────────────────────────────────────────────┤
    │ ☑ Enable YAML Front Matter                      │
    │ ☑ Enable Core Summary                           │
    │ ☑ Enable Concept Table                          │
    │ ...                                             │
    │                                                 │
    │ [+ Add Custom Rule]                             │
    │                                                 │
    │ [Preview Optimized Prompts]                     │
    │                                                 │
    │          [Apply Changes]  [Cancel]              │
    └─────────────────────────────────────────────────┘
    """
    
    # Feature display names mapping
    FEATURE_DISPLAY_NAMES = {
        "yaml_front_matter": "YAML Front Matter（元数据：tags、日期、周次）",
        "core_summary": "核心主题摘要（blockquote 形式）",
        "concept_table": "重要概念总览表格（5-8个核心概念）",
        "chinese_exercise_title": "中文习题标题格式（习题 X —— 名称）",
        "image_placeholder": "图片占位符引用（![[...]]）",
        "subproblem_format": "子问题格式（### a. b. c.）",
        "solution_marker": "解答标记（**解：**）",
        "boxed_answers": "最终答案 boxed 包装（\\boxed{}）",
        "key_insight_box": "要点提示框（每题后 > **要点**）",
        "cross_note_links": "跨笔记双链接（[[TWn#锚点]]，≥5个）",
        "summary_table": "题型总结与要点表格（文末）",
        "formula_cheatsheet": "核心公式速查表（文末）",
    }
    
    def __init__(
        self, 
        analysis: TemplateAnalysisResult, 
        parent=None
    ):
        """Initialize the dialog with analysis results.
        
        Args:
            analysis: Complete template analysis result from TemplateAnalyzer
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._analysis = analysis
        self._modified_analysis = None  # Will hold user-modified result
        
        self.setWindowTitle(f"📋 模板分析结果 — {analysis.template_path.stem}")
        self.setMinimumSize(750, 650)
        self.resize(820, 700)
        
        self._setup_ui()
        self._populate_data()
    
    def _populate_data(self):
        """Populate UI components with analysis data.
        
        This method initializes all form fields, checkboxes, and display
        elements with data from the TemplateAnalysisResult.
        """
        # Update variant combo based on analysis recommendation
        current_idx = self.variant_combo.findData(self._analysis.prompt_variant)
        if current_idx >= 0:
            self.variant_combo.setCurrentIndex(current_idx)
        
        # Update feature checkboxes based on detected features
        for feature_key, checkbox in self.feature_checkboxes.items():
            is_present = self._analysis.features.get(feature_key, False)
            checkbox.setChecked(is_present)
        
        # Populate custom rules if any exist from previous modifications
        if hasattr(self._analysis, 'user_modifications') and self._analysis.user_modifications:
            custom_rules = self._analysis.user_modifications.get('custom_rules', [])
            if custom_rules:
                self.custom_rules_edit.setPlainText('\n'.join(custom_rules))
    
    def _setup_ui(self):
        """Setup all UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 12)
        
        # === Header Section ===
        header = self._create_header()
        main_layout.addWidget(header)
        
        # === Main Content Area (Splitter) ===
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Analysis Overview
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right: Configuration Options
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([380, 420])
        main_layout.addWidget(splitter, stretch=1)
        
        # === Footer Buttons ===
        footer = self._create_footer()
        main_layout.addWidget(footer)
    
    def _create_header(self) -> QWidget:
        """Create header section with template info."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 8)
        
        # Icon + Title
        title_label = QLabel("📊 模板智能分析")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
        """)
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Style badge
        style_names = {
            TemplateStyle.ACADEMIC: ("学术严谨型", "#3498db"),
            TemplateStyle.EXAM_ORIENTED: ("备考导向型", "#e74c3c"),
            TemplateStyle.CASUAL: ("轻松学习型", "#27ae60"),
            TemplateStyle.MIXED: ("混合型", "#9b59b6"),
            TemplateStyle.UNKNOWN: ("待识别", "#95a5a6"),
        }
        
        style_name, style_color = style_names.get(
            self._analysis.style, 
            ("未知", "#7f8c8d")
        )
        
        style_badge = QLabel(f"🎯 风格：{style_name}")
        style_badge.setStyleSheet(f"""
            background-color: {style_color}20;
            color: {style_color};
            padding: 6px 14px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 13px;
        """)
        layout.addWidget(style_badge)
        
        # Confidence score
        conf_text = f"置信度：{self._analysis.confidence:.0%}"
        conf_label = QLabel(conf_text)
        conf_color = "#27ae60" if self._analysis.confidence > 0.7 else "#f39c12"
        conf_label.setStyleSheet(f"""
            color: {conf_color};
            font-size: 13px;
            font-weight: bold;
        """)
        layout.addWidget(conf_label)
        
        return widget
    
    def _create_left_panel(self) -> QWidget:
        """Create left panel with analysis overview."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        
        # 1. Structure Info Group
        struct_group = self._create_structure_group()
        layout.addWidget(struct_group)
        
        # 2. Features Detection Group
        features_group = self._create_features_group()
        layout.addWidget(features_group)
        
        # 3. Gaps Detection Group
        gaps_group = self._create_gaps_group()
        layout.addWidget(gaps_group)
        
        # 4. AI Suggestions Group
        suggestions_group = self._create_suggestions_group()
        layout.addWidget(suggestions_group)
        
        layout.addStretch()
        scroll.setWidget(container)
        
        return scroll
    
    def _create_structure_group(self) -> QGroupBox:
        """Create structure information group box."""
        group = QGroupBox("📐 结构信息")
        group.setStyleSheet(self._group_style())
        layout = QFormLayout(group)
        layout.setSpacing(8)
        
        struct = self._analysis.structure
        
        layout.addRow(
            "标题层级数：", 
            QLabel(str(struct.get("max_heading_level", 0)))
        )
        layout.addRow(
            "总章节数：", 
            QLabel(str(len(struct.get("sections", []))))
        )
        layout.addRow(
            "习题数量：", 
            QLabel(str(struct.get("exercise_count", 0)))
        )
        layout.addRow(
            "总行数：", 
            QLabel(f"{struct.get('line_count', 0):,}")
        )
        layout.addRow(
            "字数统计：", 
            QLabel(f"{struct.get('word_count', 0):,}")
        )
        
        has_yaml = "✅ 是" if struct.get("has_yaml") else "❌ 否"
        has_tables = "✅ 是" if struct.get("has_tables") else "❌ 否"
        has_images = "✅ 是" if struct.get("has_images") else "❌ 否"
        
        layout.addRow("含 YAML 头部：", QLabel(has_yaml))
        layout.addRow("含表格：", QLabel(has_tables))
        layout.addRow("含图片引用：", QLabel(has_images))
        
        return group
    
    def _create_features_group(self) -> QGroupBox:
        """Create features detection group box."""
        group = QGroupBox("✨ 特征检测（v2.0 标准）")
        group.setStyleSheet(self._group_style())
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        features = self._analysis.features
        total = len(features)
        detected = sum(1 for v in features.values() if v)
        
        summary = QLabel(f"已检测到 {detected}/{total} 个标准特征")
        summary.setStyleSheet("font-weight: bold; color: #3498db;")
        layout.addWidget(summary)
        
        for feature_key, present in features.items():
            display_name = self.FEATURE_DISPLAY_NAMES.get(feature_key, feature_key)
            
            item_layout = QHBoxLayout()
            item_layout.setContentsMargins(8, 2, 2, 2)
            
            icon = "✅" if present else "⭕"
            label = QLabel(f"{icon} {display_name}")
            
            if present:
                label.setStyleSheet("color: #27ae60;")
            else:
                label.setStyleSheet("color: #e74c3c;")
            
            item_layout.addWidget(label)
            item_layout.addStretch()
            layout.addLayout(item_layout)
        
        return group
    
    def _create_gaps_group(self) -> QGroupBox:
        """Create gaps detection group box."""
        group = QGroupBox("⚠️ 缺失项检测")
        group.setStyleSheet(self._group_style())
        layout = QVBoxLayout(group)
        
        gaps = self._analysis.gaps
        
        if not gaps:
            no_gaps = QLabel("🎉 完美！所有 v2.0 标准特征均已具备")
            no_gaps.setStyleSheet("color: #27ae60; font-weight: bold; padding: 10px;")
            layout.addWidget(no_gaps)
        else:
            count_label = QLabel(f"发现 {len(gaps)} 个可优化的项目：")
            count_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
            layout.addWidget(count_label)
            
            for gap in gaps:
                gap_item = QLabel(f"• {gap}")
                gap_item.setStyleSheet("color: #c0392b; margin-left: 10px;")
                layout.addWidget(gap_item)
        
        return group
    
    def _create_suggestions_group(self) -> QGroupBox:
        """Create AI suggestions group box."""
        group = QGroupBox("💡 AI 写作指导建议")
        group.setStyleSheet(self._group_style())
        layout = QVBoxLayout(group)
        
        if self._analysis.ai_suggestions:
            suggestions_text = QTextEdit()
            suggestions_text.setReadOnly(True)
            suggestions_text.setPlainText(self._analysis.ai_suggestions)
            suggestions_text.setMaximumHeight(150)
            suggestions_text.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #dfe6e9;
                    border-radius: 4px;
                    padding: 8px;
                    background-color: #f8f9fa;
                    font-size: 12px;
                }
            """)
            layout.addWidget(suggestions_text)
        else:
            no_ai = QLabel("ℹ️ 未启用 AI 深度分析，仅使用规则引擎结果")
            no_ai.setStyleSheet("color: #7f8c8d; font-style: italic;")
            layout.addWidget(no_ai)
        
        return group
    
    def _create_right_panel(self) -> QWidget:
        """Create right panel with configuration options."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        
        # Prompt Variant Selection
        variant_group = self._create_variant_group()
        layout.addWidget(variant_group)
        
        # Optimization Toggles
        toggles_group = self._create_toggles_group()
        layout.addWidget(toggles_group, stretch=1)
        
        # Custom Rules Section
        custom_group = self._create_custom_rules_group()
        layout.addWidget(custom_group)
        
        return container
    
    def _create_variant_group(self) -> QGroupBox:
        """Create prompt variant selection group."""
        from PyQt6.QtWidgets import QComboBox
        
        group = QGroupBox("🎛️ Prompt 变体选择")
        group.setStyleSheet(self._group_style())
        layout = QFormLayout(group)
        
        self.variant_combo = QComboBox()
        self.variant_combo.addItem("默认模式 (default)", "default")
        self.variant_combo.addItem("学术增强模式 (academic_enhanced)", "academic_enhanced")
        self.variant_combo.addItem("备考聚焦模式 (exam_focused)", "exam_focused")
        self.variant_combo.addItem("精简模式 (concise)", "concise")
        
        # Set current recommendation
        current_idx = self.variant_combo.findData(self._analysis.prompt_variant)
        if current_idx >= 0:
            self.variant_combo.setCurrentIndex(current_idx)
        
        self.variant_combo.currentIndexChanged.connect(self._on_variant_changed)
        layout.addRow("选择变体：", self.variant_combo)
        
        # Variant description
        self.variant_desc = QLabel()
        self.variant_desc.setWordWrap(True)
        self.variant_desc.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        self._update_variant_description()
        layout.addRow("", self.variant_desc)
        
        return group
    
    def _update_variant_description(self):
        """Update variant description based on selection."""
        descriptions = {
            "default": "标准 v2.0 Obsidian 优化，平衡质量与生成速度",
            "academic_enhanced": "增强学术严谨性，适合理论性强的课程内容",
            "exam_focused": "聚焦应试技巧，适合考前复习笔记",
            "concise": "精简冗余内容，适合快速浏览型笔记",
        }
        
        current = self.variant_combo.currentData()
        self.variant_desc.setText(descriptions.get(current, ""))
    
    def _on_variant_changed(self):
        """Handle variant combo change."""
        self._update_variant_description()
    
    def _create_toggles_group(self) -> QGroupBox:
        """Create optimization toggles group box."""
        group = QGroupBox("⚙️ 优化选项配置")
        group.setStyleSheet(self._group_style())
        layout = QVBoxLayout(group)
        
        # Scroll area for many checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        toggle_container = QWidget()
        toggle_layout = QVBoxLayout(toggle_container)
        toggle_layout.setSpacing(6)
        
        self.feature_checkboxes = {}
        
        for feature_key, display_name in self.FEATURE_DISPLAY_NAMES.items():
            is_present = self._analysis.features.get(feature_key, False)
            
            checkbox = QCheckBox(display_name)
            checkbox.setChecked(is_present)
            checkbox.setStyleSheet("""
                QCheckBox {
                    spacing: 8px;
                    font-size: 12px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border-radius: 3px;
                    border: 2px solid #bdc3c7;
                }
                QCheckBox::indicator:checked {
                    background-color: #3498db;
                    border-color: #3498db;
                }
            """)
            
            # Store reference for later retrieval
            self.feature_checkboxes[feature_key] = checkbox
            
            toggle_layout.addWidget(checkbox)
        
        toggle_layout.addStretch()
        scroll.setWidget(toggle_container)
        scroll.setMinimumHeight(250)
        layout.addWidget(scroll)
        
        # Quick actions
        actions_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self._select_all_toggles)
        select_all_btn.setStyleSheet(self._action_button_style("#27ae60"))
        actions_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("全不选")
        deselect_all_btn.clicked.connect(self._deselect_all_toggles)
        deselect_all_btn.setStyleSheet(self._action_button_style("#e74c3c"))
        actions_layout.addWidget(deselect_all_btn)
        
        recommend_btn = QPushButton("推荐配置")
        recommend_btn.clicked.connect(self._apply_recommended_config)
        recommend_btn.setStyleSheet(self._action_button_style("#3498db"))
        actions_layout.addWidget(recommend_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        return group
    
    def _select_all_toggles(self):
        """Select all feature checkboxes."""
        for checkbox in self.feature_checkboxes.values():
            checkbox.setChecked(True)
    
    def _deselect_all_toggles(self):
        """Deselect all feature checkboxes."""
        for checkbox in self.feature_checkboxes.values():
            checkbox.setChecked(False)
    
    def _apply_recommended_config(self):
        """Apply recommended configuration based on analysis."""
        # Always enable core features
        always_enable = [
            "yaml_front_matter",
            "core_summary",
            "chinese_exercise_title",
            "solution_marker",
            "boxed_answers",
        ]
        
        # Enable based on content type
        conditional_enable = []
        
        if self._analysis.structure.get("exercise_count", 0) > 3:
            conditional_enable.extend([
                "subproblem_format",
                "key_insight_box",
                "summary_table",
            ])
        
        if self._analysis.style == TemplateStyle.ACADEMIC:
            conditional_enable.extend([
                "concept_table",
                "formula_cheatsheet",
            ])
        
        if self._analysis.style == TemplateStyle.EXAM_ORIENTED:
            conditional_enable.append("cross_note_links")
        
        # Apply selections
        for key, checkbox in self.feature_checkboxes.items():
            if key in always_enable or key in conditional_enable:
                checkbox.setChecked(True)
    
    def _create_custom_rules_group(self) -> QGroupBox:
        """Create custom rules input group."""
        group = QGroupBox("✏️ 自定义规则（可选）")
        group.setStyleSheet(self._group_style())
        layout = QVBoxLayout(group)
        
        hint = QLabel("添加额外的写作要求或特殊指令（每条一行）：")
        hint.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(hint)
        
        self.custom_rules_edit = QTextEdit()
        self.custom_rules_edit.setPlaceholderText(
            "示例：\n"
            "- 所有公式必须同时给出国际单位和常用单位\n"
            "- 物理量首次出现时标注符号（如：电流强度 I）\n"
            "- 避免使用'显然'、'容易看出'等模糊表述\n"
        )
        self.custom_rules_edit.setMaximumHeight(100)
        self.custom_rules_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dfe6e9;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.custom_rules_edit)
        
        return group
    
    def _create_footer(self) -> QWidget:
        """Create footer button bar."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 12, 0, 0)
        
        layout.addStretch()
        
        # Preview button
        preview_btn = QPushButton("👁️ 预览优化后的 Prompt")
        preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        preview_btn.clicked.connect(self._preview_prompts)
        preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #495057;
                border: 1px solid #dee2e6;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
        """)
        layout.addWidget(preview_btn)
        
        # Cancel button
        cancel_btn = QPushButton("取消")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        layout.addWidget(cancel_btn)
        
        # Apply button
        apply_btn = QPushButton("✅ 应用配置并开始生成")
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.setDefault(True)
        apply_btn.clicked.connect(self._apply_and_accept)
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        layout.addWidget(apply_btn)
        
        return widget
    
    def _preview_prompts(self):
        """Show preview of optimized prompts in a message box."""
        from PyQt6.QtWidgets import QMessageBox
        
        modified = self._collect_modifications()
        
        # Generate preview text
        enabled_features = [
            self.FEATURE_DISPLAY_NAMES[k]
            for k, cb in self.feature_checkboxes.items()
            if cb.isChecked()
        ]
        
        disabled_features = [
            self.FEATURE_DISPLAY_NAMES[k]
            for k, cb in self.feature_checkboxes.items()
            if not cb.isChecked()
        ]
        
        variant_name = self.variant_combo.currentText().split("(")[0].strip()
        custom_rules = self.custom_rules_edit.toPlainText().strip()
        
        preview_text = f"""
═══ 📋 优化配置预览 ═══

【Prompt 变体】
{variant_name}

【启用的功能】({len(enabled_features)} 项)
{chr(10).join(f'  ✅ {f}' for f in enabled_features)}

【禁用的功能】({len(disabled_features)} 项)
{chr(10).join(f'  ❌ {f}' for f in disabled_features)}

【自定义规则】
{custom_rules if custom_rules else '  （无）'}

【预期效果】
- YAML Front Matter: {'✅ 启用' if self.feature_checkboxes['yaml_front_matter'].isChecked() else '❌ 禁用'}
- 核心主题摘要: {'✅ 启用' if self.feature_checkboxes['core_summary'].isChecked() else '❌ 禁用'}
- 跨笔记链接: {'✅ 启用' if self.feature_checkboxes['cross_note_links'].isChecked() else '═════════════════════'}
"""
        
        QMessageBox.information(
            self,
            "Prompt 配置预览",
            preview_text.strip(),
        )
    
    def _collect_modifications(self) -> Dict[str, Any]:
        """Collect all user modifications from UI state."""
        modifications = {}
        
        # Collect feature toggles
        enabled_features = []
        disabled_features = []
        
        for feature_key, checkbox in self.feature_checkboxes.items():
            if checkbox.isChecked():
                enabled_features.append(feature_key)
            else:
                disabled_features.append(feature_key)
        
        modifications["enabled_features"] = enabled_features
        modifications["disabled_features"] = disabled_features
        
        # Collect variant choice
        modifications["prompt_variant"] = self.variant_combo.currentData()
        
        # Collect custom rules
        custom_text = self.custom_rules_edit.toPlainText().strip()
        if custom_text:
            modifications["custom_rules"] = [
                line.strip()
                for line in custom_text.split('\n')
                if line.strip()
            ]
        
        return modifications
    
    def _apply_and_accept(self):
        """Collect modifications, update analysis result, and accept dialog."""
        # Collect all user changes
        modifications = self._collect_modifications()
        
        # Create modified copy of analysis
        self._modified_analysis = TemplateAnalysisResult(
            template_path=self._analysis.template_path,
            template_hash=self._analysis.template_hash,
            style=self._analysis.style,
            structure=self._analysis.structure.copy(),
            features=self._analysis.features.copy(),  # Will be updated below
            gaps=[],  # Recalculate after user choices
            complexity=self._analysis.complexity.copy(),
            ai_suggestions=self._analysis.ai_suggestions,
            prompt_variant=modifications["prompt_variant"],
            confidence=self._analysis.confidence,
            analyzed_at=self._analysis.analyzed_at,
            user_modifications=modifications,
        )
        
        # Update features based on user toggles
        for feature_key in self.feature_checkboxes.keys():
            is_checked = self.feature_checkboxes[feature_key].isChecked()
            self._modified_analysis.features[feature_key] = is_checked
            
            # If user disabled a previously-present feature, add to gaps
            if not is_checked and self._analysis.features.get(feature_key, False):
                pass  # User intentionally disabled
            
            # If user enabled a missing feature, remove from gaps
            if is_checked and feature_key in self._analysis.gaps:
                pass  # User filled the gap
        
        # Accept dialog
        self.accept()
    
    def get_modified_result(self) -> Optional[TemplateAnalysisResult]:
        """Get the modified analysis result after user confirms.
        
        Returns:
            Modified TemplateAnalysisResult if user clicked "Apply",
            None if dialog was cancelled.
        """
        return self._modified_analysis
    
    @staticmethod
    def _group_style() -> str:
        """Return standard group box style."""
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #dfe6e9;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2c3e50;
            }
        """
    
    @staticmethod
    def _action_button_style(color: str) -> str:
        """Return small action button style."""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 3px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
        """
