"""Evaluation report generator"""

import json
import csv
import sqlite3
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from ..utils.logger import setup_logger
from .scoring import ScoringSystem
from .satisfaction import SatisfactionMetrics
from .fairness import FairnessAnalyzer

logger = setup_logger(__name__)


class EvaluationReporter:
    """Generates evaluation reports and outputs"""
    
    def __init__(self, db_connection: sqlite3.Connection, output_dir: str = "data/evaluation"):
        """Initialize evaluation reporter.
        
        Args:
            db_connection: SQLite database connection
            output_dir: Directory to write output files (default: "data/evaluation")
        """
        self.conn = db_connection
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.scoring = ScoringSystem(db_connection)
        self.satisfaction = SatisfactionMetrics(db_connection)
        self.fairness = FairnessAnalyzer(db_connection)
    
    def generate_json_output(self, metrics: Dict[str, any]) -> str:
        """Generate JSON output file.
        
        Args:
            metrics: Complete metrics dictionary
            
        Returns:
            Path to generated JSON file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"evaluation_metrics_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Generated JSON output: {output_file}")
        return str(output_file)
    
    def generate_csv_output(self, metrics: Dict[str, any]) -> str:
        """Generate CSV output files.
        
        Args:
            metrics: Complete metrics dictionary
            
        Returns:
            Path to generated CSV directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_dir = self.output_dir / f"csv_{timestamp}"
        csv_dir.mkdir(exist_ok=True)
        
        # Coverage metrics
        coverage_file = csv_dir / "coverage_metrics.csv"
        with open(coverage_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value', 'Target', 'Meets Target'])
            coverage = metrics['scoring']['coverage']
            writer.writerow(['Coverage Rate', coverage['coverage_rate'], coverage['target'], coverage['meets_target']])
            writer.writerow(['Total Users', coverage['total_users'], '', ''])
            writer.writerow(['Users with Persona', coverage['users_with_persona'], '', ''])
            writer.writerow(['Users with 3+ Behaviors', coverage['users_with_3_behaviors'], '', ''])
        
        # Satisfaction metrics
        satisfaction_file = csv_dir / "satisfaction_metrics.csv"
        with open(satisfaction_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            engagement = metrics['satisfaction']['engagement']
            helpfulness = metrics['satisfaction']['helpfulness']
            action = metrics['satisfaction']['action']
            writer.writerow(['Engagement Rate', engagement['engagement_rate']])
            writer.writerow(['Helpfulness Score', helpfulness['helpfulness_score']])
            writer.writerow(['Action Rate', action['action_rate']])
            writer.writerow(['Total Feedback', engagement['recommendations_with_feedback']])
        
        # Fairness metrics
        fairness_file = csv_dir / "fairness_metrics.csv"
        with open(fairness_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Quartile', 'Total Users', 'Avg Recommendations', 'Persona Coverage'])
            rec_counts = metrics['fairness']['recommendation_count_by_income']
            persona_dist = metrics['fairness']['persona_distribution_by_income']
            for q in ['q1', 'q2', 'q3', 'q4']:
                rec_data = rec_counts.get(q, {})
                persona_data = persona_dist.get(q, {})
                writer.writerow([
                    q,
                    rec_data.get('total_users', 0),
                    rec_data.get('avg_recommendations', 0),
                    persona_data.get('total_users', 0)
                ])
        
        logger.info(f"Generated CSV outputs in: {csv_dir}")
        return str(csv_dir)
    
    def generate_summary_report(self, metrics: Dict[str, any]) -> str:
        """Generate 1-2 page summary report.
        
        Args:
            metrics: Complete metrics dictionary
            
        Returns:
            Path to generated summary report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"evaluation_summary_{timestamp}.md"
        
        scoring = metrics['scoring']
        satisfaction = metrics['satisfaction']
        fairness = metrics['fairness']
        
        with open(output_file, 'w') as f:
            f.write("# SpendSense Evaluation Summary\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Automatic Scoring Metrics\n\n")
            
            # Coverage
            coverage = scoring['coverage']
            f.write(f"### Coverage: {coverage['coverage_rate']}% (Target: {coverage['target']}%)\n")
            f.write(f"- Total Users: {coverage['total_users']}\n")
            f.write(f"- Users with Persona: {coverage['users_with_persona']}\n")
            f.write(f"- Users with 3+ Behaviors: {coverage['users_with_3_behaviors']}\n")
            f.write(f"- Users with Both: {coverage['users_with_persona_and_behaviors']}\n")
            f.write(f"- **Status:** {'✅ Meets Target' if coverage['meets_target'] else '❌ Below Target'}\n\n")
            
            # Explainability
            explainability = scoring['explainability']
            f.write(f"### Explainability: {explainability['explainability_rate']}% (Target: {explainability['target']}%)\n")
            f.write(f"- Total Recommendations: {explainability['total_recommendations']}\n")
            f.write(f"- With Rationales: {explainability['recommendations_with_rationales']}\n")
            f.write(f"- **Status:** {'✅ Meets Target' if explainability['meets_target'] else '❌ Below Target'}\n\n")
            
            # Latency
            latency = scoring['latency']
            f.write(f"### Latency: {latency['avg_latency_seconds']}s (Target: <{latency['target']}s)\n")
            f.write(f"- Sample Size: {latency['sample_size']}\n")
            f.write(f"- Min: {latency['min_latency_seconds']}s, Max: {latency['max_latency_seconds']}s\n")
            f.write(f"- **Status:** {'✅ Meets Target' if latency['meets_target'] else '❌ Above Target'}\n\n")
            
            # Auditability
            auditability = scoring['auditability']
            f.write(f"### Auditability: {auditability['auditability_rate']}% (Target: {auditability['target']}%)\n")
            f.write(f"- Users with Traces: {auditability['users_with_traces']}\n")
            f.write(f"- **Status:** {'✅ Meets Target' if auditability['meets_target'] else '❌ Below Target'}\n\n")
            
            f.write("## User Satisfaction Metrics\n\n")
            
            # Engagement
            engagement = satisfaction['engagement']
            f.write(f"### Engagement Rate: {engagement['engagement_rate']}%\n")
            f.write(f"- Recommendations with Feedback: {engagement['recommendations_with_feedback']}\n")
            f.write(f"- User Engagement: {engagement['user_engagement_rate']}%\n\n")
            
            # Helpfulness
            helpfulness = satisfaction['helpfulness']
            f.write(f"### Helpfulness Score: {helpfulness['helpfulness_score']}%\n")
            f.write(f"- Thumbs Up: {helpfulness['thumbs_up']}\n")
            f.write(f"- Thumbs Down: {helpfulness['thumbs_down']}\n\n")
            
            # Action
            action = satisfaction['action']
            f.write(f"### Action Rate: {action['action_rate']}%\n")
            f.write(f"- Applied This: {action['applied_this_count']}\n")
            f.write(f"- Helped Me: {action['helped_me_count']}\n\n")
            
            f.write("## Fairness Analysis\n\n")
            
            # Bias detection
            bias = fairness['bias_detection']
            f.write(f"### Bias Detection\n")
            f.write(f"- Q1 to Q4 Recommendation Ratio: {bias['recommendation_ratio_q1_to_q4']}\n")
            f.write(f"- Q1 Coverage: {bias['q1_coverage_rate']}%\n")
            f.write(f"- Q4 Coverage: {bias['q4_coverage_rate']}%\n")
            f.write(f"- **Bias Detected:** {'⚠️ Yes' if bias['overall_bias_detected'] else '✅ No'}\n\n")
            
            # Persona distribution
            f.write("### Persona Distribution by Income Quartile\n\n")
            persona_dist = fairness['persona_distribution_by_income']
            for q in ['q1', 'q2', 'q3', 'q4']:
                data = persona_dist.get(q, {})
                f.write(f"**{q.upper()}:** {data.get('total_users', 0)} users\n")
                for persona, count in data.get('persona_distribution', {}).items():
                    f.write(f"  - {persona}: {count}\n")
                f.write("\n")
            
            f.write("## Recommendations\n\n")
            
            # Generate recommendations based on metrics
            recommendations = []
            
            if not coverage['meets_target']:
                recommendations.append("Improve coverage by ensuring all users with sufficient data get persona assignments")
            
            if not explainability['meets_target']:
                recommendations.append("Ensure all recommendations have rationales")
            
            if not latency['meets_target']:
                recommendations.append("Optimize recommendation generation performance")
            
            if not auditability['meets_target']:
                recommendations.append("Ensure all persona assignments include decision traces")
            
            if bias['overall_bias_detected']:
                recommendations.append("Review fairness: Q1 users may be systematically underserved")
            
            if helpfulness['helpfulness_score'] < 70:
                recommendations.append("Improve recommendation quality based on user feedback")
            
            if not recommendations:
                recommendations.append("✅ All metrics meet targets. Continue monitoring.")
            
            for i, rec in enumerate(recommendations, 1):
                f.write(f"{i}. {rec}\n")
        
        logger.info(f"Generated summary report: {output_file}")
        return str(output_file)
    
    def generate_fairness_report(self, fairness_metrics: Dict[str, any]) -> str:
        """Generate detailed fairness analysis report.
        
        Args:
            fairness_metrics: Fairness metrics dictionary
            
        Returns:
            Path to generated fairness report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"fairness_analysis_{timestamp}.md"
        
        with open(output_file, 'w') as f:
            f.write("# SpendSense Fairness Analysis Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Executive Summary\n\n")
            bias = fairness_metrics['bias_detection']
            if bias['overall_bias_detected']:
                f.write("⚠️ **Bias detected in the system.**\n\n")
                f.write("Low-income users (Q1) may be receiving fewer recommendations or lower coverage.\n\n")
            else:
                f.write("✅ **No significant bias detected.**\n\n")
                f.write("The system appears to provide equitable treatment across income levels.\n\n")
            
            f.write("## Income Quartile Analysis\n\n")
            
            # Recommendation counts
            f.write("### Recommendation Distribution\n\n")
            rec_counts = fairness_metrics['recommendation_count_by_income']
            for q in ['q1', 'q2', 'q3', 'q4']:
                data = rec_counts.get(q, {})
                f.write(f"**{q.upper()}:**\n")
                f.write(f"- Total Users: {data.get('total_users', 0)}\n")
                f.write(f"- Avg Recommendations: {data.get('avg_recommendations', 0)}\n")
                f.write(f"- Total Recommendations: {data.get('total_recommendations', 0)}\n\n")
            
            # Persona distribution
            f.write("### Persona Distribution\n\n")
            persona_dist = fairness_metrics['persona_distribution_by_income']
            for q in ['q1', 'q2', 'q3', 'q4']:
                data = persona_dist.get(q, {})
                f.write(f"**{q.upper()}:** {data.get('total_users', 0)} users\n")
                for persona, count in sorted(data.get('persona_distribution', {}).items(), key=lambda x: -x[1]):
                    f.write(f"  - {persona}: {count}\n")
                f.write("\n")
            
            # Offer eligibility
            f.write("### Offer Eligibility by Account Complexity\n\n")
            eligibility = fairness_metrics['offer_eligibility_by_complexity']
            for category, data in eligibility.items():
                f.write(f"**{category.replace('_', ' ').title()}:**\n")
                f.write(f"- Total Users: {data.get('total_users', 0)}\n")
                f.write(f"- Users with Offers: {data.get('users_with_offers', 0)}\n")
                f.write(f"- Eligibility Rate: {data.get('eligibility_rate', 0)}%\n\n")
            
            # Tone sentiment
            f.write("### Tone Sentiment by Persona\n\n")
            tone = fairness_metrics['tone_sentiment_by_persona']
            for persona, data in tone.items():
                f.write(f"**{persona}:**\n")
                f.write(f"- Total Recommendations: {data.get('total_recommendations', 0)}\n")
                f.write(f"- Positive Keyword Rate: {data.get('positive_keyword_rate', 0)}%\n")
                f.write(f"- Explanatory Keyword Rate: {data.get('explanatory_keyword_rate', 0)}%\n\n")
            
            f.write("## Bias Detection Results\n\n")
            f.write(f"- Recommendation Ratio (Q1/Q4): {bias['recommendation_ratio_q1_to_q4']}\n")
            f.write(f"- Bias in Recommendations: {'⚠️ Detected' if bias['bias_detected_recommendations'] else '✅ None'}\n")
            f.write(f"- Coverage Q1: {bias['q1_coverage_rate']}%\n")
            f.write(f"- Coverage Q4: {bias['q4_coverage_rate']}%\n")
            f.write(f"- Bias in Coverage: {'⚠️ Detected' if bias['bias_detected_coverage'] else '✅ None'}\n")
            f.write(f"- **Overall Bias:** {'⚠️ Detected' if bias['overall_bias_detected'] else '✅ None'}\n\n")
            
            f.write("## Recommendations\n\n")
            if bias['overall_bias_detected']:
                f.write("1. Review persona assignment criteria for Q1 users\n")
                f.write("2. Ensure recommendation generation is equitable across income levels\n")
                f.write("3. Monitor offer eligibility rates for basic account users\n")
                f.write("4. Consider targeted outreach to low-income users\n")
            else:
                f.write("✅ System appears fair. Continue monitoring for bias.\n")
        
        logger.info(f"Generated fairness report: {output_file}")
        return str(output_file)
    
    def export_decision_traces(self) -> str:
        """Export per-user decision traces.
        
        Returns:
            Path to generated decision traces file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"decision_traces_{timestamp}.json"
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                user_id,
                persona_name,
                priority_level,
                signal_strength,
                decision_trace
            FROM personas
            WHERE decision_trace IS NOT NULL AND decision_trace != ''
            ORDER BY user_id
        """)
        
        traces = []
        for row in cursor.fetchall():
            try:
                trace_data = json.loads(row['decision_trace']) if isinstance(row['decision_trace'], str) else row['decision_trace']
            except:
                trace_data = {'raw': row['decision_trace']}
            
            traces.append({
                'user_id': row['user_id'],
                'persona_name': row['persona_name'],
                'priority_level': row['priority_level'],
                'signal_strength': row['signal_strength'],
                'decision_trace': trace_data
            })
        
        with open(output_file, 'w') as f:
            json.dump(traces, f, indent=2)
        
        logger.info(f"Exported {len(traces)} decision traces: {output_file}")
        return str(output_file)
    
    def run_full_evaluation(self, latency_sample_size: int = 10) -> Dict[str, any]:
        """Run complete evaluation and generate all outputs.
        
        Args:
            latency_sample_size: Number of users to test for latency (default: 10)
            
        Returns:
            Dictionary with all metrics and output file paths
        """
        logger.info("Running full evaluation...")
        
        # Compute all metrics
        scoring_metrics = self.scoring.compute_all_scores(latency_sample_size)
        satisfaction_metrics = self.satisfaction.compute_all_satisfaction_metrics()
        fairness_metrics = self.fairness.compute_all_fairness_metrics()
        
        # Combine metrics
        all_metrics = {
            'scoring': scoring_metrics,
            'satisfaction': satisfaction_metrics,
            'fairness': fairness_metrics,
            'evaluation_date': datetime.now().isoformat()
        }
        
        # Generate outputs
        json_file = self.generate_json_output(all_metrics)
        csv_dir = self.generate_csv_output(all_metrics)
        summary_file = self.generate_summary_report(all_metrics)
        fairness_file = self.generate_fairness_report(fairness_metrics)
        traces_file = self.export_decision_traces()
        
        all_metrics['output_files'] = {
            'json': json_file,
            'csv_directory': csv_dir,
            'summary_report': summary_file,
            'fairness_report': fairness_file,
            'decision_traces': traces_file
        }
        
        logger.info("Full evaluation complete!")
        
        return all_metrics

