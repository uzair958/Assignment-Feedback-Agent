import type { CriterionScore } from '../types/feedback'

type Props = {
  score: CriterionScore
}

export default function ScoreCard({ score }: Props) {
  return (
    <article className="score-card">
      <h4>
        {score.criterion}: {score.awarded_points}/{score.max_points}
      </h4>
      <p>{score.justification}</p>
      <p>
        <strong>Strengths:</strong> {score.strengths.join('; ')}
      </p>
      <p>
        <strong>Improvements:</strong> {score.improvements.join('; ')}
      </p>
    </article>
  )
}
