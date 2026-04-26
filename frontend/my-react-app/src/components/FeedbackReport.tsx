import ScoreCard from './ScoreCard'
import type { FeedbackReport } from '../types/feedback'

type Props = {
  report: FeedbackReport
}

export default function FeedbackReportView({ report }: Props) {
  return (
    <section className="panel">
      <h2>Feedback Report</h2>
      <p>
        Total: {report.total_score}/{report.total_possible}
      </p>
      <p>{report.overall_summary}</p>
      {report.grade_breakdown.map((score) => (
        <ScoreCard key={`${score.criterion}-${score.max_points}`} score={score} />
      ))}
      <h3>Top Strengths</h3>
      <ul>{report.top_strengths.map((item) => <li key={item}>{item}</li>)}</ul>
      <h3>Priority Improvements</h3>
      <ul>{report.priority_improvements.map((item) => <li key={item}>{item}</li>)}</ul>
      <h3>Suggested Next Steps</h3>
      <ul>{report.suggested_next_steps.map((item) => <li key={item}>{item}</li>)}</ul>
    </section>
  )
}
