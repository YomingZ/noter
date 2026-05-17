"""Past exam question correlation and analysis module."""

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Set

logger = logging.getLogger(__name__)


@dataclass
class ExamQuestion:
    """Represents a single exam question."""
    id: str
    source: str  # Exam source (year, term, etc.)
    question_type: str  # choice, fill, short_answer, calculation, essay
    content: str
    answer: Optional[str] = None
    knowledge_points: List[str] = field(default_factory=list)
    difficulty: str = "medium"  # easy, medium, hard


@dataclass
class KnowledgePoint:
    """Represents a knowledge point from course materials."""
    id: str
    name: str
    description: str
    related_questions: List[str] = field(default_factory=list)
    frequency: int = 0  # How often it appears in exams


class ExamQuestionAnalyzer:
    """
    Analyze and correlate exam questions with course materials.

    Features:
    - Extract questions from exam PDFs
    - Identify knowledge points
    - Build question-knowledge correlation
    - Predict exam focus areas
    """

    # Question type patterns
    QUESTION_PATTERNS = {
        'choice': [
            r'([一二三四五六七八九十]+[、.．]\s*[单项选择题|选择题].*?)(?=[一二三四五六七八九十]+[、.．]|$)',
            r'([一二三四五六七八九十]+[、.．]\s*选择题.*?)(?=[一二三四五六七八九十]+[、.．]|$)',
        ],
        'fill': [
            r'([一二三四五六七八九十]+[、.．]\s*[填空题|填空].*?)(?=[一二三四五六七八九十]+[、.．]|$)',
        ],
        'short_answer': [
            r'([一二三四五六七八九十]+[、.．]\s*[简答题|简答].*?)(?=[一二三四五六七八九十]+[、.．]|$)',
            r'([一二三四五六七八九十]+[、.．]\s*名词解释.*?)(?=[一二三四五六七八九十]+[、.．]|$)',
        ],
        'calculation': [
            r'([一二三四五六七八九十]+[、.．]\s*[计算题|计算].*?)(?=[一二三四五六七八九十]+[、.．]|$)',
        ],
        'essay': [
            r'([一二三四五六七八九十]+[、.．]\s*[论述题|论述].*?)(?=[一二三四五六七八九十]+[、.．]|$)',
        ],
    }

    # Common knowledge point indicators
    KP_INDICATORS = [
        '概念', '定义', '原理', '定理', '公式', '方法',
        '特点', '性质', '分类', '应用', '区别', '关系',
    ]

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path("./output/.exam_data")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.questions: Dict[str, ExamQuestion] = {}
        self.knowledge_points: Dict[str, KnowledgePoint] = {}
        self.correlations: Dict[str, Set[str]] = {}  # kp_id -> question_ids

        self._load_data()

    def _load_data(self):
        """Load saved data from disk."""
        questions_file = self.data_dir / "questions.json"
        kp_file = self.data_dir / "knowledge_points.json"

        if questions_file.exists():
            try:
                with open(questions_file, encoding='utf-8') as f:
                    data = json.load(f)
                    for q_id, q_data in data.items():
                        self.questions[q_id] = ExamQuestion(**q_data)
            except Exception as e:
                logger.warning(f"Failed to load questions: {e}")

        if kp_file.exists():
            try:
                with open(kp_file, encoding='utf-8') as f:
                    data = json.load(f)
                    for kp_id, kp_data in data.items():
                        self.knowledge_points[kp_id] = KnowledgePoint(**kp_data)
            except Exception as e:
                logger.warning(f"Failed to load knowledge points: {e}")

    def _save_data(self):
        """Save data to disk."""
        questions_file = self.data_dir / "questions.json"
        kp_file = self.data_dir / "knowledge_points.json"

        with open(questions_file, 'w', encoding='utf-8') as f:
            json.dump(
                {q_id: q.__dict__ for q_id, q in self.questions.items()},
                f, ensure_ascii=False, indent=2
            )

        with open(kp_file, 'w', encoding='utf-8') as f:
            json.dump(
                {kp_id: kp.__dict__ for kp_id, kp in self.knowledge_points.items()},
                f, ensure_ascii=False, indent=2
            )

    def extract_questions_from_text(
        self,
        text: str,
        source: str = "unknown",
    ) -> List[ExamQuestion]:
        """
        Extract questions from exam text content.

        Args:
            text: Text content from exam PDF
            source: Source identifier (e.g., "2023期末")

        Returns:
            List of extracted questions
        """
        questions = []

        for q_type, patterns in self.QUESTION_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.DOTALL)

                for match in matches:
                    section = match.group(1)

                    # Split into individual questions
                    individual_questions = self._split_questions(section, q_type)

                    for i, q_content in enumerate(individual_questions):
                        if len(q_content.strip()) < 10:
                            continue

                        q_id = self._generate_id(f"{source}_{q_type}_{i}")

                        question = ExamQuestion(
                            id=q_id,
                            source=source,
                            question_type=q_type,
                            content=q_content.strip(),
                        )

                        questions.append(question)
                        self.questions[q_id] = question

        self._save_data()
        logger.info(f"Extracted {len(questions)} questions from {source}")

        return questions

    def _split_questions(self, section: str, q_type: str) -> List[str]:
        """Split a section into individual questions."""
        # Pattern for numbered questions
        if q_type in ['choice', 'fill']:
            pattern = r'\d+[\.、．]\s*(.*?)(?=\d+[\.、．]|$)'
        else:
            pattern = r'\d+[\.、．]\s*(.*?)(?=\d+[\.、．]|$)'

        matches = re.findall(pattern, section, re.DOTALL)
        return [m.strip() for m in matches if m.strip()]

    def _generate_id(self, text: str) -> str:
        """Generate unique ID from text."""
        return hashlib.md5(text.encode()).hexdigest()[:12]

    def analyze_knowledge_points(
        self,
        course_content: str,
        min_frequency: int = 1,
    ) -> List[KnowledgePoint]:
        """
        Analyze course content to identify knowledge points.

        Args:
            course_content: Text content from course materials
            min_frequency: Minimum frequency to include

        Returns:
            List of identified knowledge points
        """
        # Extract potential knowledge points
        potential_kps = {}

        # Look for defined terms
        definition_patterns = [
            r'【([^】]+)】[：:]\s*([^。\n]+)',
            r'([^\n]{2,10})[：:是指即]+\s*([^。\n]{10,100})',
            r'所谓[「"『]([^」"』]+)[」"』]，?[是指]+\s*([^。\n]+)',
        ]

        for pattern in definition_patterns:
            matches = re.finditer(pattern, course_content)
            for match in matches:
                name = match.group(1).strip()
                description = match.group(2).strip()

                if len(name) < 2 or len(name) > 20:
                    continue

                kp_id = self._generate_id(name)

                if kp_id not in potential_kps:
                    potential_kps[kp_id] = KnowledgePoint(
                        id=kp_id,
                        name=name,
                        description=description,
                    )
                potential_kps[kp_id].frequency += 1

        # Filter by frequency
        filtered = [
            kp for kp in potential_kps.values()
            if kp.frequency >= min_frequency
        ]

        # Update stored knowledge points
        for kp in filtered:
            self.knowledge_points[kp.id] = kp

        self._save_data()

        return filtered

    def correlate_questions_with_kp(
        self,
        questions: Optional[List[ExamQuestion]] = None,
    ) -> Dict[str, Set[str]]:
        """
        Build correlation between questions and knowledge points.

        Args:
            questions: Questions to correlate (uses all if None)

        Returns:
            Dict mapping knowledge point IDs to related question IDs
        """
        questions = questions or list(self.questions.values())

        correlations: Dict[str, Set[str]] = {
            kp_id: set() for kp_id in self.knowledge_points
        }

        for question in questions:
            content_lower = question.content.lower()

            for kp_id, kp in self.knowledge_points.items():
                # Check if KP name appears in question
                if kp.name.lower() in content_lower:
                    correlations[kp_id].add(question.id)
                    question.knowledge_points.append(kp.name)

        self.correlations = correlations
        self._save_data()

        return correlations

    def get_exam_prediction(
        self,
        top_n: int = 10,
    ) -> List[Dict]:
        """
        Predict likely exam focus areas based on historical data.

        Args:
            top_n: Number of predictions to return

        Returns:
            List of predicted focus areas with scores
        """
        predictions = []

        for kp_id, kp in self.knowledge_points.items():
            # Calculate prediction score
            # Factors: frequency in materials, frequency in past exams, question types

            related_questions = self.correlations.get(kp_id, set())
            question_count = len(related_questions)

            if question_count == 0:
                continue

            # Analyze question types
            types = {}
            for q_id in related_questions:
                q = self.questions.get(q_id)
                if q:
                    types[q.question_type] = types.get(q.question_type, 0) + 1

            # Score based on type variety and frequency
            score = (
                kp.frequency * 0.3 +  # Material frequency
                question_count * 0.5 +  # Past exam frequency
                len(types) * 0.2  # Question type variety
            )

            predictions.append({
                'knowledge_point': kp.name,
                'description': kp.description[:100] if kp.description else '',
                'score': round(score, 2),
                'frequency': kp.frequency,
                'exam_count': question_count,
                'question_types': list(types.keys()),
                'last_appeared': self._get_last_appearance(related_questions),
            })

        # Sort by score
        predictions.sort(key=lambda x: x['score'], reverse=True)

        return predictions[:top_n]

    def _get_last_appearance(self, question_ids: Set[str]) -> str:
        """Get the most recent source from related questions."""
        sources = set()
        for q_id in question_ids:
            q = self.questions.get(q_id)
            if q:
                sources.add(q.source)

        if sources:
            return max(sources)  # Assuming sources are sortable (e.g., "2023期末")

        return "未知"

    def generate_study_guide(
        self,
        course_name: str = "",
    ) -> str:
        """
        Generate a study guide based on exam analysis.

        Returns:
            Markdown formatted study guide
        """
        predictions = self.get_exam_prediction(top_n=20)

        lines = [
            f"# 📚 {course_name} 考前重点预测",
            "",
            f"> 基于往届考题分析，生成时间: {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "---",
            "",
            "## 🔥 高频考点 (按重要性排序)",
            "",
        ]

        for i, pred in enumerate(predictions[:10], 1):
            emoji = "🔥" if pred['score'] > 5 else "⭐" if pred['score'] > 3 else "📌"

            lines.append(f"### {emoji} {i}. {pred['knowledge_point']}")
            lines.append("")
            lines.append(f"- **预测分数**: {pred['score']}")
            lines.append(f"- **材料频率**: 出现 {pred['frequency']} 次")
            lines.append(f"- **往年考题**: {pred['exam_count']} 次")

            if pred['question_types']:
                type_names = {
                    'choice': '选择题',
                    'fill': '填空题',
                    'short_answer': '简答题',
                    'calculation': '计算题',
                    'essay': '论述题',
                }
                types_str = ', '.join(
                    type_names.get(t, t) for t in pred['question_types']
                )
                lines.append(f"- **常考题型**: {types_str}")

            if pred['description']:
                lines.append(f"- **要点**: {pred['description']}...")

            lines.append("")

        # Add question type statistics
        lines.append("---")
        lines.append("")
        lines.append("## 📊 题型分布统计")
        lines.append("")

        type_counts = {}
        for q in self.questions.values():
            type_counts[q.question_type] = type_counts.get(q.question_type, 0) + 1

        for q_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            type_name = {
                'choice': '选择题',
                'fill': '填空题',
                'short_answer': '简答题',
                'calculation': '计算题',
                'essay': '论述题',
            }.get(q_type, q_type)
            lines.append(f"- {type_name}: {count} 题")

        return "\n".join(lines)


def analyze_exam_pdfs(
    exam_dir: Path,
    course_content: str = "",
) -> Dict:
    """
    Convenience function to analyze exam PDFs.

    Args:
        exam_dir: Directory containing exam PDF files
        course_content: Optional course content for better analysis

    Returns:
        Analysis results
    """
    from pdf_summarizer.pdf_reader import PDFExtractor

    analyzer = ExamQuestionAnalyzer()
    extractor = PDFExtractor()

    # Extract questions from all exam PDFs
    all_questions = []
    for pdf_file in sorted(exam_dir.glob("*.pdf")):
        try:
            doc = extractor.read(pdf_file)
            text = doc.get_full_text()

            questions = analyzer.extract_questions_from_text(
                text,
                source=pdf_file.stem,
            )
            all_questions.extend(questions)

        except Exception as e:
            logger.error(f"Failed to process {pdf_file}: {e}")

    # Analyze knowledge points if course content provided
    if course_content:
        analyzer.analyze_knowledge_points(course_content)
        analyzer.correlate_questions_with_kp(all_questions)

    return {
        'total_questions': len(all_questions),
        'predictions': analyzer.get_exam_prediction(),
        'analyzer': analyzer,
    }
